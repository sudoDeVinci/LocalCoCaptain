from ollama import (
    chat,
    ChatResponse,
    Message
)
from typing import (
    Iterator
)
from server import (
    TOOLS,
    SYSTEM_PROMPT_TOOLS,
    SYSTEM_PROMPT_THIKING_SUPPRESION,
    handle_tool_calls,
    LOGGER,
    BotSession,
    ToolCall
)

if __name__ == "__main__":
    SESSION = BotSession(params="14b",
                         logfile="chat_history.json",
                         tools=TOOLS)

    # Attempt to init the model
    yn, err = SESSION.init_model()
    if not yn or not SESSION.modelfile:
        print(f">> {err}")
        exit(0)

    MODELFILE = SESSION.modelfile
    print(f">> {MODELFILE['name']} is ready to use.")

    SESSION.prepend_messages((
        {
            'role':"system",
            'content':MODELFILE['system']
        },
        {
            'role':"system",
            'content':SYSTEM_PROMPT_TOOLS
        },
        {
            'role':"system",
            'content':SYSTEM_PROMPT_THIKING_SUPPRESION
        }
    ))

    # Preload the model into memory with the system prompts
    SESSION.chat(
        stream=False,
    )

    thinking = False  # Initialize thinking state globally
    skipUserInput = False  # Flag to skip user input after tool calls

    try:
        while True:
            if skipUserInput is False:
                user_input = input(">> USER: ").strip()
                print()  # Clean newline
                if user_input.lower() in ("exit", "quit",):
                    print(">> JARVIS: Good day.")
                    raise KeyboardInterrupt

                SESSION.add_message(
                    {
                        'role':"user",
                        'content':user_input
                    }
                )

            skipUserInput = False

            responsechunks: Iterator[ChatResponse] = SESSION.chat(
                stream=True,
            )

            print(">> JARVIS: ", end="", flush=True)
            chunkedMessage: Message = {
                'role': 'assistant',
                'content': ''
            }

            SESSION.add_message(chunkedMessage)
            
            for response in responsechunks:
                content = response['message']['content']
                tool_calls: list[ToolCall] = response.get('message', {}).get('tool_calls', [])
                chunkedMessage['content'] += content

                if content.startswith("<think>"):
                    thinking = True
                    continue
                    
                if thinking:
                    if content.endswith("</think>"):
                        thinking = False
                    continue

                print(content, end="", flush=True)


                if tool_calls:
                    print(f"\n>> TOOL CALLS: {tool_calls}")
                    # chunkedMessage["tool_calls"] = tool_calls
                    res = handle_tool_calls(response['message'])
                    for tool in res:
                        print(f">> TOOL: {tool['name']} - {tool['content']}")
                        SESSION.add_message(tool)
                    
                    skipUserInput = True
                    break

            if not skipUserInput:
                print()  # Clean newline only if we're not skipping user input


    except KeyboardInterrupt:
        print("\n>> JARVIS: Good day.")
        SESSION.save()

