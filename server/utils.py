from ollama import Tool, Message
from ._types import (
    Function,
    ToolCall,
    ToolResponse
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
    Tool(
        name="generate_random_string",
        description="Generates a random string of characters of a specified length.",
        function=Function(
            name="generate_random_string",
            description="Generates a random string of characters of a specified length.",
            parameters={
                "type": "object",
                "properties": {
                    "length": {
                        "type": "integer",
                        "description": "The length of the random string to generate."
                    }
                },
                "required": ["length"]
            }
        )
    )
]

TOOLS_LOOKUP: dict[str, callable] = {
    "generate_random_string": generate_random_string
}


def handle_tool_calls(message: Message) -> list[ToolResponse]:
    out = []
    
    calls: Sequence[ToolCall] = message.get('tool_calls', [])
    
    for call in calls:
        name = call.function.name
        args = call.function.arguments
        func = TOOLS_LOOKUP.get(name, None)
        if not func: continue
        result = func(**args)
        out.append(ToolResponse(
            role="tool",
            content=str(result),
            name=name
        ))

    return out


