from ollama import (
    chat,
    ChatResponse,
    Message,
    create,
    list as list_models,
    ListResponse,
    ResponseError
)
from _types import (
    Modelfile
)

from json import load

MODELFILE: Modelfile | None = None


def read_config_file() -> Modelfile | None:
    """
    Reads the config file and returns the content as a dictionary.

    Returns:
        Modelfile | None: The content of the config file as a dictionary, or None if the file does not exist.
    """
    global MODELFILE
    if MODELFILE is None:
        try:
            with open("config.json", "r") as f:
                MODELFILE = load(f)
        except FileNotFoundError:
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

read_config_file()


# Attempt to init the model
yn, err = init_model()
if not yn:
    print(f">> {err}")
    exit(0)
else:
    print(f">> {MODELFILE['name']} is ready to use.")


if __name__ == "__main__":
    messages = [Message(
            role="user",
            content="Hey Jarvis, how you doing today?"
        )
    ]

    initialresponse = chat(model=MODELFILE['name'],
                        messages=messages,
                            stream=True
                        )

    print(f">> USER: {messages[0]['content']}\n")
    print(">> JARVIS: ", end="", flush=True)
    for chunk in initialresponse:
        print(chunk['message']['content'],end="", flush=True)
    print("\n")

    while True:
        user_input = input(">> USER: ").strip()
        print("\n")
        if user_input.lower() in ["exit", "quit"]:
            print(">> JARVIS: Good day.")
            break

        messages.append(Message(role="user", content=user_input))
        response = chat(model=MODELFILE['name'],
                        messages=messages,
                            stream=True
                        )
        print(">> JARVIS: ", end="", flush=True)
        for chunk in response:
            print(chunk['message']['content'], end="", flush=True)
        print("\n")