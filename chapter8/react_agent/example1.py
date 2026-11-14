
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import ast
import argparse
import logging
import math
import operator
import re

from workshop_runtime.chat import chat

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tool implementation
def lookup_fact(keyword):
    """
    Retrieve a predefined fact based on a keyword.
    """
    logger.info(f"Looking up fact: {keyword}")
    facts = {
        "speed of light": "The speed of light is approximately 299,792,458 meters per second.",
        "planck's constant": "Planck's constant is approximately 6.62607015 × 10^-34 Js.",
        "mass of earth": "The mass of the Earth is approximately 5.972 × 10^24 kg.",
        "mass of moon": "The mass of the Moon is approximately 7.342 × 10^22 kg."
    }
    result = facts.get(keyword.strip().strip("'\"").lower(), "No relevant information found")
    logger.info(f"Lookup result: {result}")
    return result

_BINARY_OPERATIONS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _arithmetic_value(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _arithmetic_value(node.operand)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATIONS:
        operation = _BINARY_OPERATIONS[type(node.op)]
        return operation(_arithmetic_value(node.left), _arithmetic_value(node.right))
    raise ValueError("Use numbers, parentheses, and +, -, *, or /.")


def calculate(expression):
    """Calculate basic arithmetic without executing model output as Python."""
    expression = expression.strip().strip("`")
    if len(expression) > 200:
        return "Calculation error: the expression is too long."
    try:
        result = _arithmetic_value(ast.parse(expression, mode="eval").body)
        if not math.isfinite(result):
            raise ValueError("The result must be finite.")
    except (ArithmeticError, SyntaxError, ValueError) as error:
        return f"Calculation error: {error}"
    return result

# Tool registry
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name, description, handler):
        logger.debug(f"Registering tool: {name}, Description: {description}")
        self.tools[name] = {"description": description, "handler": handler}

    def get_handler(self, name):
        handler = self.tools.get(name, {}).get("handler")
        if handler:
            logger.debug(f"Found handler for tool: {name}")
        else:
            logger.warning(f"Handler for tool not found: {name}")
        return handler

# Initialize tool registry
tool_registry = ToolRegistry()
tool_registry.register("lookup_fact", "Retrieve a predefined fact about a keyword (Valid keys: speed of light, planck's constant, mass of earth, mass of moon)", lookup_fact)
tool_registry.register("calculate", "Calculate using +, -, *, /, parentheses and scientific notation such as 1e-3", calculate)

# Generate prompt
def generate_prompt(tools):
    tool_descriptions = "\n".join(
    [f"{i+1}. {name}: {desc['description']} Usage: Action: {name} <parameter>"
     for i, (name, desc) in enumerate(tools.items())]
    )

    return (
        "Solve the problem using the registered ReAct tools. You may briefly name your next step on a Thought: line.\n"
        "Send one Action: line and wait for the host to supply the Observation. Never supply an Observation yourself.\n"
        "When you have the needed tool results, start your full final response with Answer:.\n"
        "Available tools:\n"
        f"{tool_descriptions}\n"
        "Example dialogue:\n"
        "Question: Find the mass of the Earth and the Moon, and calculate their mass ratio.\n"
        "Thought: I need to look up the mass of the Earth and the Moon.\n"
        "Action: lookup_fact mass of earth\n"
        "Observation: The mass of the Earth is approximately 5.972 × 10^24 kg.\n"
        "Thought: Next, I need to look up the mass of the Moon.\n"
        "Action: lookup_fact mass of moon\n"
        "Observation: The mass of the Moon is approximately 7.342 × 10^22 kg.\n"
        "Thought: Now that I have the masses of the Earth and the Moon, I can calculate their mass ratio.\n"
        "Action: calculate 5.972e24 / 7.342e22\n"
        "Observation: The result is 81.35215091343292.\n"
        "Answer: The mass of the Earth is approximately 81.35 times the mass of the Moon."
    ).strip()

# Prompt
prompt = generate_prompt(tool_registry.tools)

# Regular expression for extracting action commands
action_re = re.compile(r'^Action:[ \t]*(\w+)[ \t]+(.+)$', re.IGNORECASE | re.MULTILINE)
answer_re = re.compile(r'^(?:Final )?Answer:[ \t]*', re.IGNORECASE | re.MULTILINE)

# ChatBot implementation
class ChatBot:
    def __init__(self, system=""):
        self.messages = [{"role": "system", "content": system}] if system else []

    def __call__(self):
        response = chat(messages=self.messages)
        return response.strip()

# Main query function
def query(question, max_turns=8):
    bot = ChatBot(prompt)
    bot.messages.append({"role": "user", "content": question})
    for turn in range(max_turns):
        logger.info("Turn %s", turn + 1)
        result = bot()
        action_match = action_re.search(result)
        answer_match = answer_re.search(result)
        if action_match and (not answer_match or action_match.start() < answer_match.start()):
            action, action_input = action_match.groups()
            action_line = f"Action: {action} {action_input}"
            logger.info(action_line)
            handler = tool_registry.get_handler(action.lower())
            observation = handler(action_input) if handler else f"Unknown tool: {action}"
            observation_message = f"Observation: {observation}"
            logger.info(observation_message)
            bot.messages.append({"role": "assistant", "content": action_line})
            bot.messages.append({"role": "user", "content": observation_message})
        elif answer_match and (answer := result[answer_match.end():].strip()):
            return answer
        else:
            logger.info("The model returned neither an action nor a complete answer. Asking again.")
            bot.messages.append({"role": "assistant", "content": result})
            bot.messages.append({"role": "user", "content": "Continue with Action: or a complete Answer:."})
    raise RuntimeError(f"No final answer after {max_turns} turns.")

# Example execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="观察真实查表、计算与模型答案之间的反馈循环。")
    parser.add_argument("--max-turns", type=int, choices=range(1, 21), default=8, metavar="1-20")
    parser.add_argument("--question", default="Find the values of the speed of light and Planck's constant, and calculate their product.")
    args = parser.parse_args()
    question = args.question
    print(f"Question: {question}", flush=True)
    try:
        print(f"Answer: {query(question, max_turns=args.max_turns)}")
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
