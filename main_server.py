from ollama import (
    chat,
    ChatResponse,
    Message,
)
from typing import Iterator, Sequence
from server import (
    read_config_file,
    init_model,
    TOOLS,
    ToolResponse,
    ToolCall,
    Function,
    handle_tool_calls,
)

if __name__ == "__main__":
    read_config_file()

    # Attempt to init the model
    yn, err = init_model()
    if not yn:
        print(f">> {err}")
        exit(0)
    else:
        global MODELFILE
        from server.startup import MODELFILE
        print(f">> {MODELFILE['name']} is ready to use.")
        

    messages: list[Message] = [Message(
            role="user",
            content="Hey Jarvis, list the tools I've made available to you to call."
            tools=TOOLS
        )
    ]

    initialresponse: Iterator[ChatResponse] = chat(
        model=MODELFILE['name'],
        messages=messages,
        stream=True,
    )

    print(f">> USER: {messages[0]['content']}\n")

    print(">> JARVIS: ", end="", flush=True)
    chunkedMessage: ChatResponse = {'role': 'assistant',
                                    'content': ''}
    """
    The message we piece together from the streamed message chunks.
    We feed this back into the chat for memory purposes. 
    We add this now so it's in order, then mutate it as the
    chunks stream in.
    """
    messages.append(chunkedMessage)

    for chunk in initialresponse:
        msgrole:str = chunk['message']['role']
    
        if msgrole == "tool":
            print(" [Calling tool...] ", end="", flush=True)
            toolsresponses = handle_tool_calls(chunk['message'])
            for toolresponse in toolsresponses:
                messages.append(toolresponse)

        else:
            print(chunk['message']['content'],end="", flush=True)
            chunkedMessage['content'] += chunk['message']['content']
    print("\n")

    reponse = chat(
        model=MODELFILE['name'],
        messages=messages,
        stream=False
    )

    print(f">> JARVIS: {reponse['message']['content']}\n")

    """
    while True:
        user_input = input(">> USER: ").strip()
        print("\n")
        if user_input.lower() in ("exit", "quit",):
            print(">> JARVIS: Good day.")
            break

        messages.append(Message(role="user", content=user_input))
        responsechunks: Iterator[ChatResponse] = chat(
            model=MODELFILE['name'],
            messages=messages,
            stream=True
        )
        print(">> JARVIS: ", end="", flush=True)
        for response in responsechunks:
            print(response['message']['content'], end="", flush=True)
        print("\n")
    """