"""
MCP Tools: discovery, execution and agent loop

Demonstrates how an LLM agent uses the Model Context Protocol (MCP) to
discover and invoke external tools through a standardized harness.

Architecture:
  User task
      │
      ▼
  McpHarness
      ├── launches tools_server.py as a subprocess (stdio transport)
      ├── discovers available tools via MCP list_tools()
      ├── converts tool schemas to OpenAI function-calling format
      └── runs the ReAct loop:
              LLM  ──tool_call──▶  MCP server  ──result──▶  LLM
              LLM  ──final answer──▶  AgentTrace

Usage:
    # List tools exposed by the MCP server
    python mcp_harness.py list-tools

    # Run a single task
    python mcp_harness.py run --task "What is sqrt(2) * 100, rounded to 2 decimal places?"

    # Run all tasks in the default tasks file
    python mcp_harness.py run --tasks-file data/tasks.json

    # Run and save a JSON report
    python mcp_harness.py run --tasks-file data/tasks.json --output-dir results/
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import openai
import typer
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

app = typer.Typer(add_completion=False, no_args_is_help=True)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from workshop_runtime.deepseek import DeepSeek, model_name

# Path to the MCP tool server, relative to this file
_DEFAULT_SERVER = str(Path(__file__).parent / "tools_server.py")


# ─── Data structures ──────────────────────────────────────────────────────────


@dataclass
class ToolCall:
    """One tool invocation inside an agent trajectory."""

    tool: str
    arguments: dict
    result: str
    latency_ms: float


@dataclass
class AgentTrace:
    """Full trace for a single task execution."""

    task: str
    model: str
    answer: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    total_latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


# ─── Harness ──────────────────────────────────────────────────────────────────


class McpHarness:
    """
    Agent harness that wires an LLM to an MCP tool server.

    Responsibilities:
      1. Launch the MCP server process and establish a ClientSession.
      2. Discover available tools and convert schemas to OpenAI format.
      3. Run the ReAct agent loop until the LLM stops requesting tools.
      4. Return a structured AgentTrace for logging and evaluation.
    """

    def __init__(
        self,
        server_script: str = _DEFAULT_SERVER,
        model: str | None = None,
        max_turns: int = 10,
    ):
        self.server_script = server_script
        self.backend = None
        self.model = model
        self.max_turns = max_turns

    # ── MCP helpers ───────────────────────────────────────────────────────────

    def _server_params(self) -> StdioServerParameters:
        return StdioServerParameters(
            command=sys.executable,
            args=[self.server_script],
        )

    @staticmethod
    def _to_openai_tools(mcp_tools) -> list[dict]:
        """Convert MCP tool descriptors to OpenAI function-calling format."""
        result = []
        for tool in mcp_tools:
            schema = tool.input_schema or {"type": "object", "properties": {}}
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": schema,
                    },
                }
            )
        return result

    async def list_tools_async(self) -> list[dict]:
        """Return tool descriptors from the MCP server (for CLI display)."""
        async with stdio_client(self._server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return [
                    {
                        "name": t.name,
                        "description": t.description,
                        "schema": t.input_schema,
                    }
                    for t in tools_result.tools
                ]

    # ── Agent loop ────────────────────────────────────────────────────────────

    async def run_task_async(self, task: str) -> AgentTrace:
        """Execute one task through the full MCP + LLM agent loop."""
        trace = AgentTrace(task=task, model=self.model or "未配置", answer="")
        wall_start = time.perf_counter()

        try:
            if self.backend is None:
                self.backend = DeepSeek(self.model)
            self.model = self.backend.model
            trace.model = self.model
            async with stdio_client(self._server_params()) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    tools_result = await session.list_tools()
                    openai_tools = self._to_openai_tools(tools_result.tools)

                    messages: list[dict] = [{"role": "user", "content": task}]

                    for turn in range(self.max_turns):
                        msg = await asyncio.to_thread(self.backend.complete, messages,
                                                      tools=openai_tools, thinking=True)

                        # ── No tool calls → final answer ──────────────────
                        if not msg.tool_calls:
                            trace.answer = msg.content or ""
                            break

                        # ── Tool calls → dispatch via MCP ─────────────────
                        # Append the assistant turn (with tool_calls) to history
                        # DeepSeek 思考模式的工具回合必须回传 reasoning_content。
                        messages.append(msg.model_dump(exclude_none=True))

                        for tc in msg.tool_calls:
                            tool_name = tc.function.name
                            try:
                                tool_args = json.loads(tc.function.arguments)
                            except json.JSONDecodeError:
                                tool_args = {}

                            t0 = time.perf_counter()
                            mcp_result = await session.call_tool(tool_name, tool_args)
                            latency_ms = (time.perf_counter() - t0) * 1000

                            result_text = (
                                mcp_result.content[0].text
                                if mcp_result.content
                                else ""
                            )

                            trace.tool_calls.append(
                                ToolCall(
                                    tool=tool_name,
                                    arguments=tool_args,
                                    result=result_text,
                                    latency_ms=round(latency_ms, 1),
                                )
                            )

                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tc.id,
                                    "content": result_text,
                                }
                            )
                    else:
                        # max_turns exhausted without a final answer
                        trace.answer = messages[-1].get("content", "")
                        trace.error = f"Reached max_turns={self.max_turns} without final answer"
                        trace.success = False

        except Exception as exc:
            trace.success = False
            trace.error = str(exc)

        trace.total_latency_ms = round((time.perf_counter() - wall_start) * 1000, 1)
        return trace

    def run_task(self, task: str) -> AgentTrace:
        """Synchronous wrapper around run_task_async."""
        return asyncio.run(self.run_task_async(task))


# ─── Reporting ────────────────────────────────────────────────────────────────


def print_trace(trace: AgentTrace) -> None:
    """Print a human-readable summary of an AgentTrace."""
    bar = "─" * 64
    print(f"\n{bar}")
    print(f"  Task   : {trace.task}")
    print(f"  Model  : {trace.model}")
    if trace.tool_calls:
        print(f"  Tools  : {len(trace.tool_calls)} call(s)")
        for i, tc in enumerate(trace.tool_calls, 1):
            print(f"    [{i}] {tc.tool}({tc.arguments})  →  {tc.result}  ({tc.latency_ms} ms)")
    else:
        print("  Tools  : none")
    print(f"  Answer : {trace.answer}")
    print(f"  Time   : {trace.total_latency_ms} ms")
    if trace.error:
        print(f"  Error  : {trace.error}")
    print(bar)


def save_report(traces: list[AgentTrace], output_dir: str) -> None:
    """Serialize all traces to a JSON file in output_dir."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(output_dir) / "mcp_harness_report.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in traces], f, ensure_ascii=False, indent=2)
    print(f"\n[Harness] Report saved → {out_path}")


