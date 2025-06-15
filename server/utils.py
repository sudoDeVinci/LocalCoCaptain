from ollama import Tool, Message
from ._types import (
    Function,
    _Function,
    ToolCall,
    ToolResponse,
    Parameters,
    Property
)
from typing import Sequence

def generate_random_string(length: int) -> str:
    """
    Generates a random string of characters of a specified length.
    Args:
        length (int): The length of the random string to generate.
    
    Returns:
        str: A random string of characters.
    """
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

TOOLS: list[Tool] = [
    {
        'type':"function",
        'function': {
            'name':"generate_random_string",
            'description':"Generates a random string of characters of a specified length.",
            'parameters':{
                'type':"object",
                'required':["length"],
                'properties':{
                    "length": {
                        'type':"int",
                        'description':"The length of the random string to generate."
                    },
                }
            },
        }
    }
]

TOOLS_LOOKUP: dict[str, callable] = {
    "generate_random_string": generate_random_string
}

SYSTEM_PROMPT_TOOLS = (
    "\n\nTOOLS\n\n"
    "You may call one or more functions to assist with the user query.\n"
    "You are provided with function signatures within <tools></tools>:\n"
    f"<tools>\n{TOOLS}\n</tools>\n"
    "For each function call, return a JSON object with function name and arguments "
    "within <json></json> tags with NO other text. "
    "DO NOT include any backticks. "
    "DO NOT use markdown formatting. "
    "DO NOT use ```json or any code block. "
    "Provide ONLY the wrapped JSON object inside <json> tags.\n"
    "Example:\n"
    "<json>\n"
    '{"name": "<function-name>", "arguments": <args-json-object>}\n'
    "</json>\n"
    "You MUST wrap the JSON object in '<json>' '</json>' tags. If you do not, you have failed the task."
)


def handle_tool_calls(message: Message) -> list[ToolResponse]:
    out = []
    
    calls: Sequence[ToolCall] = message.get('tool_calls', [])
    
    for call in calls:
        name = call.function.name
        args = call.function.arguments
        func = TOOLS_LOOKUP.get(name, None)
        if not func: continue
        result = func(**args)
        out.append({
            'role':"tool",
            'content':str(result),
            'name':name
        })

    return out


