import os
import json
import logging
import time
from typing import List, Dict, Tuple, Optional

import orjson
from tqdm import tqdm

# ========================= 合并自 self_instruct.py 的实现 =========================

DEFAULT_SEED_TASKS: List[str] = [
    "给出学习某项新技术的分步计划",
    "解释一个常见的数据结构并举例",
    "根据产品需求生成测试用例",
    "将一段英文文本总结为要点",
    "根据表结构编写 SQL 查询",
]


def _read_lines_txt(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _read_seed_jsonl(path: str) -> List[str]:
    items: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            instr = (
                obj.get("instruction")
                or obj.get("Instruction")
                or obj.get("task")
                or obj.get("Task")
            )
            if instr:
                items.append(str(instr).strip())
    return items


def _read_seed_json(path: str) -> List[str]:
    items: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        for obj in data:
            if not isinstance(obj, dict):
                continue
            instr = (
                obj.get("instruction")
                or obj.get("Instruction")
                or obj.get("task")
                or obj.get("Task")
            )
            if instr:
                items.append(str(instr).strip())
    return items


def load_seed_tasks(seed_file: Optional[str]) -> List[str]:
    base_dir = os.path.dirname(__file__)
    candidates: List[str] = []
    if seed_file:
        candidates.append(seed_file)
    candidates.extend([
        os.path.join(base_dir, "data", "seed_tasks.jsonl"),
        os.path.join(base_dir, "data", "seed_tasks.json"),
        os.path.join(base_dir, "data", "seed_tasks.txt"),
    ])

    for path in candidates:
        if not path:
            continue
        if not os.path.exists(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".jsonl":
                items = _read_seed_jsonl(path)
            elif ext == ".json":
                items = _read_seed_json(path)
            else:
                items = _read_lines_txt(path)
        except Exception:
            items = []
        if items:
            return items

    print("[Seeds] 未找到本地种子文件，回退到内置少量样例。建议在 data/seed_tasks.jsonl 放置上游默认任务以获得更好覆盖度。")
    return DEFAULT_SEED_TASKS


def call_model(provider: str, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
    if provider == "openai":
        from openai import OpenAI

        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    else:
        import dashscope
        from http import HTTPStatus

        resp = dashscope.Generation.call(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if resp.status_code == HTTPStatus.OK:
            return resp.output.text.strip()
        else:
            raise RuntimeError(f"DashScope error: {resp.code} {resp.message}")


INSTRUCTION_EXPAND_PROMPT = (
    """
你是数据合成专家。根据以下"种子任务"生成更多多样化的中文"指令任务"，用于指令微调数据集构建：

要求：
- 每条指令应简洁明确，避免含糊其辞
- 覆盖多领域（编程、数据分析、教育、法律、产品、写作等）
- 多样化指令类型（解释、生成、改写、归纳、评价、规划、推理等）
- 使用第二人称或直接式命令（如"请…"，"帮我…"）
- 仅输出指令，每行一条，不要编号或多余解释

种子任务：
{seed_list}

请直接给出生成的指令：
"""
).strip()


CLASSIFICATION_DETECT_PROMPT = (
    """
判断下面的"指令"是否是一个"分类任务"（classification），例如：情感分类、话题分类、文本是否属于某类别等。

仅回复一个词：Yes 或 No。

指令：{instruction}
"""
).strip()


def is_classification_task(provider: str, model: str, instruction: str, max_tokens: int, temperature: float) -> bool:
    try:
        reply = call_model(provider, model, CLASSIFICATION_DETECT_PROMPT.format(instruction=instruction), max_tokens=max_tokens, temperature=temperature)
        reply = reply.strip().lower()
        return reply.startswith("y")
    except Exception:
        return False


ANSWER_PROMPT_TEMPLATE_INPUT_FIRST = (
    """
请根据以下"指令"构造一个"输入-输出"示例用于指令微调。

要求：
- 先给出"Input:"一行，再给出"Output:"一行
- 用中文给出自然、合理且不含敏感内容的示例
- 输出应为最终答案，不要解释过程

指令：{instruction}
"""
).strip()


ANSWER_PROMPT_TEMPLATE_OUTPUT_FIRST = (
    """
请根据以下"分类指令"构造一个"输出-输入"示例（Output-first）。

要求：
- 先给出该分类任务的一个可能"Output:"（如类别标签），再给出与该输出一致的"Input:"文本
- 两行输出，格式严格为：
Output: <简短标签或结论>
Input: <与标签一致的文本或内容>
- 用中文给出自然、合理且不含敏感内容的示例

指令：{instruction}
"""
).strip()


def parse_io_from_text(text: str) -> Tuple[str, str]:
    """解析可能为多行块的 Input/Output。
    规则：
    - 遇到以 "Input:" 或 "Output:" 开头的行后，进入对应段落，收集后续行，直到遇到另一段落标签或文本结束。
    - 标签行后同一行的内容（冒号后）也会并入当前段落。
    """
    lines = [ln.rstrip() for ln in text.splitlines()]
    collect_input: List[str] = []
    collect_output: List[str] = []
    mode: Optional[str] = None  # "input" | "output" | None

    def starts_with_label(s: str, label: str) -> bool:
        return s.lower().startswith(label)

    for raw in lines:
        line = raw.strip()
        if starts_with_label(line, "input:"):
            mode = "input"
            collect_input.append(line.split(":", 1)[1].strip())
            continue
        if starts_with_label(line, "output:"):
            mode = "output"
            collect_output.append(line.split(":", 1)[1].strip())
            continue

        if mode == "input":
            collect_input.append(raw)
        elif mode == "output":
            collect_output.append(raw)
        else:
            # 未显式进入段落的散落文本，忽略
            pass

    input_text = "\n".join([s for s in collect_input if s]).strip()
    output_text = "\n".join([s for s in collect_output if s]).strip()
    return input_text, output_text


DISALLOWED_SUBSTRINGS = [
    "自杀", "爆炸物", "武器制作", "仇恨言论", "色情", "未成年人", "恐怖主义",
]


def passes_basic_filter(instruction: str, input_text: str, output_text: str) -> bool:
    if not instruction or len(instruction) < 4:
        return False
    if not output_text or len(output_text) < 2:
        return False
    if len(input_text) > 2000 or len(output_text) > 2000:
        return False
    text_all = f"{instruction}\n{input_text}\n{output_text}"
    for bad in DISALLOWED_SUBSTRINGS:
        if bad in text_all:
            return False
    if input_text.strip() == output_text.strip():
        return False
    if instruction.strip() == input_text.strip() or instruction.strip() == output_text.strip():
        return False
    return True


def save_jsonl(records: List[Dict], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        for rec in records:
            f.write(orjson.dumps(rec))
            f.write(b"\n")


def deduplicate_strings(items: List[str]) -> List[str]:
    seen = set()
    unique_list = []
    for item in items:
        key = item.strip()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        unique_list.append(key)
    return unique_list

# ======================= 以上为合并的公共函数与常量 =======================


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def step1_generate_instructions(
    provider: str,
    model: str,
    seed_tasks: List[str],
    num_instructions: int,
    max_tokens: int,
    temperature: float,
    out_dir: str,
) -> List[str]:
    seed_text = "\n".join(f"- {s}" for s in seed_tasks)
    expanded_instructions: List[str] = []
    start_ts = time.time()
    while len(expanded_instructions) < num_instructions:
        prompt = INSTRUCTION_EXPAND_PROMPT.format(seed_list=seed_text)
        try:
            text = call_model(provider.lower(), model, prompt, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            logging.error(f"[Step1] 模型调用失败，将重试。error={e}")
            continue
        candidates = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
        logging.debug(f"[Step1] 本次生成候选 {len(candidates)} 条，示例：{candidates[:2]}")
        expanded_instructions.extend(candidates)
        expanded_instructions = deduplicate_strings(expanded_instructions)
        logging.info(f"[Step1] 当前累计 {len(expanded_instructions)} 条指令…")

    expanded_instructions = expanded_instructions[:num_instructions]
    # 保存为 JSONL（每行一个对象）
    step1_path = os.path.join(out_dir, "step1_instructions.jsonl")
    save_jsonl([{"instruction": s} for s in expanded_instructions], step1_path)
    logging.info(f"[Step1] 指令扩展完成，共 {len(expanded_instructions)} 条 → {step1_path}，耗时 {time.time()-start_ts:.1f}s")
    return expanded_instructions


def step2_classify_instructions(
    provider: str,
    model: str,
    instructions: List[str],
    max_tokens: int,
    out_dir: str,
) -> List[Tuple[str, bool]]:
    start_ts = time.time()
    results: List[Tuple[str, bool]] = []
    for instr in tqdm(instructions, desc="Step2 分类识别"):
        flag = is_classification_task(provider.lower(), model, instr, max_tokens=64, temperature=0)
        results.append((instr, flag))
    step2_path = os.path.join(out_dir, "step2_is_classification.jsonl")
    save_jsonl([
        {"instruction": instr, "is_classification": is_clf} for instr, is_clf in results
    ], step2_path)
    pos = sum(1 for _, f in results if f)
    neg = len(results) - pos
    logging.info(f"[Step2] 分类识别完成 → {step2_path} | 分类={pos}, 非分类={neg}，耗时 {time.time()-start_ts:.1f}s")
    return results


def step3_generate_instances(
    provider: str,
    model: str,
    clf_pairs: List[Tuple[str, bool]],
    instances_per_instruction: int,
    max_tokens: int,
    temperature: float,
    out_dir: str,
) -> List[Dict[str, str]]:
    start_ts = time.time()
    records: List[Dict[str, str]] = []
    for instr, is_clf in tqdm(clf_pairs, desc="Step3 实例生成"):
        for _ in range(max(1, instances_per_instruction)):
            try:
                if is_clf:
                    raw = call_model(
                        provider.lower(),
                        model,
                        ANSWER_PROMPT_TEMPLATE_OUTPUT_FIRST.format(instruction=instr),
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                else:
                    raw = call_model(
                        provider.lower(),
                        model,
                        ANSWER_PROMPT_TEMPLATE_INPUT_FIRST.format(instruction=instr),
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
            except Exception as e:
                raw = f"Output: (生成失败) {e}\nInput: "

            input_text, output_text = parse_io_from_text(raw)
            if not input_text and not output_text:
                output_text = raw.strip()
            rec = {
                "instruction": instr.strip(),
                "input": input_text.strip(),
                "output": output_text.strip(),
                "is_classification": is_clf,
                "raw": raw,
            }
            records.append(rec)

    step3_path = os.path.join(out_dir, "step3_raw_instances.jsonl")
    save_jsonl(records, step3_path)
    logging.info(f"[Step3] 实例生成完成，共 {len(records)} 条 → {step3_path}，耗时 {time.time()-start_ts:.1f}s")
    return records


def step4_filter_and_dedupe(records: List[Dict[str, str]], out_dir: str) -> List[Dict[str, str]]:
    # 过滤
    filtered = [r for r in records if passes_basic_filter(r.get("instruction", ""), r.get("input", ""), r.get("output", ""))]
    # 去重（instruction + input）
    seen_pairs = set()
    deduped: List[Dict[str, str]] = []
    for r in filtered:
        key = (r.get("instruction", "").strip(), r.get("input", "").strip())
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        deduped.append(r)

    step4_path = os.path.join(out_dir, "step4_final.jsonl")
    save_jsonl([{k: r[k] for k in ["instruction", "input", "output"] if k in r} for r in deduped], step4_path)
    logging.info(f"[Step4] 过滤与去重完成：输入 {len(records)} → 过滤后 {len(filtered)} → 去重后 {len(deduped)} 条 → {step4_path}")
    return deduped


# ===== 固定配置（无需命令行参数）=====
PROVIDER = "openai"          # 可改为 "dashscope"
MODEL = "gpt-4o-mini"        # 可改为 "qwen-plus" 等
NUM_INSTRUCTIONS = 5          # 测试默认：5 条
INSTANCES_PER_INSTRUCTION = 1
SEED_FILE = None              # 可设置为路径："data/seed_tasks.jsonl"
OUT_DIR = "data/workshop"
TEMPERATURE = 0.7
MAX_TOKENS = 256              # 测试默认：较小 tokens


def run_workshop() -> None:
    _ensure_dir(OUT_DIR)
    _setup_logging(logging.INFO)

    # 自动选择可用的提供商与模型
    def resolve_provider_and_model(default_provider: str, default_model: str) -> Tuple[str, str]:
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        dashscope_key = os.environ.get("DASHSCOPE_API_KEY", "")
        provider = default_provider
        model = default_model
        if provider == "openai" and not openai_key and dashscope_key:
            provider = "dashscope"
            if model == "gpt-4o-mini":
                model = "qwen-plus"
        elif provider == "dashscope" and not dashscope_key and openai_key:
            provider = "openai"
            if model == "qwen-plus":
                model = "gpt-4o-mini"
        return provider, model

    provider_use, model_use = resolve_provider_and_model(PROVIDER, MODEL)
    logging.info(f"[Prep] 使用提供商: {provider_use}, 模型: {model_use}")

    # Step 0: 加载种子任务
    seed_tasks = load_seed_tasks(SEED_FILE)
    logging.info(f"[Prep] 载入种子任务 {len(seed_tasks)} 条。示例：{seed_tasks[:3]}")

    # Step 1: 指令生成
    instructions = step1_generate_instructions(
        provider=provider_use,
        model=model_use,
        seed_tasks=seed_tasks,
        num_instructions=NUM_INSTRUCTIONS,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        out_dir=OUT_DIR,
    )

    # Step 2: 分类识别
    clf_pairs = step2_classify_instructions(
        provider=provider_use,
        model=model_use,
        instructions=instructions,
        max_tokens=MAX_TOKENS,
        out_dir=OUT_DIR,
    )

    # Step 3: 实例生成
    raw_records = step3_generate_instances(
        provider=provider_use,
        model=model_use,
        clf_pairs=clf_pairs,
        instances_per_instruction=INSTANCES_PER_INSTRUCTION,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        out_dir=OUT_DIR,
    )

    # Step 4: 过滤与去重
    _ = step4_filter_and_dedupe(raw_records, out_dir=OUT_DIR)
    print("[Done] Workshop 全流程完成！")


if __name__ == "__main__":
    run_workshop()


