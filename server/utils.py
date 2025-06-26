from ollama import Tool, Message
from ._types import (
    ToolCall,
    ToolResponse,
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
    """
{- if .Messages }}
{{- if or .System .Tools }}<|im_start|>system
{{- if .System }}
{{ .System }}
{{- end }}
{{- if .Tools }}

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{{- range .Tools }}
{"type": "function", "function": {{ .Function }}}
{{- end }}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call>
{{- end }}<|im_end|>
{{ end }}
{{- range $i, $_ := .Messages }}
{{- $last := eq (len (slice $.Messages $i)) 1 -}}
{{- if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{ else if eq .Role "assistant" }}<|im_start|>assistant
{{ if .Content }}{{ .Content }}
{{- else if .ToolCalls }}<tool_call>
{{ range .ToolCalls }}{"name": "{{ .Function.Name }}", "arguments": {{ .Function.Arguments }}}
{{ end }}</tool_call>
{{- end }}{{ if not $last }}<|im_end|>
{{ end }}
{{- else if eq .Role "tool" }}<|im_start|>user
<tool_response>
{{ .Content }}
</tool_response><|im_end|>
{{ end }}
{{- if and (ne .Role "assistant") $last }}<|im_start|>assistant
{{ end }}
{{- end }}
{{- else }}
{{- if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ end }}{{ .Response }}{{ if .Response }}<|im_end|>{{ end }}
    """
)

SYSTEM_PROMPT_THIKING_SUPPRESION = (
"""
{- range $i, $_ := .Messages }}
{{- $last := eq (len (slice $.Messages $i)) 1 -}}
{{- if eq .Role "user" }}<|im_start|>user
{{ .Content }}
{{/* This part correctly appends /think or /no_think based on $.IsThinkSet and $.Think */}}
{{- if and $.IsThinkSet (eq $i $lastUserIdx) }}
   {{- if $.Think -}}
      {{- " "}}/think
   {{- else -}}
      {{- " "}}/no_think
   {{- end -}}
{{- end }}<|im_end|>
{{ else if eq .Role "assistant" }}<|im_start|>assistant
{{/* Modified condition: Only render .Thinking if $.Think is true (user explicitly wants to think) */}}
{{ if (and $.Think .Thinking (or $last (gt $i $lastUserIdx))) -}}
<think>{{ .Thinking }}</think>
{{ end -}}
{{ if .Content }}{{ .Content }}
{{- else if .ToolCalls }}<tool_call>
{{ range .ToolCalls }}{"name": "{{ .Function.Name }}", "arguments": {{ .Function.Arguments }}}
{{ end }}</tool_call>
{{- end }}{{ if not $last }}<|im_end|>
{{ end }}
{{- else if eq .Role "tool" }}<|im_start|>user
<tool_response>
{{ .Content }}
</tool_response><|im_end|>
{{ end }}
{{- if and (ne .Role "assistant") $last }}<|im_start|>assistant
{{/* Removed the conditional empty <think> block.
     If $.Think is true, the model should generate the <think> block itself.
     If $.Think is false, no thinking is desired.
     Original block that was here:
     {{ if and $.IsThinkSet (not $.Think) -}}
     <think>

     </think>
     {{ end -}}
*/}}
{{ end }}
{{- end }}
"""
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

