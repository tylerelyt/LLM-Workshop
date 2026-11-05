"""DeepSeek Flash 通过真实 MCP 调查企业资料、加载 Skill、形成 Spec 并实现。"""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from time import perf_counter

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB.parents[1]))
from workshop_runtime.deepseek import DeepSeek


def local_tools():
    definitions = [
        ('read_file', '读取当前工作副本中的文件，包括项目 Skill 及其模板。',
         {'path':{'type':'string'}}, ['path']),
        ('write_file', '在当前工作副本中写入 Spec、应用代码或本地测试。共享 SDK 不能改。',
         {'path':{'type':'string'}, 'content':{'type':'string'}}, ['path','content']),
        ('verify_application', '执行独立业务检查，返回实际结果。先形成 Spec、修改应用再验证。', {}, []),
    ]
    return [{'type':'function', 'function':{'name':name, 'description':description,
            'parameters':{'type':'object','properties':properties,'required':required,
                          'additionalProperties':False}}}
            for name, description, properties, required in definitions]


def workspace_path(workspace, name):
    path = (workspace/name).resolve()
    if not path.is_relative_to(workspace.resolve()):
        raise ValueError('文件必须位于当前工作副本。')
    return path


def execute_local(name, arguments, workspace):
    if name == 'read_file':
        path = workspace_path(workspace, arguments['path'])
        if path.stat().st_size > 200_000:
            raise ValueError('文件过大，请读取与当前任务相关的文件。')
        return path.read_text()
    if name == 'write_file':
        path = workspace_path(workspace, arguments['path'])
        if path.suffix not in {'.py','.md','.json'} or path.relative_to(workspace).parts[0] not in {'src','specs','tests'}:
            raise ValueError('仅写入 src、specs 或 tests 内的 Python、Markdown、JSON 文件。')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(arguments['content'], encoding='utf-8')
        return {'written':str(path.relative_to(workspace)), 'bytes':path.stat().st_size}
    if name == 'verify_application':
        result_path = workspace.parent/'business-check.json'
        # 子进程仅获得运行所需变量，不继承模型或企业 API 凭据。
        environment = {'PATH':os.environ.get('PATH',''), 'PYTHONDONTWRITEBYTECODE':'1',
                       'LANG':'en_US.UTF-8'}
        done = subprocess.run([sys.executable, str(LAB/'checks/check_lab.py'),
            '--app', str(workspace/'src/application.py'), '--out', str(result_path)],
            cwd=workspace, env=environment, capture_output=True, text=True, timeout=30)
        return {'exit_code':done.returncode, 'stdout':done.stdout[-12000:], 'stderr':done.stderr[-4000:]}
    raise ValueError('未知的本地工具。')


