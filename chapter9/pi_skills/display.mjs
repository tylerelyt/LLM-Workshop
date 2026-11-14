// 课堂视图只展示本轮真实记录；完整工具轨迹保存在 report.json。
function readScope(read) {
  return `${read.scope}${read.block_id ? ` / ${read.block_id}` : ""}${read.keyword ? ` / ${read.keyword}` : ""}`;
}

export function showRun(run) {
  console.log(`\n=== ${run.name === "baseline" ? "未加载 Skill" : "加载 lark-doc Skill"} ===`);
  const skillReads = run.tools.filter((call) => call.tool === "read" && call.completed);
  console.log(`实际 Skill 读取：${skillReads.length ? skillReads.map((call) => call.args.path).join(", ") : "无"}`);
  for (const [index, read] of run.verified_reads.entries()) {
    console.log(`读取 ${index + 1}：${readScope(read)}；版本 ${read.revision_id}`);
    console.log(`  来源：${read.source}`);
    const text = typeof read.content === "string" ? read.content : JSON.stringify(read.content);
    console.log(text.length <= 600 ? text : `${text.slice(0, 600)}\n…本次返回较长，完整内容见 report.json 的 verified_reads。`);
  }
  for (const call of run.tools.filter((call) => call.error)) console.log(`工具失败 ${call.tool}：${call.error}`);
  console.log(`实际回答：\n${run.answer || "无回答"}`);
}

export function showComparison(runs) {
  console.log("\n=== 同一问题的读取对照 ===");
  for (const run of runs) {
    console.log(`${run.name}：${run.verified_reads.length} 次文档读取；${run.verified_reads.map(readScope).join(" → ") || "未读取文档"}`);
  }
  console.log("核对两份回答的原文、块 ID、版本和证据缺口；加载 Skill 本身不代表回答改善。");
}