# ─── CLI ──────────────────────────────────────────────────────────────────────


@app.command("list-tools")
def cmd_list_tools(
    server_script: str = typer.Option(_DEFAULT_SERVER, help="Path to MCP tools server"),
):
    """List all tools exposed by the MCP server."""
    harness = McpHarness(server_script=server_script)
    tools = asyncio.run(harness.list_tools_async())
    print(f"\n{len(tools)} tool(s) available from: {server_script}\n")
    for t in tools:
        print(f"  {t['name']}")
        print(f"    {t['description']}")
        props = (t.get("schema") or {}).get("properties", {})
        if props:
            for param, meta in props.items():
                ptype = meta.get("type", "any")
                pdesc = meta.get("description", "")
                print(f"    • {param} ({ptype}){': ' + pdesc if pdesc else ''}")
        print()


@app.command("run")
def cmd_run(
    task: Optional[str] = typer.Option(None, help="Single task string to execute"),
    tasks_file: Optional[str] = typer.Option(
        None, help="JSON file with a list of task strings"
    ),
    model: str = typer.Option(None, help="覆盖环境配置中的模型名"),
    server_script: str = typer.Option(_DEFAULT_SERVER, help="Path to MCP tools server"),
    output_dir: Optional[str] = typer.Option(None, help="Directory to save JSON report"),
    max_turns: int = typer.Option(10, help="Maximum agent turns per task"),
):
    """
    Run one or more tasks through the MCP agent harness.

    Provide either --task for a single run or --tasks-file for batch execution.
    """
    if not task and not tasks_file:
        typer.echo("Error: provide --task or --tasks-file.", err=True)
        raise typer.Exit(code=1)

    tasks: list[str] = []
    if task:
        tasks.append(task)
    if tasks_file:
        path = Path(tasks_file)
        if not path.exists():
            typer.echo(f"Error: tasks file not found: {tasks_file}", err=True)
            raise typer.Exit(code=1)
        with path.open(encoding="utf-8") as f:
            tasks.extend(json.load(f))

    harness = McpHarness(server_script=server_script, model=model, max_turns=max_turns)
    traces: list[AgentTrace] = []

    for i, t in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] {t}")
        trace = harness.run_task(t)
        print_trace(trace)
        traces.append(trace)

    if output_dir:
        save_report(traces, output_dir)
    if not all(trace.success for trace in traces):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
