from typing import TypedDict, Any, Mapping, Optional, Sequence, Literal, Union

from pydantic import ConfigDict, Field

from ollama._types import SubscriptableBaseModel


class Modelfile(TypedDict):
    """
    A singular Model file for a give model.

    Attributes:
        model (str): The model identifier.
        name (str): The name of the model.
        description (str): A description of the model.
        temperature (float): The temperature setting for the model.
        top_p (float): The top-p setting for the model.
        presence_penalty (float): The presence penalty for the model.
        frequency_penalty (float): The frequency penalty for the model.
        context_length (int): The context length for the model.
        system (str): The system prompt for the model.
    """

    model: str
    name: str
    description: str
    temperature: float
    top_p: float
    presence_penalty: float
    frequency_penalty: float
    context_length: int
    system: str


class _Function(SubscriptableBaseModel):
    name: Optional[str] = None
    arguments: Mapping[str, Any]


class ToolCall(SubscriptableBaseModel):
    """
    Model tool calls.
    This uses the "arguments" field of the
    Function, NOT "parameters".
    """

    function: _Function


class ToolResponse(TypedDict):
    """
    Tool function call response to model

    Attributes:
        role (str): The role of the message (e.g., "tool").
        content (str | None): The content of the message, if any.
        name (str | None): The name of the tool being called, if applicable.
    """

    role: str
    content: str | None
    name: str | None
