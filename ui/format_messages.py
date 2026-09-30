import json

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

CORES = {
    "system": "\033[90m",     # cinza
    "user": "\033[94m",       # azul
    "assistant": "\033[92m",  # verde
    "tool": "\033[93m",       # amarelo
}
COR_TOOL_CALL = "\033[95m"    # magenta
COR_ERRO = "\033[91m"         # vermelho


def _formata_tool_calls(tool_calls: list[dict]) -> str:
    linhas = []
    for call in tool_calls:
        args = json.dumps(call.get("arguments", {}), ensure_ascii=False)
        linhas.append(f"{COR_TOOL_CALL}>> chama {BOLD}{call['name']}{RESET}{COR_TOOL_CALL}({args}){RESET}")
    return "\n".join(linhas)


def format_messages(messages: list[dict]) -> str:
    output = "\n"
    for m in messages:
        role = m["role"]
        cor = CORES.get(role, "")
        titulo = role.upper() + (f" · {m['name']}" if role == "tool" and "name" in m else "")
        output += f"{cor}{BOLD}<{titulo}>{RESET}\n"

        content = m.get("content") or ""
        if content:
            erro = role == "tool" and content.split(":", 1)[0].endswith(("Error", "Exception"))
            cor_texto = COR_ERRO if erro else (DIM if role == "system" else "")
            output += f"{cor_texto}>> {content}{RESET}\n"
        if m.get("tool_calls"):
            output += _formata_tool_calls(m["tool_calls"]) + "\n"
        output += "\n"

    return output


def last_message(messages: list[dict]) -> str:
    return messages[-1].get("content") or ""
