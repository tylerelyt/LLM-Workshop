"""MCP Harness：Agent Loop 获取上下文、执行工具、写回观察并继续或结束。"""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import DeepSeek


def show_observation(observation):
    """终端按原始换行显示结果；协议和资源中保留结构化数据。"""
    detail = []
    for key in ('ok', 'exit_code', 'timed_out', 'truncated'):
        if key in observation:
            detail.append(f'{key}={observation[key]}')
    print('[观察] ' + ' · '.join(detail), flush=True)
    for key in ('output', 'stdout', 'stderr', 'error', 'preview'):
        if observation.get(key):
            print(f'{key}:\n{observation[key]}', flush=True)
    if observation.get('artifact'):
        print('完整资源：' + observation['artifact'], flush=True)
    displayed = {'ok', 'exit_code', 'timed_out', 'truncated', 'output', 'stdout', 'stderr', 'error', 'preview', 'artifact'}
    extra = {key: value for key, value in observation.items() if key not in displayed}
    if extra:
        print(json.dumps(extra, ensure_ascii=False, indent=2), flush=True)


def show_usage(usage):
    cached = usage.get('prompt_cache_hit_tokens')
    if cached is None:
        cached = (usage.get('prompt_tokens_details') or {}).get('cached_tokens')
    fields = [f'输入={usage.get("prompt_tokens", "未报告")}',
              f'输出={usage.get("completion_tokens", "未报告")}']
    if cached is not None:
        fields.append(f'缓存命中={cached}')
    print('[服务用量] ' + ' · '.join(fields) + ' Token', flush=True)


class CodingAgent:
    def __init__(self, session, args):
        self.session, self.args = session, args
        self.session_id, self.tools, self.backend = '', [], None

    async def call(self, name, arguments):
        result = await self.session.call_tool(name, arguments, read_timeout_seconds=self.args.command_timeout + 20)
        if result.is_error:
            raise RuntimeError('\n'.join(c.text for c in result.content if c.type == 'text'))
        if result.structured_content is not None:
            return result.structured_content
        return json.loads(next(c.text for c in result.content if c.type == 'text'))

    async def event(self, operation, payload, version=None):
        return await self.call('session_event', {'session_id': self.session_id,
                         'operation': operation, 'payload': payload, 'expected_version': version})

    async def open(self, resume=False):
        result = await self.event('open', {'resume': resume})
        self.session_id = result['session_id']
        discovered = await self.session.list_tools()
        # 路由和批准信息由 Harness 填充，不允许模型选择其他会话或自授权限。
        for tool in discovered.tools:
            if tool.name == 'session_event':
                continue
            schema = deepcopy(tool.input_schema)
            for name in ('session_id', 'call_id', 'approved'):
                schema.get('properties', {}).pop(name, None)
            schema['required'] = [name for name in schema.get('required', []) if name not in ('session_id', 'call_id', 'approved')]
            self.tools.append({'type': 'function', 'function': {
                'name': tool.name, 'description': tool.description, 'parameters': schema}})

    async def capabilities(self):
        tools = await self.session.list_tools()
        prompts = await self.session.list_prompts()
        resources = await self.session.list_resources()
        templates = await self.session.list_resource_templates()
        return {
            'tools': [tool.model_dump(mode='json', by_alias=True, exclude_none=True) for tool in tools.tools],
            'prompts': [prompt.model_dump(mode='json', by_alias=True, exclude_none=True) for prompt in prompts.prompts],
            'resources': [resource.model_dump(mode='json', by_alias=True, exclude_none=True) for resource in resources.resources],
            'resourceTemplates': [template.model_dump(mode='json', by_alias=True, exclude_none=True) for template in templates.resource_templates],
        }

    async def resource(self, part):
        result = await self.session.read_resource(f'context://sessions/{self.session_id}/{part}')
        return json.loads(result.contents[0].text)

    async def context(self, mode='task'):
        result = await self.session.get_prompt('coding_context', {'session_id': self.session_id, 'mode': mode})
        # MCP Prompt 的 resource 消息里是服务端组好的原生模型消息快照。
        # Prompt 本身没有 system/tool 角色；这里做显式协议转换，不将其冒充 PromptMessage。
        resource = next(message.content.resource for message in result.messages if message.content.type == 'resource')
        packet = json.loads(resource.text)
        if self.args.show_context:
            print(json.dumps(packet, ensure_ascii=False, indent=2), flush=True)
        return packet

    def approve(self, name, arguments):
        if name not in ('write', 'edit', 'bash') or self.args.read_only:
            return False
        print(f'[批准请求] {name} {json.dumps(arguments, ensure_ascii=False)}', flush=True)
        if self.args.yes:
            return True
        try:
            return input('允许执行？[y/N] ').strip().lower() == 'y'
        except EOFError:
            return False

    async def pending(self):
        status = await self.resource('status')
        interrupted = False
        for call in status['pending']:
            name = call['function']['name']
            print(f'[MCP 工具] {name} {call["function"]["arguments"]}', flush=True)
            try:
                arguments = json.loads(call['function']['arguments'])
                if not isinstance(arguments, dict) or name not in {t['function']['name'] for t in self.tools}:
                    raise ValueError('未知工具或参数不是 JSON 对象。')
                if interrupted:
                    raise RuntimeError('本轮已中断，未执行该工具。')
                approved = self.approve(name, arguments)
                arguments = {**arguments, 'session_id': self.session_id, 'call_id': call['id']}
                if name in ('write', 'edit', 'bash'):
                    arguments['approved'] = approved
                observation = await self.call(name, arguments)
            except KeyboardInterrupt:
                interrupted = True
                observation = await self.event('tool_error', {'call_id': call['id'], 'error': '用户中断，未执行本次调用。'})
            except Exception as error:
                observation = await self.event('tool_error', {'call_id': call['id'], 'error': str(error)})
            show_observation(observation)
        return not interrupted

    async def complete(self, messages, tools=None, max_tokens=4096):
        if self.backend is None:
            self.backend = DeepSeek()
            print(f'[Model] {self.backend.model}：根据当前消息和工具定义生成下一步。', flush=True)
        return await asyncio.to_thread(self.backend.complete, messages, tools=tools, thinking=False, max_tokens=max_tokens)

    async def turn(self, task=None):
        if not await self.pending():
            return 130
        if task:
            await self.event('begin', {'task': task})
        elif not (await self.resource('task'))['task']:
            raise ValueError('当前会话没有任务，请先输入任务。')
        for step in range(self.args.max_steps):
            packet = await self.context()
            print(f'\n[模型 {step + 1}/{self.args.max_steps}] 资源版本={packet["version"]}', flush=True)
            reply = await self.complete(packet['messages'], self.tools)
            await self.event('assistant', {'message': reply.model_dump(exclude_none=True)}, packet['version'])
            if reply.content:
                print('\n' + reply.content, flush=True)
            if self.backend.usage:
                show_usage(self.backend.usage[-1])
            if not reply.tool_calls:
                return 0
            if not await self.pending():
                return 130
        await self.event('budget', {})
        print('达到调用预算，任务尚未完成。输入 /continue 或重启后恢复。')
        return 2

    async def compact(self):
        packet = await self.context('compact')
        summary = (await self.complete(packet['messages'], max_tokens=2048)).content
        await self.event('compact', {'summary': summary}, packet['version'])
        print('摘要已写入 memory Resource；完整 history 和 observations 保留。')

    async def interact(self):
        print(f'MCP Harness · {self.args.workspace}\n/new /continue /compact /status /context /mcp /resources /resource 名称 /plan 文本 /remember 文本 /exit')
        while True:
            try:
                task = input('\nyou> ').strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            try:
                if task == '/exit':
                    return 0
                if task == '/new':
                    self.tools = []
                    await self.open()
                    print('已创建新资源会话，代码文件保留。')
                elif task == '/continue':
                    await self.turn()
                elif task == '/compact':
                    await self.compact()
                elif task == '/status':
                    print(json.dumps(await self.resource('status'), ensure_ascii=False, indent=2))
                elif task == '/context':
                    print(json.dumps(await self.context(), ensure_ascii=False, indent=2))
                elif task == '/mcp':
                    print(json.dumps(await self.capabilities(), ensure_ascii=False, indent=2))
                elif task.startswith('/resource '):
                    print(json.dumps(await self.resource(task[10:].strip()), ensure_ascii=False, indent=2))
                elif task == '/resources':
                    print('\n'.join(f'context://sessions/{self.session_id}/{part}' for part in ('task', 'plan', 'history', 'observations', 'memory', 'rules', 'policy', 'status', 'snapshot')))
                elif task.startswith('/plan '):
                    await self.event('set', {'plan': task[6:]})
                elif task.startswith('/remember '):
                    await self.event('set', {'memory': task[10:]})
                elif task.startswith('/'):
                    print('未知命令。')
                elif task:
                    await self.turn(task)
            except Exception as error:
                print(f'本次操作失败：{error}', file=sys.stderr)


