"""Tool do agentkit que registra o feedback do aluno sobre a grade proposta."""

import json
from pathlib import Path

from agentkit.tools import tool

FEEDBACK_PATH = Path(__file__).resolve().parent.parent / "dados" / "feedback.jsonl"


@tool
def coleta_feedback(aluno_id: int, mensagem: str) -> str:
    """Registra o feedback do aluno sobre a grade proposta, para ajustar recomendações futuras."""
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    registro = {"aluno_id": aluno_id, "mensagem": mensagem}
    with open(FEEDBACK_PATH, "a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return f'Feedback registrado para o aluno {aluno_id}: "{mensagem}"'
