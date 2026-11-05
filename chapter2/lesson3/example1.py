import ollama
import re
import logging
from sympy import sympify

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
    result = facts.get(keyword.lower(), "No relevant information found")
    logger.info(f"Lookup result: {result}")
    return result

def calculate(expression):
    """
    Safely evaluate a mathematical expression.
    """
    logger.info(f"Calculating: {expression}")
    try:
        result = float(sympify(expression))
        logger.info(f"Calculation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Calculation error: {e}")
        return f"Calculation error: {e}"

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
tool_registry.register("calculate", "Perform a mathematical expression calculation", calculate)

# Generate prompt
def generate_prompt(tools):
    tool_descriptions = "\n".join(
    [f"{i+1}. {name}: Function: {desc['description']} Usage format: {name}: <parameter>"
     for i, (name, desc) in enumerate(tools.items())]
    )

    return (
        "You will act as a ReAct agent and solve the user's problem step-by-step, strictly following these steps:\n"
        "Workflow:\n"
        "1. Thought: Describe your thought process regarding the given problem.\n"
        "2. Action: Choose an available tool and perform the action. Only perform one action at a time, and wait for the observation before proceeding.\n"
        "3. Observation: Record the result returned by the tool.\n"
        "4. Answer: Output the final answer once the problem is solved.\n"
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
        "Answer: The mass of the Earth is approximately 81.35 times the mass of the Moon.\n"
        "\nIMPORTANT: Always provide only a single line (Thought or Action or Observation) in response. If no action is required, continue reasoning."
    ).strip()

# Prompt
prompt = generate_prompt(tool_registry.tools)

# Regular expression for extracting action commands
action_re = re.compile(r'^Action:\s*(\w+)\s+(.*)$', re.IGNORECASE | re.MULTILINE)

# ChatBot implementation
class ChatBot:
    def __init__(self, system=""):
        self.messages = [{"role": "system", "content": system}] if system else []

    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        try:
            logger.debug(f"Sending message to model: {message}")
            response = ollama.chat(model="llama3", messages=self.messages)
            content = response['message']['content'].splitlines()[0]  # Ensure only one line of response
            logger.debug(f"Model response: {content}")
            self.messages.append({"role": "assistant", "content": content})
            return content
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return "An error occurred, unable to continue the conversation."

    def trim_messages(self, max_messages=10):
        logger.debug(f"Trimming message history to retain the last {max_messages} messages")
        self.messages = self.messages[-max_messages:]

# Main query function
def query(question, max_turns=5):
    bot = ChatBot(prompt)
    next_prompt = question
    for turn in range(max_turns):
        logger.info(f"---- Turn {turn + 1} ----")
        logger.debug(f"Current prompt: {next_prompt}")
        result = bot(next_prompt)
        logger.info(f"AI response: {result}")

        # Extract action commands
        actions = [action_re.match(line) for line in result.splitlines() if action_re.match(line)]
        logger.debug(f"Action matches found: {actions}")
        if actions:
            # Parse the first valid action command
            action, action_input = actions[0].groups()
            logger.debug(f"Extracted action: {action}, parameter: {action_input}")
            handler = tool_registry.get_handler(action)
            if handler:
                logger.info(f" -- Executing action: {action} with parameter: {action_input}")
                observation = handler(action_input)

                # Integrate observation into context
                observation_message = f"Observation: {observation}"
                logger.info(f"Observation result: {observation_message}")

                # Update next prompt to continue solving the problem based on observation
                next_prompt = f"{result}\n{observation_message}\nThought:"
                bot.trim_messages()

                # Add observation to message history for coherent conversation
                bot.messages.append({"role": "assistant", "content": observation_message})
            else:
                logger.error(f"Unknown action: {action}")
                break
        else:
            # If no action is found, continue reasoning
            next_prompt = f"{result}\nThought:"
            bot.trim_messages()

# Example execution
if __name__ == "__main__":
    question = "Find the values of the speed of light and Planck's constant, and calculate their product."
    query(question)
