from typing import TypedDict

class Modelfile(TypedDict):
    model: str
    name: str
    description: str
    temperature: float
    top_p: float
    presence_penalty: float
    frequency_penalty: float
    context_length: int
    system: str