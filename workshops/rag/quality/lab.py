"""文档片段质量打标练习的可复现参考实现。"""

import json
from collections import Counter, defaultdict


CHUNKS = {
    "spec@3:1": "项目检索只返回当前归属项目的资料。文档迁出后，旧项目应停止使用旧依据。",
    "spec@3:2": "正文版本不变时，归属变更仍应触发变更事件。",
    "archive@1:4": "只在正文版本更新时触发通知。所有项目继续保留迁出资料。",
    "notify@2:1": "同一变更事件重复投递时只通知一次。",
    "sdk@3:2": "本次变更只改应用层，共享 Wiki SDK 接口和全局检索行为保持兼容。",
    "releases@1:3": "正式环境由当班负责人批准回滚。",
    "notes@1:2": "迁出之后的缓存行为需要另行确认。",
}

# label 是这份回放材料里已完成的独立复核，不来自反馈按钮。
# 每行包含轨迹、用户、查询组、问题、已核验的规则、回答、回答级反馈、片段观察。
REPLAY = [
    ("t01", "u1", "project_move", "文档迁出后旧项目还能用它吗？",
     "旧项目停止采用", "旧项目停止采用该文档", "+",
     [("spec@3:1", "used", "supports"), ("archive@1:4", "recalled", None)]),
    ("t02", "u2", "project_scope", "项目检索应该限制到哪里？",
     "只查当前归属项目", "只查当前归属项目", "+",
     [("spec@3:1", "used", "supports"), ("notify@2:1", "loaded", None)]),
    ("t03", "u3", "project_move", "换项目后旧项目还能引用吗？",
     "旧项目停止采用", "旧项目停止采用", "+", [("spec@3:1", "used", "supports")]),
    ("t04", "u4", "project_scope", "新项目检索能查到迁入的文档吗？",
     "按最新归属确定检索范围", "按最新归属确定检索范围", "+", [("spec@3:1", "used", "supports")]),
    ("t05", "u1", "same_version", "正文版本未变，迁出要不要通知？",
     "正文不变也应触发归属变更通知", "版本未变，无需通知", "-",
     [("archive@1:4", "used", "contradicts"), ("spec@3:2", "loaded", None)]),
    ("t06", "u2", "project_move", "迁出的资料还要保留在旧项目吗？",
     "旧项目停止采用", "所有项目仍保留迁出资料", "-",
     [("archive@1:4", "used", "contradicts"), ("spec@3:1", "recalled", None)]),
    ("t07", "u3", "same_version", "只改项目归属，需要告诉订阅方吗？",
     "正文不变也应触发归属变更通知", "先等正文有新版本", "-",
     [("archive@1:4", "used", "contradicts")]),
    ("t08", "u4", "project_move", "旧项目还能继续检索迁出的内容吗？",
     "旧项目不应返回已迁出文档", "可以继续检索", "-",
     [("archive@1:4", "used", "contradicts")]),
    ("t09", "u5", "same_version", "正文未改的归属变更应该发事件吗？",
     "正文不变也应触发归属变更通知", "归属变化就应发通知。同一事件只通知一次。", "+",
     [("spec@3:2", "used", "supports"), ("notify@2:1", "used", "irrelevant")]),
    ("t10", "u6", "replay_event", "同一事件被重放两次，应该发几条通知？",
     "同一事件只通知一次", "只发送一次", "+",
     [("notify@2:1", "used", "supports"), ("releases@1:3", "loaded", None)]),
    ("t11", "u6", "sdk_compat", "能否为了项目检索修改共享 SDK 接口？",
     "共享接口保持兼容", "这次只改应用层，保留共享接口", "-",
     [("sdk@3:2", "used", "supports")]),
    ("t12", "u7", "cache_ttl", "迁出后的缓存多久会失效？",
     "资料暂未确认缓存失效时间", "需要另行确认", "+",
     [("notes@1:2", "used", None)]),
]

ROUTE_STABLE_AT = 4
AttributionKey = tuple[str, str]


def _observations():
    seen = set()
    for trace, user, group, query, rule, answer, feedback, observations in REPLAY:
        for chunk, stage, label in observations:
            key = trace, chunk
            if key in seen:
                raise ValueError(f"重复片段曝光 {key}")
            seen.add(key)
            yield {
                "trace": trace, "user": user, "query_group": group, "query": query,
                "verified_rule": rule, "answer": answer, "answer_feedback": feedback,
                "chunk": chunk, "stage": stage, "label": label if stage == "used" else None,
            }


def _partition(rows):
    by_chunk = defaultdict(list)
    for row in rows:
        by_chunk[row["chunk"]].append(row)
    maintained = {"stable_high": [], "stable_low": [], "frequent_unresolved": []}
    samples = []
    attribution_counts = []
    for chunk, observations in sorted(by_chunk.items()):
        exposure_count = len(observations)
        verified = [row for row in observations if row["label"] is not None]
        directions = {row["label"] for row in verified}
        attribution_counts.append({
            "chunk": chunk,
            "exposures": exposure_count,
            "verified_uses": len(verified),
            "feedback_on_verified_uses": dict(Counter(row["answer_feedback"] for row in verified)),
            "verified_labels": dict(Counter(row["label"] for row in verified)),
        })
        enough_coverage = (
            len(verified) >= ROUTE_STABLE_AT
            and len({row["user"] for row in verified}) >= 3
            and len({row["query_group"] for row in verified}) >= 2
        )
        if exposure_count >= ROUTE_STABLE_AT:
            status = "frequent_unresolved"
            if enough_coverage and directions == {"supports"}:
                status = "stable_high"
            elif enough_coverage and directions == {"contradicts"}:
                status = "stable_low"
            maintained[status].append({
                "chunk": chunk, "exposures": exposure_count,
                "evidence": [row["trace"] for row in verified],
            })
            continue

        for row in verified:
            direction = row["label"]
            if direction in {"supports", "contradicts", "irrelevant"}:
                samples.append({
                    "trace": row["trace"], "query": row["query"], "chunk": chunk,
                    "label": "positive" if direction == "supports" else "negative",
                    "reason": direction, "answer_feedback": row["answer_feedback"],
                })
    return maintained, samples, attribution_counts


