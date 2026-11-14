"""用固定语料和问题观察检索、证据覆盖与生成，或换入自己的文档。"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.chat import chat
from workshop_runtime.deepseek import load_environment, model_name

DATA = Path(__file__).parent / 'data'
ID_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]*')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_documents(path):
    documents = read_json(path)
    if not isinstance(documents, list) or not documents:
        raise ValueError('语料必须是非空 JSON 数组。')
    ids = set()
    for doc in documents:
        if not isinstance(doc, dict):
            raise ValueError('每份文档需要 id 和 text。')
        doc_id, text = doc.get('id'), doc.get('text')
        if not isinstance(doc_id, str) or not ID_PATTERN.fullmatch(doc_id):
            raise ValueError('文档 ID 需为字母或数字开头，可含 _ . : -。')
        if doc_id in ids:
            raise ValueError(f'文档 ID 重复：{doc_id}')
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f'文档正文为空：{doc_id}')
        ids.add(doc_id)
    return documents


def load_cases(path, document_ids):
    cases = read_json(path)
    if not isinstance(cases, list) or not cases:
        raise ValueError('问题集必须是非空 JSON 数组。')
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('每个问题需要对象记录。')
        case_id, question = case.get('id'), case.get('question')
        if not isinstance(case_id, str) or not case_id.strip() or case_id in ids:
            raise ValueError('问题 ID 需要非空且唯一。')
        ids.add(case_id)
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f'问题不能为空：{case_id}')
        expected = case.get('expected_document_ids')
        if (not isinstance(expected, list) or any(not isinstance(i, str) for i in expected)
                or len(set(expected)) != len(expected) or not set(expected) <= document_ids):
            raise ValueError(f'参考文档 ID 缺失、重复或不在语料中：{case_id}')
        abstain = case.get('expected_abstention')
        if type(abstain) is not bool or abstain == bool(expected):
            raise ValueError(f'需标注证据不足，或提供非空参考文档：{case_id}')
        if not isinstance(case.get('reference_answer'), str) or not case['reference_answer'].strip():
            raise ValueError(f'需要人工参考答案或判定依据：{case_id}')
    return cases


def fingerprint(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def evidence_review(report, case):
    expected = set(case['expected_document_ids'])
    hit_ids = {hit['id'] for hit in report['hits']}
    return {
        'expected_document_ids': sorted(expected),
        'missing_document_ids': sorted(expected - hit_ids),
        'all_reference_documents_retrieved': expected <= hit_ids if expected else None,
        'expected_abstention': case['expected_abstention'],
        'reference_answer': case['reference_answer'],
        'answer_review': '待人工核对：事实、引用是否支持结论、证据不足时是否拒答',
    }


class VectorQA:
    def __init__(self, documents):
        import chromadb
        self.embedding_model = os.getenv('WORKSHOP_LOCAL_EMBEDDING_MODEL') or 'BAAI/bge-m3'
        if os.getenv('WORKSHOP_LOCAL_EMBEDDING_MODEL'):
            from fastembed import TextEmbedding
            model = TextEmbedding(self.embedding_model, cache_dir=os.getenv('FASTEMBED_CACHE_PATH'))
            self.embed = lambda text: next(iter(model.embed([text]))).tolist()
        else:
            from FlagEmbedding import BGEM3FlagModel
            model = BGEM3FlagModel(self.embedding_model, use_fp16=False)
            self.embed = lambda text: model.encode([text], batch_size=1)['dense_vecs'][0].tolist()
        self.corpus_sha256 = fingerprint(documents)
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', str(Path(__file__).parent / 'results' / 'chromadb')))
        # 内容与嵌入来源共同标识索引，避免删改文档后召回旧版本残留。
        name = 'qa_' + fingerprint([self.embedding_model, self.corpus_sha256])[:24]
        self.collection = client.get_or_create_collection(name=name)
        self.collection.upsert(ids=[d['id'] for d in documents], documents=[d['text'] for d in documents],
                               embeddings=[self.embed(d['text']) for d in documents])

    def query(self, question, top_k, search_only=False):
        started = perf_counter()
        results = self.collection.query(query_embeddings=[self.embed(question)], n_results=top_k)
        hits = [{'id': doc_id, 'text': text, 'distance': distance} for doc_id, text, distance in zip(
            results['ids'][0], results['documents'][0], results['distances'][0])]
        if not hits:
            raise RuntimeError('没有检索到文档，请检查索引。')
        print(f'问题：{question}', flush=True)
        for hit in hits:
            print(f"命中 [{hit['id']}]，距离 {hit['distance']:.4f}：{hit['text']}", flush=True)
        report = {'question': question, 'top_k': top_k, 'embedding_model': self.embedding_model,
                  'corpus_sha256': self.corpus_sha256,
                  'mode': 'retrieval_only' if search_only else 'retrieval_and_generation',
                  'hits': hits, 'answer': None, 'generation_calls': 0}
        try:
            if not search_only:
                context = '\n'.join(f"[{h['id']}] {h['text']}" for h in hits)
                report['generation_model'] = model_name()
                report['generation_calls'] = 1  # 逻辑调用次数，不包含 SDK 内部重试。
                report['messages'] = [{'role': 'user', 'content': (
                    '只依据下面的教学资料回答问题，并引用实际使用的文档 ID。证据不足时明确说明。'
                    f'\n\n资料：{context}\n\n问题：{question}')}]
                report['prompt_sha256'] = fingerprint(report['messages'])
                answer = chat(messages=report['messages'])
                cited = re.findall(r'\[([A-Za-z0-9][A-Za-z0-9_.:-]*)\]', answer)
                report.update(answer=answer, citations=cited,
                              citations_from_current_hits=bool(cited) and set(cited) <= {h['id'] for h in hits})
                print('生成的结果：', answer)
            else:
                print('本轮只观察向量检索。尚未调用聊天模型。')
        except Exception as error:
            report['error'] = f'{type(error).__name__}: {error}'
        report['total_elapsed_seconds'] = perf_counter() - started
        return report


def save_report(path, report):
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'本轮证据与设置：{path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('--question', help='单个问题；不指定时使用合同主要义务问题')
    inputs.add_argument('--cases', type=Path, help='固定问题集 JSON，逐题保留实际证据与回答')
    parser.add_argument('--documents', type=Path, default=DATA / 'documents.json')
    parser.add_argument('--top-k', type=int, default=1)
    parser.add_argument('--search-only', action='store_true', help='只运行嵌入与检索，不调用聊天服务')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    load_environment()
    try:
        documents = load_documents(args.documents)
        if not 1 <= args.top_k <= len(documents):
            raise ValueError('--top-k 必须在 1 与语料文档数量之间。')
        cases = load_cases(args.cases, {d['id'] for d in documents}) if args.cases else None
        question = args.question if args.question is not None else '合同中的主要义务是什么？'
        if not question.strip():
            raise ValueError('--question 不能为空。')
    except (ValueError, OSError) as error:
        parser.error(str(error))
    started = perf_counter()
    qa = VectorQA(documents)
    indexing_seconds = perf_counter() - started
    if cases is None:
        report = qa.query(question, args.top_k, args.search_only)
        report['indexing_elapsed_seconds'] = indexing_seconds
    else:
        records = []
        for case in cases:
            record = qa.query(case['question'], args.top_k, args.search_only)
            record['case_id'] = case['id']
            record['review'] = evidence_review(record, case)
            records.append(record)
        answerable = [r for r in records if not r['review']['expected_abstention']]
        covered = sum(r['review']['all_reference_documents_retrieved'] for r in answerable)
        report = {
            'corpus_sha256': qa.corpus_sha256, 'cases_sha256': fingerprint(cases),
            'embedding_model': qa.embedding_model, 'top_k': args.top_k,
            'mode': 'retrieval_only' if args.search_only else 'retrieval_and_generation',
            'indexing_elapsed_seconds': indexing_seconds, 'cases': records,
            'summary': {'questions': len(records), 'answerable_questions': len(answerable),
                        'fully_covered_questions': covered,
                        'reference_evidence_coverage': covered / len(answerable) if answerable else None,
                        'generation_calls': sum(r['generation_calls'] for r in records),
                        'execution_errors': sum('error' in r for r in records),
                        'answer_quality': '待人工按每题参考依据核对，未自动评分'},
            'total_elapsed_seconds': perf_counter() - started,
        }
        print('问题集摘要：' + json.dumps(report['summary'], ensure_ascii=False))
    save_report(args.output, report)
    if ('error' in report or report.get('summary', {}).get('execution_errors')):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
