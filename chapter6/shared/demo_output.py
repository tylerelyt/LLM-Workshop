"""检索练习的课堂输出；所有内容来自本轮运行结果。完整轨迹仍保存在 JSON。"""


def show(variant, result, case="first"):
    titles = {5: "语义去重", 6: "切块质量反馈", 7: "跨语言检索", 8: "迭代图检索", 9: "检索服务接入 Harness"}
    print(f"\n{titles[variant]}")
    if variant == 5:
        print("模式：在线模型判重" if result["mode"] == "model" else "模式：固定教学数据、离线判重替身")
        print("任务：合并同版退款规则，保留版本冲突和原文出处。")
        print("处理前：" + " → ".join(result["before"]))
        for job in result["processed_jobs"]:
            if job["status"] in {"merged", "conflict", "queued", "keep"}:
                print(f"  {job['left_id']} / {job['right_id']}：{job['status']}；{job['reason']}")
        print("处理后：" + " → ".join(result["after"]))
        print(f"代表：{result['canonical_id']}；来源：{', '.join(result['source_ids']) or '无'}")
        for row in result["archive"]:
            print(f"  归档原文 [{row['id']}@{row['revision']}] {row['body']}")
    elif variant == 6:
        print("模式：固定反馈回放；片段标签来自独立核验，不由点赞决定。")
        for row in result["alignment_samples"][:3]:
            print(f"问题：{row['query']}")
            print(f"  [{row['chunk']}] {row['text']}")
            print(f"  回答反馈 {row['answer_feedback']}；片段标签 {row['label']}；依据 {row['reason']}")
        for kind, title in [("stable_high", "稳定支持"), ("stable_low", "稳定冲突"), ("frequent_unresolved", "待复核")]:
            print(f"{title}：" + (", ".join(row["chunk"] for row in result["maintenance"][kind]) or "无"))
        print(f"未确认归因：{len(result['unresolved_attribution'])} 条；本轮模型复核：{result['review']['mode']}")
        for review in result["review"]["reviews"]:
            print(f"  模型复核 [{review['trace']} / {review['chunk']}]：{review['label']}；原文：{review['evidence_quote']}")
        for pending in result["review"]["pending"]:
            print(f"  待复核：{pending.get('trace', '')} / {pending.get('chunk', '')}；{pending['reason']}")
        print("线上 A/B：仅设计方案，本次没有测量线上改善。")
    elif variant == 7:
        print(f"模式：{'固定译文离线回放' if result['mode'] == 'offline_replay' else '在线模型翻译'}；总候选名额 {result['candidate_budget']}")
        selected = result["cases"] if case == "all" else (result["cases"][:1] if case == "first" else [row for row in result["cases"] if row["case_id"] == case])
        print(f"显示 {len(selected)}/{len(result['cases'])} 题；--case all 查看全部，--case CASE_ID 聚焦单题。")
        print("题目 ID：" + ", ".join(row["case_id"] for row in result["cases"]))
        for case in selected:
            print(f"\n问题 [{case['case_id']}]：{case['question']}")
            print(f"  核验目标：{case['expected_source_fragment']}")
            for p in case["baseline_hits"]:
                print(f"  基线 [{p['id']}@{p['version']}] {p['text']}")
            print(f"  目标片段命中：合库 {case['baseline_found']} → 原问题分库 {case['raw_split_found']} → 语种适配 {case['adapted_found']}")
            for lang, query in case["adapted_queries"].items():
                if lang != case["query_language"]:
                    print(f"  实际查询 [{lang}]：{query}")
            for hits in case["adapted_hits_by_language"].values():
                for p in hits:
                    print(f"  [{p['id']}@{p['version']}] {p['text']}")
                    print(f"    来源：{p['source']}")
        print(f"\n本组 Recall@2：{result['baseline_recall_at_2']:.0%} → {result['raw_split_recall_at_2']:.0%} → {result['adapted_recall_at_2']:.0%}")
    elif variant == 8:
        print(f"模式：{'离线策略、模拟图谱' if result['mode'] == 'offline' else '在线模型、模拟图谱'}；步数上限 {result['step_limit']}")
        print(f"问题：{result['question']}")
        print(f"一次展开：完整={result['one_shot']['complete']}；{result['one_shot']['why']}")
        observations = {row["observation_id"]: row for row in result["observations"]}
        for step, row in enumerate(result["trace"], 1):
            print(f"步骤 {step}：{row.get('from', '?')} --{row.get('relation', row.get('edge_id', '?'))}--> {row.get('observation_id', row['status'])}")
            if row.get("observation_id") in observations:
                print("  观察：" + observations[row["observation_id"]]["excerpt"])
        print(f"证据闭合：{result['complete']}")
        answer = result["answer"]
        print(f"结论：{answer['team']}；{answer['policy']}" if answer else "结论：证据不足，不输出团队和通道。")
    elif variant == 9:
        print(f"模式：真实 stdio MCP；{'在线模型参与作答' if result['model'] else '仅协议与索引刷新，不运行模型'}")
        print("发现工具：" + ", ".join(t["function"]["name"] for t in result["tool_schema"]))
        for phase in ("before", "after"):
            snapshot = result[phase]
            print(f"{'更新前' if phase == 'before' else '更新后'}：语料指纹前 12 位 {snapshot['corpus_revision'][:12]}")
            for p in snapshot["passages"]:
                print(f"  [{p['citation_id']}] {p['text']}")
        for turn in result["answers"]:
            print(f"问题：{turn['question']}")
            for call in turn["observations"]:
                print(f"  调用 {call['tool']}({call['arguments']})")
                for passage in call["result"]["passages"]:
                    print(f"  本轮原文 [{passage['citation_id']}] {passage['text']}")
                    print(f"    来源：{passage['source']}")
            print(f"  回答：{turn['response']['answer']}；引用：{', '.join(turn['response']['citations']) or '无'}")
    checks = result.get("checks", {})
    if checks:
        failed = [name for name, passed in checks.items() if not passed]
        scope = "离线标签规则检查（不代表模型复核通过）" if variant == 6 else "行为检查"
        print(f"{scope}：{sum(bool(v) for v in checks.values())}/{len(checks)} 通过")
        for name in failed:
            print(f"  未通过：{name}")
