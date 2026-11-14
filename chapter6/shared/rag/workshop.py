"""两阶段 RAG 实验入口。复用原课代码，保留每一阶段的实际结果。"""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def measure(expected, actual):
    """按文档来源评估；一篇文档的多个块不重复计分。"""
    expected = set(expected)
    unique = list(dict.fromkeys(actual))
    hits = expected.intersection(unique)
    return {
        "evidence_recall": len(hits) / len(expected) if expected else None,
        "reciprocal_rank": next((1 / (i + 1) for i, x in enumerate(unique) if x in expected), 0),
    }


def check_data():
    docs, questions = read_json(ROOT / "documents.json"), read_json(ROOT / "questions.json")
    ids = {d["id"] for d in docs}
    assert len(ids) == len(docs), "文档标识重复"
    for q in questions:
        assert q["evidence"] and set(q["evidence"]) <= ids, "标注引用了不存在的文档"
    return {"documents": len(docs), "questions": len(questions), "status": "材料引用检查通过"}


def run(args):
    # 重模型按需加载；检查题目不需要下载权重。
    import numpy as np
    from vendor.rag_pipeline import BGERetrievalSystem, BGEReranker, Document, RetrievalResult, LLMGenerator

    if args.retrieve < args.keep or args.keep < 1:
        raise ValueError("召回量必须不小于最终入选量，入选量须为正数")
    check_data()
    docs = read_json(ROOT / "documents.json")
    questions = read_json(ROOT / "questions.json")
    if args.question:
        questions = [{"question": args.question, "evidence": []}]
    retriever = BGERetrievalSystem(args.embedding)
    # 适合教学小语料的内存向量索引；不是持久化向量数据库。
    retriever.add_documents([Document(**d) for d in docs])
    reranker = BGEReranker(args.reranker)
    generator = LLMGenerator(model=args.model) if args.generate else None
    rows = []
    for q in questions:
        started = perf_counter()
        candidates = retriever.search(q["question"], args.retrieve)
        recall_ms = (perf_counter() - started) * 1000
        baseline = candidates[:args.keep]
        started = perf_counter()
        pairs = [[q["question"], x.document.title + "\n" + x.document.content] for x in candidates]
        # FlagEmbedding 对单个输入可能返回标量，统一为一维数组。
        scores = np.asarray(reranker.reranker.compute_score(pairs), dtype=float).reshape(-1)
        if len(scores) != len(candidates) or not np.isfinite(scores).all():
            raise ValueError("重排器返回的分数数量或数值无效")
        order = np.argsort(-scores, kind="stable")[:args.keep]
        ranked = [RetrievalResult(candidates[int(j)].document, float(scores[j]), i + 1)
                  for i, j in enumerate(order)]
        rerank_ms = (perf_counter() - started) * 1000
        def pack(results):
            return [{"document": x.document.parent_id or x.document.id,
                     "chunk": x.document.chunk_id, "text": x.document.content,
                     "score": x.score, "rank": i + 1} for i, x in enumerate(results)]
        row = {"question": q["question"], "expected_evidence": q["evidence"],
               "candidates": pack(candidates), "without_reranker": pack(baseline),
               "with_reranker": pack(ranked), "recall_ms": recall_ms, "rerank_ms": rerank_ms}
        if q["evidence"]:
            for label in ["without_reranker", "with_reranker"]:
                row[label + "_metrics"] = measure(q["evidence"], [x["document"] for x in row[label]])
        if generator:
            for label, results in [("without_reranker", baseline), ("with_reranker", ranked)]:
                answer = generator.generate_answer(q["question"], results)
                # 检索相关性分数不是答案正确的概率，舍弃原示例的 confidence。
                row[label + "_answer"] = {k: answer[k] for k in ["answer", "sources"]}
        rows.append(row)
    fingerprint = hashlib.sha256((ROOT / "documents.json").read_bytes()).hexdigest()
    save_json(args.output, {"corpus_sha256": fingerprint,
              "embedding": args.embedding, "reranker": args.reranker,
              "retrieval_k": args.retrieve, "final_k": args.keep,
              "generation_enabled": args.generate, "results": rows})
    print(f"实际结果已写入 {args.output}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check-data", action="store_true")
    p.add_argument("--embedding", default="BAAI/bge-m3")
    p.add_argument("--reranker", default="BAAI/bge-reranker-v2-m3")
    p.add_argument("--retrieve", type=int, default=8)
    p.add_argument("--keep", type=int, default=3)
    p.add_argument("--question")
    p.add_argument("--generate", action="store_true")
    p.add_argument("--model", help="Override the configured chat model")
    p.add_argument("--output", default=str(ROOT / "results/run.json"))
    args = p.parse_args()
    if args.check_data:
        print(json.dumps(check_data(), ensure_ascii=False))
    else:
        run(args)
