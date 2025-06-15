from ollama import (
    chat,
    ChatResponse,
    Message,
    create,
    list as list_models,
    ListResponse,
    ResponseError
)
from ._types import (
    Modelfile
)

from typing import Iterator
from logging import getLogger, Logger

from json import load


MODELFILE: Modelfile | None = None
"""
The model file content loaded from the config file.
This is initialized to None and will be populated by
the `read_config_file` function.
"""

LOGGER: Logger = getLogger(__name__)
"""
Global logger for the application.
Set to log at the INFO level by default (convenience).
"""
LOGGER.setLevel('INFO')


def read_config_file(params: str = "2b") -> Modelfile | None:
    """
    Reads the config file and returns the content as a dictionary.

    Args:
        params (str): The key to access the specific model configuration in the config file.
                      This corresponds to billions of parameters for the model. Defaults to "2b".

    Returns:
        Modelfile | None: The content of the config file as a dictionary, or None if the file does not exist.
    """
    global MODELFILE
    if MODELFILE is None:
        try:
            with open("config.json", "r") as f:
                MODELFILE = load(f).get(params, None)
                
        except ValueError as err:
            return None
    return MODELFILE


def modelfile_str() -> str | None:
    """
    Converts the model file content to a string.

    Returns:
        str | None: The model file content as a string, or None if the model file is not available.
    """
    if MODELFILE is None:
        return None
    
    # Grab just the model type
    modeltype = MODELFILE['model'].split(':')[0]

    return (
        f"FROM {modeltype}"
        "PARAMETER stop \"<|eot|>\"\n"
        "PARAMETER stop \"</answer>\"\n"
        f"PARAMETER top_p {MODELFILE['top_p']}\n"
        f"PARAMETER presence_penalty {MODELFILE['presence_penalty']}\n"
        f"PARAMETER frequency_penalty {MODELFILE['frequency_penalty']}\n"
        f"PARAMETER context_length {MODELFILE['context_length']}\n"
        f"PARAMETER temperature {MODELFILE['temperature']}\n"
        f"SYSTEM \"\"\"\n{MODELFILE['system']}\n\"\"\"\n"
    )


def init_model() -> tuple[bool, str | None]:
    """
    Initializes the model by checking if it exists and creating it if not.
    Returns:
        tuple[bool, str | None]: A tuple containing a boolean indicating success or failure,
                                 and an error message if applicable.
    """
    # List all models
    models: ListResponse = list_models()
    
    # Check if the main model is available
    for model in models['models']:
        if MODELFILE['name'] in model['model']:
            return (True, None,)

    try:
        # If the model is not available, create it
        # TODO: Import model filecontent.
        print(f">> {MODELFILE['name']} not found. Creating from config...")
        create(model=MODELFILE['name'],
               from_=MODELFILE['model'],
               system=MODELFILE['system'],
               parameters={
                     "top_p": MODELFILE['top_p'],
                     "top_k": MODELFILE['top_k'],
                     "description": MODELFILE['description'],
                     "presence_penalty": MODELFILE['presence_penalty'],
                     "frequency_penalty": MODELFILE['frequency_penalty'],
                     "context_length": MODELFILE['context_length'],
                     "temperature": MODELFILE['temperature'],
               },
            )
        print(f">> {MODELFILE['name']} created.")
    except ResponseError as e:
        # Handle the error if the model creation fails
        return (False, f"Error creating {MODELFILE['name']}:: {e}",)
    
    # Check if the model was created successfully
    models = list_models()
    for model in models['models']:
        if MODELFILE['name'] in model['model']:
            return (True, None,)
        
    # If the model is still not available, return an error
    return (False, f"Error creating {MODELFILE['name']}:: Model not found after creation",)
