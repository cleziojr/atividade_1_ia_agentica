"""Tool do agentkit que compara o histórico de um aluno com as disciplinas ofertadas no semestre."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from agentkit.tools import tool

DIR_DADOS = Path(__file__).resolve().parent / "dados"

_SITUACOES_APROVADAS = {"APROVADO"}


def _carregar_historico() -> dict[int, dict]:
    """Agrupa o histórico por aluno_id: nome e conjunto de códigos aprovados."""
    alunos: dict[int, dict] = {}
    with open(DIR_DADOS / "historico_alunos.csv", encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            aluno_id = int(linha["aluno_id"])
            aluno = alunos.setdefault(aluno_id, {"nome": linha["aluno_nome"], "aprovadas": set()})
            if linha["situacao"] in _SITUACOES_APROVADAS:
                aluno["aprovadas"].add(linha["codigo"])
    return alunos


def _carregar_ofertadas() -> list[dict]:
    """Lê a lista de disciplinas ofertadas no semestre vigente."""
    with open(DIR_DADOS / "materias_ofertadas.csv", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def _tokenizar(expressao: str) -> list[str]:
    return re.findall(r"\(|\)|[^\s()]+", expressao)


def _prerequisito_atendido(expressao: str, aprovadas: set[str]) -> bool:
    """Avalia uma expressão de pré-requisito (códigos, E, OU, parênteses) contra os códigos aprovados."""
    tokens = _tokenizar(expressao)
    if not tokens:
        return True
    posicao = 0

    def expr() -> bool:
        nonlocal posicao
        valor = termo()
        while posicao < len(tokens) and tokens[posicao] == "OU":
            posicao += 1
            direita = termo()
            valor = valor or direita
        return valor

    def termo() -> bool:
        nonlocal posicao
        valor = fator()
        while posicao < len(tokens) and tokens[posicao] == "E":
            posicao += 1
            direita = fator()
            valor = valor and direita
        return valor

    def fator() -> bool:
        nonlocal posicao
        if tokens[posicao] == "(":
            posicao += 1
            valor = expr()
            posicao += 1  # consome ")"
            return valor
        codigo = tokens[posicao]
        posicao += 1
        return codigo in aprovadas

    return expr()


@tool
def comparar_materias_aluno(aluno_id: int) -> str:
    """Compara o histórico de um aluno com as disciplinas ofertadas no semestre e indica quais ele pode ou não cursar, com o motivo."""
    alunos = _carregar_historico()
    if aluno_id not in alunos:
        return f"aluno_id {aluno_id} não encontrado no histórico."

    aluno = alunos[aluno_id]
    ofertadas = _carregar_ofertadas()

    pode_cursar, falta_prerequisito, ja_aprovado = [], [], []
    for materia in ofertadas:
        codigo = materia["codigo"]
        if codigo in aluno["aprovadas"]:
            ja_aprovado.append(codigo)
        elif _prerequisito_atendido(materia["preRequisito"], aluno["aprovadas"]):
            pode_cursar.append(materia)
        else:
            falta_prerequisito.append(materia)

    linhas = [f"Aluno: {aluno['nome']} (id {aluno_id})", ""]

    linhas.append(f"PODE CURSAR ({len(pode_cursar)}):")
    for m in pode_cursar:
        linhas.append(
            f"- [{m['codigo']}] {m['nome']} | {m['categoria']} | turma {m['turma']} "
            f"({m['modalidade']}, {m['dia_horario']}, {m['docente']})"
        )

    linhas.append("")
    linhas.append(f"NÃO PODE CURSAR - falta pré-requisito ({len(falta_prerequisito)}):")
    for m in falta_prerequisito:
        linhas.append(f"- [{m['codigo']}] {m['nome']} | pré-requisito: {m['preRequisito']}")

    linhas.append("")
    linhas.append(f"JÁ APROVADO antes, não conta de novo ({len(ja_aprovado)}): {', '.join(ja_aprovado) or '-'}")

    return "\n".join(linhas)