async def run(args):
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    out = args.out.resolve()
    if out.exists():
        raise ValueError('输出目录已存在，请选择新目录以保留原运行。')
    if shutil.disk_usage(LAB).free < 432*1024**2:
        raise RuntimeError('可用磁盘不足 432 MiB，停止。')
    client = DeepSeek(args.model)
    workspace = out/'workspace'
    shutil.copytree(LAB/'starter', workspace)
    shutil.copytree(LAB/'.agents', workspace/'.agents')
    shutil.copyfile(LAB/'AGENTS.md', workspace/'AGENTS.md')
    sdk_before = hashlib.sha256((workspace/'shared/wiki_sdk.py').read_bytes()).hexdigest()
    environment = {k:os.environ[k] for k in ('PATH','SYSTEMROOT') if k in os.environ}
    environment.update({f'{name}_BASE_URL':args.base_url for name in ['JIRA','WIKI','GITLAB']})
    environment.update(CONTEXT_FETCH_LOG=str(out/'http-fetch.jsonl'), PYTHONDONTWRITEBYTECODE='1')
    server = StdioServerParameters(command=sys.executable,
                                  args=[str(LAB/'integration/context_mcp.py')], env=environment)
    root_rules = (workspace/'AGENTS.md').read_text()
    skill_path = '.agents/skills/project-change-investigation/SKILL.md'
    # 先只提供目录中的名称和简介；完整 Skill 由模型通过 read_file 按需加载。
    skill = (workspace/skill_path).read_text()
    description = next(line for line in skill.splitlines() if line.startswith('description:'))
    messages = [{'role':'system', 'content':root_rules+'\n当前项目文件有 README.md、src/application.py、'
        'shared/wiki_sdk.py、data/wiki.json。可用 Skill：project-change-investigation；'+description+
        '\n需要时先用 read_file 读取 '+skill_path+'，再读取相对模板。工具名 enterprise_ 开头的是实际 MCP 企业读取。'
        '输出目录已隔离，仅通过给定工具工作。不要读取讲师实现或修改共享 SDK。'},
        {'role':'user','content':(LAB/'harness/model-task.txt').read_text()}]
    started = perf_counter()
    with (out/'events.jsonl').open('w') as log:
        def record(value):
            log.write(json.dumps(value,ensure_ascii=False)+'\n'); log.flush()
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                discovered = (await session.list_tools()).tools
                tools = [{'type':'function', 'function':{'name':'enterprise_'+t.name,
                    'description':t.description or '', 'parameters':t.input_schema}} for t in discovered]
                tools += local_tools()
                (out/'tools.json').write_text(json.dumps(tools,ensure_ascii=False,indent=2))
                completed = False
                for turn in range(args.max_turns):
                    message = await asyncio.to_thread(client.complete, messages, tools=tools,
                                                       thinking=True, max_tokens=12000)
                    # 必须保留 reasoning_content；只重新拼 content/tool_calls 会导致思考模式下一轮报错。
                    messages.append(message.model_dump(exclude_none=True))
                    record({'turn':turn+1, 'assistant':message.model_dump(exclude_none=True)})
                    if not message.tool_calls:
                        (out/'answer.md').write_text(message.content or '')
                        completed = True
                        break
                    for call in message.tool_calls:
                        try:
                            arguments = json.loads(call.function.arguments)
                            name = call.function.name
                            if name.startswith('enterprise_'):
                                result = await session.call_tool(name.removeprefix('enterprise_'), arguments)
                                content = result.model_dump(mode='json', exclude_none=True)
                            else:
                                content = await asyncio.to_thread(execute_local, name, arguments, workspace)
                        except Exception as error:
                            content = {'error':type(error).__name__, 'message':str(error)}
                        record({'tool':call.function.name, 'arguments':arguments, 'result':content})
                        messages.append({'role':'tool','tool_call_id':call.id,
                                         'content':json.dumps(content,ensure_ascii=False)})
                    print(f'已完成模型回合 {turn+1}，工具调用 {len(message.tool_calls)} 次',flush=True)
    # 由宿主再次独立验收，不以模型的完成声明代替。
    verification = execute_local('verify_application', {}, workspace)
    sdk_after = hashlib.sha256((workspace/'shared/wiki_sdk.py').read_bytes()).hexdigest()
    summary = {'model':client.model, 'completed_response':completed,
        'spec_exists':(workspace/'specs/KNOW-201/spec.md').exists(),
        'shared_sdk_unchanged':sdk_before==sdk_after, 'verification':verification,
        'usage':client.usage, 'elapsed_seconds':round(perf_counter()-started,2)}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k not in {'usage','verification'}},ensure_ascii=False))
    return 0 if completed and summary['spec_exists'] and sdk_before==sdk_after and verification['exit_code']==0 else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--base-url',default='http://127.0.0.1:8766')
    parser.add_argument('--model')
    parser.add_argument('--max-turns',type=int,default=24)
    args = parser.parse_args()
    if not 1 <= args.max_turns <= 40:
        parser.error('max-turns 须在 1 到 40 之间。')
    raise SystemExit(asyncio.run(run(args)))
