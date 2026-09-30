import sys
from typing import Literal

from agentkit.tools import tool
from pydantic import BaseModel

from prompts.secure_prompt import SECURE_SYSTEM


class IntencaoUsuario(BaseModel):
    intencao: Literal[
        "planejamento_matricula",
        "fora_escopo",
    ]
    justificativa: str


_llm = None

def configura_llm(llm) -> None:
    global _llm
    _llm = llm

@tool
def recebe_input_usuario(pergunta: str) -> str:
  """Mostra a mensagem `pergunta` ao usuário (resposta, grade proposta ou pergunta) e devolve o que ele digitar, até 300 caracteres.
  Exemplos de comandos de solicitação de informações para o usuário responder/comunicar:
  'Descreva quais disciplinas você deseja cursar neste semestre. Informe suas prioridades e restrições de forma detalhada.'
  'Informe o que você acha que não funciona para você no planejamento de disciplinas que fiz para você, com o objetivo de eu melhorar'
  """
  input_usuario = input(f"\n>> {pergunta}\n\n>> ")[:300]
  intencao = classifica_intencao_usuario(input_usuario)
  if intencao.intencao == "fora_escopo":
    return f"FORA_DO_ESCOPO: a resposta do usuário não trata do planejamento de disciplinas ({intencao.justificativa})."
  return input_usuario

def classifica_intencao_usuario(input_usuario: str) -> IntencaoUsuario:
    """Classifica se a solicitação está relacionada ao planejamento de disciplinas."""
    if _llm is None:
        raise RuntimeError("Chame configura_llm(llm) antes de usar classifica_intencao_usuario.")

    resposta = _llm.generate_structured([
    {"role": "system", "content": SECURE_SYSTEM,},
    { "role": "user", "content": f""" 
    Analise a solicitação abaixo.
    Determine se a intenção do usuário está relacionada ao planejamento da grade de disciplinas do semestre.
    Solicitação: {input_usuario} """,
                },
            ],
            IntencaoUsuario,
            max_tokens=1000,
        )

    return resposta
  

@tool
def encerra_planejamento() -> None:
  """Encerra conversa conforme o LLM achar necessário"""
  sys.exit()