"""MCP Server 使用的 nanocode 工具执行器；CLI 不直接调用这些函数。"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import tempfile

def load_nanocode(source):
    source = source.expanduser().resolve()
    if not source.is_file():
        raise ValueError('--nanocode 必须指向独立 checkout 中的 nanocode.py。')
    spec = importlib.util.spec_from_file_location('workshop_nanocode', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



class CodingTools:
    def __init__(self, args):
        self.args = args
        self.workspace = args.workspace.expanduser().resolve()
        self.nanocode = load_nanocode(args.nanocode)
        self.tools = [{'type': 'function', 'function': {
            'name': item['name'], 'description': item['description'],
            'parameters': item['input_schema']}} for item in self.nanocode.make_schema()]
        self.approved = False
        self.active_process = None

    def stop(self):
        process = self.active_process
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def path(self, name):
        if not isinstance(name, str) or not name or Path(name).is_absolute():
            raise ValueError('path 必须是工作区内的相对路径。')
        target = (self.workspace / name).resolve()
        relative = target.relative_to(self.workspace)
        if relative.parts and relative.parts[0] == '.agent':
            raise ValueError('会话状态只通过 MCP Resources 和状态工具访问。')
        return target

    def approve(self):
        if self.args.read_only:
            raise PermissionError('只读模式禁止编辑文件和运行终端命令。')
        if not self.approved:
            raise PermissionError('用户未批准本次操作。')

    def execute(self, name, arguments):
        if not isinstance(arguments, dict):
            raise ValueError('工具参数必须为 JSON 对象。')
        schema = next((item['function']['parameters'] for item in self.tools if item['function']['name'] == name), None)
        if schema is None or set(arguments) - set(schema['properties']) or set(schema['required']) - set(arguments):
            raise ValueError('未知工具、缺少必填参数或存在未定义参数。')
        if name == 'bash':
            command, timeout = arguments['cmd'], self.args.command_timeout
            if not isinstance(command, str) or not command.strip():
                raise ValueError('cmd 必须是非空字符串。')
            self.approve()
            with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
                process = subprocess.Popen(command, shell=True, cwd=self.workspace, stdin=subprocess.DEVNULL,
                                           stdout=stdout, stderr=stderr, start_new_session=True)
                self.active_process = process
                timed_out = False
                try:
                    process.wait(timeout=timeout)
                except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
                    if isinstance(error, KeyboardInterrupt):
                        raise
                    timed_out = True
                self.active_process = None
                stdout.seek(0)
                stderr.seek(0)
                return {'ok': not timed_out and process.returncode == 0, 'exit_code': process.returncode,
                        'timed_out': timed_out, 'stdout': stdout.read().decode('utf-8', errors='replace'),
                        'stderr': stderr.read().decode('utf-8', errors='replace')}
        target = self.path(arguments.get('path', '.'))
        # nanocode 的文件工具只接收已经校验的工作区路径。
        params = dict(arguments, path=str(target))
        if name == 'read':
            offset, limit = params.get('offset', 0), params.get('limit', 200)
            if type(offset) is not int or offset < 0 or type(limit) is not int or limit < 1:
                raise ValueError('offset 为非负行偏移，limit 为正整数。')
            params.update(offset=offset, limit=limit)
        if name == 'glob':
            pattern = params['pat']
            if not isinstance(pattern, str) or Path(pattern).is_absolute() or '..' in Path(pattern).parts:
                raise ValueError('pat 必须是工作区内的相对匹配模式。')
        if name in ('write', 'edit'):
            self.approve()
        result = self.nanocode.run_tool(name, params)
        # 上游通过字符串反馈错误；适配器保留正文并显式标记失败。
        if name in ('glob', 'grep'):
            result = '\n'.join(line.removeprefix(str(self.workspace) + os.sep) for line in result.split('\n'))
        return {'ok': not result.startswith('error:'), 'output': result}
