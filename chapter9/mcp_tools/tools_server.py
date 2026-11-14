"""
Chapter 9 Lesson 1: MCP Tools Server

A self-contained MCP server that exposes three practical tools via the
Model Context Protocol (stdio transport).  The harness (mcp_harness.py)
launches this file as a subprocess and communicates with it over stdin/stdout
using the MCP JSON-RPC protocol.

Tools exposed:
  calculator       – evaluate safe arithmetic expressions
  unit_converter   – convert between common measurement units
  get_datetime     – return the current local date and time

Run standalone for smoke-testing (FastMCP will serve over stdio by default):
    python tools_server.py
"""

import ast
import datetime
import math
import operator as _op

from mcp.server import MCPServer

mcp = MCPServer("workshop-tools")

# ─── Tool: calculator ─────────────────────────────────────────────────────────

# Allowed AST node types for safe expression evaluation
_SAFE_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
    ast.Mod, ast.Pow, ast.UAdd, ast.USub,
    ast.Call, ast.Name, ast.Load,
)

_SAFE_NAMES = {
    "abs": abs, "round": round,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e,
}


def _safe_eval(expr: str) -> float:
    """Evaluate an arithmetic expression without using eval() on arbitrary code."""
    tree = ast.parse(expr.strip(), mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _SAFE_NODES):
            raise ValueError(f"Disallowed expression node: {type(node).__name__}")
    return _eval_node(tree.body)


def _eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        ops = {
            ast.Add: _op.add, ast.Sub: _op.sub,
            ast.Mult: _op.mul, ast.Div: _op.truediv,
            ast.FloorDiv: _op.floordiv, ast.Mod: _op.mod,
            ast.Pow: _op.pow,
        }
        fn = ops.get(type(node.op))
        if fn is None:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        return fn(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return -_eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +_eval_node(node.operand)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed")
        fn = _SAFE_NAMES.get(node.func.id)
        if fn is None:
            raise ValueError(f"Unknown function: {node.func.id}")
        args = [_eval_node(a) for a in node.args]
        return fn(*args)
    if isinstance(node, ast.Name):
        val = _SAFE_NAMES.get(node.id)
        if val is None:
            raise ValueError(f"Unknown name: {node.id}")
        return val
    raise ValueError(f"Unsupported node type: {type(node).__name__}")


@mcp.tool()
def calculator(expression: str) -> str:
    """
    Evaluate a safe arithmetic expression and return the numeric result.

    Supports: +, -, *, /, //, %, ** and math functions
    (sqrt, log, log10, sin, cos, tan, abs, round) plus constants pi and e.

    Examples:
        "2 ** 10 - 1"       → "1023.0"
        "sqrt(144)"         → "12.0"
        "round(3.14159, 2)" → "3.14"
    """
    try:
        result = _safe_eval(expression)
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


# ─── Tool: unit_converter ─────────────────────────────────────────────────────

# Conversion factors relative to a base SI unit
_CONVERSIONS: dict[str, dict[str, float]] = {
    "length": {
        "meter": 1.0, "km": 1000.0, "mile": 1609.344,
        "yard": 0.9144, "foot": 0.3048, "inch": 0.0254, "cm": 0.01,
    },
    "weight": {
        "kg": 1.0, "gram": 0.001, "pound": 0.453592,
        "ounce": 0.0283495, "ton": 1000.0,
    },
    "temperature": {
        # Special-cased below
        "celsius": None, "fahrenheit": None, "kelvin": None,
    },
    "speed": {
        "m/s": 1.0, "km/h": 1.0 / 3.6, "mph": 0.44704, "knot": 0.514444,
    },
}

_ALL_UNITS: dict[str, str] = {}  # unit_name → category
for _cat, _units in _CONVERSIONS.items():
    for _u in _units:
        _ALL_UNITS[_u] = _cat


def _convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    # Normalize to Celsius first
    if from_unit == "fahrenheit":
        celsius = (value - 32) * 5 / 9
    elif from_unit == "kelvin":
        celsius = value - 273.15
    else:
        celsius = value
    # Convert from Celsius to target
    if to_unit == "fahrenheit":
        return celsius * 9 / 5 + 32
    if to_unit == "kelvin":
        return celsius + 273.15
    return celsius


@mcp.tool()
def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """
    Convert a numeric value between units of the same category.

    Supported categories and units:
      length      : meter, km, mile, yard, foot, inch, cm
      weight      : kg, gram, pound, ounce, ton
      temperature : celsius, fahrenheit, kelvin
      speed       : m/s, km/h, mph, knot

    Examples:
        value=100, from_unit="mile", to_unit="km"
        value=100, from_unit="celsius", to_unit="fahrenheit"
    """
    fu = from_unit.lower().strip()
    tu = to_unit.lower().strip()

    if fu not in _ALL_UNITS:
        return f"Error: unknown unit '{from_unit}'. Known units: {sorted(_ALL_UNITS)}"
    if tu not in _ALL_UNITS:
        return f"Error: unknown unit '{to_unit}'. Known units: {sorted(_ALL_UNITS)}"
    if _ALL_UNITS[fu] != _ALL_UNITS[tu]:
        return (
            f"Error: cannot convert between '{from_unit}' ({_ALL_UNITS[fu]}) "
            f"and '{to_unit}' ({_ALL_UNITS[tu]})"
        )

    category = _ALL_UNITS[fu]
    if category == "temperature":
        result = _convert_temperature(value, fu, tu)
    else:
        base_value = value * _CONVERSIONS[category][fu]
        result = base_value / _CONVERSIONS[category][tu]

    return f"{round(result, 6)} {to_unit}"


# ─── Tool: get_datetime ───────────────────────────────────────────────────────


@mcp.tool()
def get_datetime() -> str:
    """
    Return the current local date and time in ISO 8601 format.

    Example output: "2026-06-21T21:30:00"
    """
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Default transport is stdio, suitable for subprocess-based harness launch
    mcp.run()
