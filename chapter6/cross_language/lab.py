"""语种分库与跨语种查询练习。运行 python lab.py 查看离线结果。"""

import json
import math
import re
from collections import Counter
from collections.abc import Callable

Ask = Callable[[str, str], str]
Vector = dict[str, float]
IndexEntry = tuple[dict[str, str], Vector]

# 每条记录是一段可独立检索的原文。lab:// 地址指向练习中的材料。
FRAGMENTS = (
    {
        "id": "release-rollback",
        "title": "Blue-green rollout: rollback after traffic cutover",
        "text": "If the green deployment fails its health checks after traffic cutover, "
                "route traffic back to blue only if no irreversible database migration "
                "has run. After an irreversible migration, pause the rollout and roll forward.",
        "version": "3.2",
        "source": "lab://release/blue-green#rollback",
    },
    {
        "id": "release-health-zh",
        "title": "蓝绿发布切流前的健康检查",
        "text": "如果新版本健康检查失败，停止切流并保留旧版本。此处记录切流前检查，"
                "切流后的回滚需要按发布手册检查数据库迁移状态。",
        "version": "2.1",
        "source": "lab://release/health-check#pre-cutover",
    },
    {
        "id": "webhook-replay",
        "title": "Webhook 通知重放与去重",
        "text": "Webhook 通知重试耗尽后，从死信队列取出失败事件并重放。重放时沿用原事件 ID "
                "作为幂等键，避免向同一个收件人重复发送通知。",
        "version": "4.0",
        "source": "lab://integrations/webhook#dead-letter-replay",
    },
    {
        "id": "webhook-dashboard-zh",
        "title": "Webhook 投递重试监控",
        "text": "值班时在 Webhook Delivery Retries 面板核对重试次数和目标地址。"
                "面板用来查看失败趋势，不处理死信队列中的通知。",
        "version": "2.3",
        "source": "lab://integrations/dashboard#retries",
    },
    {
        "id": "webhook-retry-en",
        "title": "Webhook delivery retries",
        "text": "Retry notification delivery with exponential backoff. After retries are exhausted, "
                "move the failed notification to the dead-letter queue. The retry scheduler records delivery attempts.",
        "version": "3.1",
        "source": "lab://integrations/webhook-retries#scheduler",
    },
    {
        "id": "webhook-audit-en",
        "title": "Audit webhook delivery",
        "text": "To diagnose a missing webhook notification, open delivery history. A delivery trace "
                "records HTTP responses, retries and the notification payload.",
        "version": "2.2",
        "source": "lab://integrations/webhook-audit#history",
    },
    {
        "id": "release-training-zh",
        "title": "蓝绿发布演练中的回滚",
        "text": "演练环境先切流，再模拟新版本健康检查失败，随后回滚到旧版本。演练使用可重置的测试数据库。",
        "version": "1.3",
        "source": "lab://release/drill#rollback",
    },
    {
        "id": "backup-restore",
        "title": "Restore a backup into a separate database",
        "text": "Restore the backup into a new database instance. Validate the restored copy "
                "before switching connections. Leave the live production instance serving traffic.",
        "version": "5.0",
        "source": "lab://data/backups#restore-isolated",
    },
    {
        "id": "database-failover-zh",
        "title": "数据库故障切换与连接回收",
        "text": "主实例故障后，确认备用实例接收写入，再清理旧连接。恢复服务前核对监控记录。",
        "version": "3.0",
        "source": "lab://data/failover#connections",
    },
)

QUERIES = (
    {
        "id": "after-cutover",
        "question": "生产蓝绿发布已经切流，新版本健康检查失败时，什么情况下允许回滚到旧版本？",
        "expected": "release-rollback",
        "replay": "After production blue-green rollout traffic cutover, if the new deployment fails "
                  "health checks, under what condition can we roll back to the old version?",
    },
    {
        "id": "webhook-redelivery",
        "question": "After webhook delivery retries are exhausted, how do I replay the notification without sending duplicates?",
        "expected": "webhook-replay",
        "replay": "Webhook 通知重试耗尽后，如何重放通知并避免重复发送？",
    },
    {
        "id": "switch-over",
        "question": "数据库主实例故障，要切换到备用实例并清理旧连接，该看哪个操作指引？",
        "expected": "database-failover-zh",
        "replay": "Which procedure describes switching to a standby database instance after a failure and clearing old connections?",
    },
    {
        "id": "restore",
        "question": "How do I restore a database backup while keeping the live production instance serving traffic?",
        "expected": "backup-restore",
        "replay": "如何恢复数据库备份，同时让生产实例继续提供服务？",
    },
)