def _parse_json(raw: str) -> list:
    content = raw.strip()
    if content.startswith("```") and content.endswith("```"):
        content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
    result = json.loads(content)
    if not isinstance(result, list):
        raise ValueError("模型应返回 JSON 数组")
    return result


def _second_review(rows, ask):
    targets = [
        {k: row[k] for k in ("trace", "query", "verified_rule", "answer", "answer_feedback", "chunk", "stage")}
        | {"text": CHUNKS[row["chunk"]]}
        for row in rows
        if row["trace"] in {"t09", "t11", "t12"}
    ]
    if ask is None:
        return {"mode": "offline", "candidates": targets, "reviews": [], "pending": []}
    system = (
        "你复核 RAG 片段的使用记录。按问题、原文和已核验规则判断片段的贡献。"
        "回答好评或差评不能决定片段标签，未实际使用的片段直接标 unknown。"
        "标签只能是 supports、contradicts、irrelevant、unknown。"
        "仅输出 JSON 数组，每项包含 trace、chunk、label、evidence_quote。"
        "evidence_quote 要从片段原文逐字摘录，unknown 时可留空。"
    )
    # 单次集中复核，以便同一模型并排观察相互矛盾的反馈。
    raw = ask(system, json.dumps(targets, ensure_ascii=False))
    references = {(r["trace"], r["chunk"]): r["label"] or "unknown" for r in rows}
    candidates = {(r["trace"], r["chunk"]): r for r in targets}
    reviews = []
    reviewed: set[AttributionKey] = set()
    pending = []
    try:
        suggestions = _parse_json(raw)
    except (ValueError, IndexError):
        suggestions = []
        pending.append({"reason": "invalid_model_output"})
    for suggestion in suggestions:
        if not isinstance(suggestion, dict):
            continue
        trace, chunk = suggestion.get("trace"), suggestion.get("chunk")
        label, quote = suggestion.get("label"), suggestion.get("evidence_quote")
        if not isinstance(trace, str) or not isinstance(chunk, str):
            continue
        key = trace, chunk
        target = candidates.get(key)
        if not target or key in reviewed:
            continue
        if label not in ("supports", "contradicts", "irrelevant", "unknown"):
            continue
        if label != "unknown" and (target["stage"] != "used" or not isinstance(quote, str) or not quote.strip() or quote not in target["text"]):
            continue
        reviewed.add(key)
        record = {"trace": trace, "chunk": chunk, "label": label, "evidence_quote": quote if isinstance(quote, str) else ""}
        reviews.append(record)
        if label != references[key]:
            pending.append(record | {"reason": "review_disagrees", "reference": references[key]})
    pending.extend({"trace": t, "chunk": c, "reason": "missing_valid_review"} for t, c in sorted(candidates.keys() - reviewed))
    return {"mode": "model_review", "reviews": reviews, "pending": pending}


def run(ask=None):
    rows = list(_observations())
    maintained, samples, attribution_counts = _partition(rows)
    pairs = {(r["trace"], r["chunk"], r["label"]) for r in samples}
    check = {
        "separate_fragments_in_same_document": (
            [r["chunk"] for r in maintained["stable_high"]] == ["spec@3:1"]
            and ("t09", "spec@3:2", "positive") in pairs
        ),
        "old_rule_managed_separately": [r["chunk"] for r in maintained["stable_low"]] == ["archive@1:4"],
        "opposite_labels_for_different_queries": {
            ("t09", "notify@2:1", "negative"), ("t10", "notify@2:1", "positive"),
        }.issubset(pairs),
        "feedback_does_not_overwrite_verified_evidence": ("t11", "sdk@3:2", "positive") in pairs,
        "unused_or_unverified_excluded": not any(
            (r["trace"], r["chunk"]) in {("t05", "spec@3:2"), ("t10", "releases@1:3"), ("t12", "notes@1:2")}
            for r in samples
        ),
    }
    return {
        "passed": all(check.values()), "checks": check,
        "maintenance": maintained, "alignment_samples": samples,
        "attribution_counts": attribution_counts,
        "unresolved_attribution": [
            {"trace": row["trace"], "chunk": row["chunk"]}
            for row in rows
            if row["stage"] == "used" and row["label"] is None
        ],
        "review": _second_review(rows, ask),
        "online_evaluation": {
            "status": "design_only",
            "randomization": "按用户随机分组，固定文档、生成模型和提示",
            "variants": ["原检索模型与匹配索引", "新检索模型与匹配索引"],
            "metrics": ["正向反馈率", "负向反馈率", "反馈覆盖率", "每次请求成本"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