async def run(args):
    parameters = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name('context_server.py')),
        '--nanocode', str(args.nanocode.resolve()), '--workspace', str(args.workspace.resolve()),
        '--max-output', str(args.max_output), '--command-timeout', str(args.command_timeout),
        *[flag for flag, enabled in (('--read-only', args.read_only), ('--no-recite', args.no_recite), ('--hide-errors', args.hide_errors)) if enabled]])
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            agent = CodingAgent(session, args)
            await agent.open(args.resume)
            if args.list_capabilities:
                print(json.dumps(await agent.capabilities(), ensure_ascii=False, indent=2))
                return 0
            if args.read_resource:
                print(json.dumps(await agent.resource(args.read_resource), ensure_ascii=False, indent=2))
                return 0
            if args.inspect:
                print(json.dumps(await agent.context(), ensure_ascii=False, indent=2))
                return 0
            print(f'[Harness] 最大轮次={args.max_steps} · 只读={args.read_only} · 自动批准={args.yes}', flush=True)
            if args.task:
                return await agent.turn(args.task)
            return await agent.interact()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task', nargs='?')
    parser.add_argument('--nanocode', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--list-capabilities', action='store_true', help='通过 MCP 发现 Tools、Prompts 和 Resources，无需模型密钥')
    parser.add_argument('--read-resource', help='通过 resources/read 读取当前会话的资源，如 plan、memory')
    parser.add_argument('--inspect', action='store_true', help='只获取 MCP Prompt 和资源快照，无需模型密钥')
    parser.add_argument('--yes', action='store_true')
    parser.add_argument('--read-only', action='store_true')
    parser.add_argument('--no-recite', action='store_true')
    parser.add_argument('--hide-errors', action='store_true')
    parser.add_argument('--show-context', action='store_true')
    parser.add_argument('--max-steps', type=int, default=20)
    parser.add_argument('--max-output', type=int, default=6000)
    parser.add_argument('--command-timeout', type=int, choices=range(1, 121), default=30, metavar='1-120')
    args = parser.parse_args()
    if args.max_steps < 1 or args.max_output < 200 or not args.workspace.is_dir() or not args.nanocode.is_file():
        parser.error('检查工作区、nanocode.py 路径、max-steps 和 max-output。')
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
