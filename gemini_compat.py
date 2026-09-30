"""Compatibilidade do agentkit com o Gemini 3 (endpoint OpenAI).

O Gemini 3 devolve cada tool_call com extra_content.google.thought_signature e
exige que esse campo volte na requisição seguinte; sem ele a API responde
400 "Function call is missing a thought_signature". O agentkit guarda só name e
arguments da chamada, então o campo se perde. Este módulo embrulha as funções de
tradução do agentkit para preservar extra_content nos dois sentidos. Para outros
provedores nada muda, porque o campo simplesmente não existe.

Basta importar o módulo antes de usar o Agent.
"""

from agentkit import model

_from_api_message = model.from_api_message
_to_api_messages = model.to_api_messages


def from_api_message(message: dict) -> dict:
    assistant = _from_api_message(message)
    for call, raw in zip(assistant.get("tool_calls", []), message.get("tool_calls") or []):
        if "extra_content" in raw:
            call["extra_content"] = raw["extra_content"]
    return assistant


def to_api_messages(messages: list[dict]) -> list[dict]:
    api_messages = _to_api_messages(messages)
    # A tradução é 1:1 por posição, então dá para parear as listas.
    for message, api_message in zip(messages, api_messages):
        for call, api_call in zip(message.get("tool_calls") or [], api_message.get("tool_calls") or []):
            if "extra_content" in call:
                api_call["extra_content"] = call["extra_content"]
    return api_messages


model.from_api_message = from_api_message
model.to_api_messages = to_api_messages
