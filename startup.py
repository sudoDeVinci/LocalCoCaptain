from ollama import (
    chat,
    ChatResponse,
    create,
    list as list_models,
    ListResponse,
    ResponseError
)
from typing import Final

MAIN_MODEL: Final[str] = "Jarvis"
MODELFILE: Final[str] = "Modelfile"
MODELFILE_CONTENT: str | None = None

def read_model_file() -> str | None:
    """
    Reads the model file from the specified path.
    """
    try:
        with open(MODELFILE, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Model file {MODELFILE} not found.")
        return None
    
def modelfile_content() -> str | None:
    """
    Reads the model file content.
    """
    global MODELFILE_CONTENT
    if MODELFILE_CONTENT is None:
        MODELFILE_CONTENT = read_model_file()
    return MODELFILE_CONTENT

def init_model() -> tuple[bool, str | None]:
    # List all models
    models: ListResponse = list_models()
    
    # Check if the main model is available
    for model in models['models']:
        if MAIN_MODEL in model['model']:
            return (True, None,)

    try:
        # If the model is not available, create it
        # TODO: Import model filecontent.
        create(model=MAIN_MODEL,
               from_="llama3.2:latest",
            )
    except ResponseError as e:
        # Handle the error if the model creation fails
        return (False, f"Error creating {MAIN_MODEL}:: {e}",)
    
    # Check if the model was created successfully
    models: ListResponse = list_models()
    for model in models['models']:
        if  MAIN_MODEL in model['model']:
            return (True, None,)
        
    # If the model is still not available, return an error
    return (False, f"Error creating {MAIN_MODEL}:: Model not found after creation",)

initres = init_model()