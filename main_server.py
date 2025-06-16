from ollama import (
    chat,
    ChatResponse,
    Message,
)
from typing import (
    Iterator
)
from server import (
    TOOLS,
    SYSTEM_PROMPT_TOOLS,
    handle_tool_calls,
    LOGGER,
    BotSession
)

from json import dumps

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
    
    # Extend the session messages with initial system prompts
    SESSION.extend_messages([
        {
            'role':"system",
            'content':MODELFILE['system']
        },
        {
            'role':"system",
            'content':SYSTEM_PROMPT_TOOLS
        },
        {
            'role':"user",
            'content':"Hey Jarvis, how we doing today?",
        }
    ])

    try:
        thinking = False  # Initialize thinking state globally
        skipUserInput = False  # Flag to skip user input after tool calls

        initialresponse: Iterator[ChatResponse] = SESSION.chat(
            stream=True,
        )

        print(f">> USER: {SESSION.get_message(2)['content']}\n")

        print(">> JARVIS: ", end="", flush=True)
        chunkedMessage: Message = {'role': 'assistant',
                                        'content': ''}
        """
        The message we piece together from the streamed message chunks.
        We feed this back into the chat for memory purposes. 
        We add this now so it's in order, then mutate it as the
        chunks stream in.
        """
        SESSION.add_message(chunkedMessage)

        for chunk in initialresponse:
            content = chunk['message']['content']
            
            if content.startswith("<think>"):
                thinking = True
                chunkedMessage['content'] += content
                continue
                
            if thinking:
                chunkedMessage['content'] += content
                if content.endswith("</think>"):
                    thinking = False
                continue
            
            chunkedMessage['content'] += content
            print(content, end="", flush=True)
        print("\n")

        # Remove this duplicate call - it's not needed
        # response = chat(...)

        # Reset the chunked message for the next user input
        chunkedMessage = None
        skipUserInput = False

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
                tool_calls = response.get('message', {}).get('tool_calls', [])
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