LANGUAGE_NAMES = {"zh": "简体中文", "en": "英语"}
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
WORD = re.compile(r"[a-z]+(?:\d+)?|\d+")


def language_of(text: str) -> str:
    """按主要书写系统判断这组中英样本，允许中文正文包含英文术语。"""
    han_count = len(HAN.findall(text))
    latin_count = sum(character.isascii() and character.isalpha() for character in text)
    if not han_count and not latin_count:
        raise ValueError("材料缺少可识别的中英文内容。")
    return "zh" if han_count and han_count >= latin_count / 3 else "en"


def project(text: str, language: str) -> Vector:
    """离线稀疏向量替身。中文取字和相邻字，英文取词。"""
    text = text.casefold()
    features = Counter(WORD.findall(text))
    if language == "zh":
        for sequence in re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", text):
            features.update(sequence)
            features.update(sequence[index:index + 2] for index in range(len(sequence) - 1))
    length = math.sqrt(sum(count ** 2 for count in features.values()))
    return {token: count / length for token, count in features.items()}


def score(query: Vector, passage: Vector) -> float:
    return sum(weight * passage.get(term, 0.0) for term, weight in query.items())


def build_index() -> dict[str, list[IndexEntry]]:
    partitions = {language: [] for language in LANGUAGE_NAMES}
    for fragment in FRAGMENTS:
        searchable_text = f'{fragment["title"]}\n{fragment["text"]}'
        language = language_of(searchable_text)
        document = {**fragment, "language": language}
        partitions[language].append((document, project(searchable_text, language)))
    return partitions


def search(query: Vector, entries: list[IndexEntry], limit: int) -> list[dict]:
    matches = [(score(query, vector), document) for document, vector in entries]
    matches = sorted(matches, key=lambda match: (-match[0], match[1]["id"]))
    return [{**document, "score": round(value, 4)} for value, document in matches[:limit] if value > 0]


def adapt_question(case: dict[str, str], query_language: str, target: str, ask: Ask | None) -> str:
    if target == query_language:
        return case["question"]
    if ask is None:
        return case["replay"]

    translated = ask(
        f"把用户给出的检索问题译为{LANGUAGE_NAMES[target]}。保留产品名、技术术语、"
        "操作顺序、条件与否定词。仅输出译文，不回答问题，不补充未给出的事实。",
        case["question"],
    ).strip()
    if not translated or language_of(translated) != target:
        raise ValueError(f"{case['id']} 的译文没有使用目标语言 {LANGUAGE_NAMES[target]}。")
    return translated


def run(ask: Ask | None = None) -> dict:
    partitions = build_index()
    mixed = partitions["zh"] + partitions["en"]
    results = []
    for case in QUERIES:
        original = case["question"]
        query_language = language_of(original)
        baseline = search(project(original, query_language), mixed, limit=2)
        raw_by_language = {}
        queries = {}
        by_language = {}
        for target, entries in partitions.items():
            raw_by_language[target] = search(project(original, target), entries, limit=1)
            queries[target] = adapt_question(case, query_language, target, ask)
            by_language[target] = search(project(queries[target], target), entries, limit=1)
        raw_split = raw_by_language["zh"] + raw_by_language["en"]
        adapted = by_language["zh"] + by_language["en"]
        results.append({
            "case_id": case["id"],
            "question": original,
            "query_language": query_language,
            "expected_source_fragment": case["expected"],
            "baseline_hits": baseline,
            "baseline_found": any(hit["id"] == case["expected"] for hit in baseline),
            "raw_split_hits_by_language": raw_by_language,
            "raw_split_found": any(hit["id"] == case["expected"] for hit in raw_split),
            "adapted_queries": queries,
            "adapted_hits_by_language": by_language,
            "adapted_found": any(hit["id"] == case["expected"] for hit in adapted),
        })
    return {
        "mode": "live_translation" if ask is not None else "offline_replay",
        "index_sizes": {lang: len(entries) for lang, entries in partitions.items()},
        "candidate_budget": 2,
        "baseline_recall_at_2": sum(row["baseline_found"] for row in results) / len(results),
        "raw_split_recall_at_2": sum(row["raw_split_found"] for row in results) / len(results),
        "adapted_recall_at_2": sum(row["adapted_found"] for row in results) / len(results),
        "cases": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
