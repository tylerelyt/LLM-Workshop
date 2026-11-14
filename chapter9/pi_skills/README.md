<a id="pi-feishu"></a>

# Pi SDK 与技能加载

固定模型、资料和问题，比较两个独立会话是否加载 `lark-doc` 技能时的读取行为。目标是从真实工具结果核对答案的引用与版本，并说明技能改变了哪些读取范围或调用次数。

## 工程任务

加载了技能不代表模型已经读取指引，也不代表最终答案更准确。

在 [pi_probe.mjs](pi_probe.mjs) 中，固定资料、模型与问题，只改变是否加载 lark-doc Skill，并使用独立会话。

比较实际 Skill 读取、文档范围、版本与答案，再判断该指引是否改变了有效行为。

## 准备模型和技能

需要 Node.js 22.19 或更新版本、课程聊天模型配置，以及官方 `lark-doc` 技能。程序默认从 `~/.agents/skills/lark-doc` 加载，也可用 `--skill-dir` 指向自己的安装目录，目录中需要 `SKILL.md` 与 `references/lark-doc-fetch.md`。[飞书 CLI 与技能安装](https://github.com/larksuite/cli#readme)

从仓库根目录运行。课程支持 `OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_API_KEY`，也兼容 `DEEPSEEK_API_KEY` 和可选的 `DEEPSEEK_MODEL`、`DEEPSEEK_BASE_URL`。[模型配置](../../README-DEEPSEEK.md)

```bash
npm --prefix chapter9/pi_skills ci
```

两轮都会获得 `read_feishu`，读取范围为目录、关键词或章节，第二轮还会获得读取技能说明的 `read` 工具。技能提供操作指引，文档权限和读取能力由接入的工具提供。两轮使用独立会话，避免第一轮内容进入第二轮的对话历史。

## 从可核对的合成文档开始

程序自带三个片段，包括“旧版规则（已废止）”“现行发布规则”和“复盘归档”，版本号为 7。先预测应该引用哪条规则，以及资料能否支持电话号码。

```bash
npm --prefix chapter9/pi_skills run lab -- --fixture \
  --question '发布前由谁审批？文档能否证实审批人的手机号？'
```

两轮都应依据现行规则回答由当班 SRE 负责人审批，并说明缺少手机号依据。检查 `report.json` 中实际返回的 `verified_reads.content`，确认答案中的块标识和版本确实能从读取结果找到。旧规则的标题或模型口头说“已核实”都不能替代原文。

本路径运行在线模型、Pi 会话与合成文档工具，不调用真实飞书，也不需要飞书扫码授权。它验证本课的模型与技能加载对照。

## 换成一份真实教学文档

使用本机配置好的 `lark-cli` 用户授权，选择一份有权读取并可提交给所选模型的教学文档。检查程序只读取该文档的目录并报告是否成功及版本号。

```bash
python3 chapter9/pi_skills/check_feishu_access.py
DOC_URL='替换为教学文档链接'
python3 chapter9/pi_skills/check_feishu_access.py --doc "$DOC_URL"
npm --prefix chapter9/pi_skills run lab -- --doc "$DOC_URL" \
  --question '发布前由谁审批？文档能否证实审批人的手机号？'
```

把问题改成这份文档里一条可核验的规则和一个缺少依据的问题。两轮保持相同文档、问题和模型。检查真实返回的原文、版本与回答引用，而非把合成样例中的审批人当作真实答案。真实路径的授权和内容访问需要独立验证。

## 修改一条技能指引

先完成原技能的前后对照，再复制 `lark-doc` 到自己的实验目录。只修改副本中与读取顺序或证据引用有关的一条指引，例如先查看目录定位现行章节，再引用块标识和版本。保留技能名称、引用文件路径与只读权限。可以让 Coding Agent 完成这处修改，先预测会影响哪种读取，再新建运行查看。

重新运行相同命令，只把 `--skill-dir` 指向副本。程序每次建立新会话和新的 `pi-*` 目录，旧报告会保留。比较报告的 `skill_source.sha256`，确认实际使用了修改后的说明，同时固定模型、文档版本和问题。文档版本改变时先重新建立对照，不能把不同资料造成的变化归因于技能。

## 报告与行为验收

报告位于 `chapter9/pi_skills/results/pi-*/report.json`。

- `document_source` 区分 `synthetic_fixture` 与 `live_feishu`。
- `active_tools`、`skill_advertised` 和已完成的 `read` 调用说明两轮实际提供和读取了哪些技能。
- `verified_reads` 保存实际读取范围、来源、版本与返回内容，逐条对照最终答案。
- `tools` 记录调用参数与完成或失败状态，比较读取范围和调用次数。
- `skill_source` 记录技能目录及说明和读取参考文件的内容指纹。

对照两轮答案与对应原文，解释现行规则引用、无依据问题的处理和调用差异。报告文件存在、读取次数更多或回答更长，都需结合内容正确性判断；一次模型波动不足以说明稳定改善。

默认终端依次展示两轮实际 Skill 读取、文档读取范围、块内容、版本与最终回答，最后汇总读取路径。先直接对照这些结果，再在 `report.json` 查看完整工具参数；较长原文会明确标注截断。

真实文档内容会保存在本地报告中，分享记录时只使用可公开的教学资料并去除敏感内容。清理时只删除本课自己生成的 `results/pi-*` 目录和实验技能副本。[CLI Skill](../cli_skills/README.md) · [主题目录](../README.md)

## 在自己的项目中使用

为自己反复执行的一个操作写技能说明，固定任务和资料，用独立会话比较加载前后的真实执行。先用[CLI Skill](../cli_skills/README.md)把脚本本身调通，再检查技能是否改变读取范围、参数选择或结果呈现。
