"""从同一批候选比较纯向量排序和 DeepSeek Flash 重排。"""

from pathlib import Path

from workshops.rag.deepseek_workshop import ROOT, VectorIndex, answer, measure, read_json, rerank

HERE = Path(__file__).resolve().parent
RETRIEVE = 8
KEEP = 3
EMBEDDING = "BAAI/bge-small-zh-v1.5"


def run(client=None):
    if client is None:
        replay = read_json(HERE / "replay.json")
        return {**replay, "mode": "recorded_replay",
                "corpus_snapshot": "2026-11-01 的 8 篇文档快照，未包含后来并入的支付回滚条款"}

    index = VectorIndex(EMBEDDING, HERE.parent / "results" / "index")
    index_action = index.build_or_load()
    rows = []
    for question in read_json(ROOT / "questions.json"):
        prompt = question["question"]
        expected = question["evidence"]
        candidates = index.search(prompt, RETRIEVE)
        branches = {"baseline": candidates[:KEEP], "reranked": rerank(client, prompt, candidates, KEEP)}
        rows.append({
            "question": prompt,
            "expected_evidence": expected,
            "candidate_evidence": measure(expected, [chunk["document"] for chunk in candidates]),
            "candidates": candidates,
            **{
                branch: {
                    "chunks": chunks,
                    "metrics": measure(expected, [chunk["document"] for chunk in chunks]),
                    "answer": answer(client, prompt, chunks),
                }
                for branch, chunks in branches.items()
            },
        })
    return {
        "mode": "live", "embedding": EMBEDDING, "retrieve": RETRIEVE, "keep": KEEP,
        "index_action": index_action, "questions": rows,
    }
