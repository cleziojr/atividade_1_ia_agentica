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


def _elegibilidade(aluno_id: int) -> tuple[dict, list[dict], list[dict], list[str]] | None:
    """Classifica as ofertadas em pode cursar / falta pré-requisito / já aprovado, para um aluno."""
    alunos = _carregar_historico()
    if aluno_id not in alunos:
        return None

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

    return aluno, pode_cursar, falta_prerequisito, ja_aprovado


def _parse_horario(dia_horario: str) -> tuple[set[str], str, set[str]]:
    """Decompõe um código SIGAA (ex: '24M12') em dias, turno e horários."""
    m = re.match(r"^(\d+)([MTN])(\d+)$", dia_horario)
    if not m:
        return set(), "", set()
    dias, turno, horarios = m.groups()
    return set(dias), turno, set(horarios)


def _conflitam(horario_1: str, horario_2: str) -> bool:
    """Verifica se dois códigos de horário SIGAA se sobrepõem em dia, turno e horário."""
    dias_1, turno_1, slots_1 = _parse_horario(horario_1)
    dias_2, turno_2, slots_2 = _parse_horario(horario_2)
    return turno_1 == turno_2 and bool(dias_1 & dias_2) and bool(slots_1 & slots_2)


@tool
def comparar_materias_aluno(aluno_id: int) -> str:
    """Compara o histórico de um aluno com as disciplinas ofertadas no semestre e indica quais ele pode ou não cursar, com o motivo."""
    resultado = _elegibilidade(aluno_id)
    if resultado is None:
        return f"aluno_id {aluno_id} não encontrado no histórico."
    aluno, pode_cursar, falta_prerequisito, ja_aprovado = resultado

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


@tool
def calcula_carga_hora_disciplinas(codigos: str) -> str:
    """Soma a carga horária de uma lista de códigos de disciplina ofertados, separados por vírgula ou espaço."""
    lista_codigos = [c.strip().upper() for c in codigos.replace(",", " ").split() if c.strip()]
    if not lista_codigos:
        return "Nenhum código informado."

    ofertadas = {m["codigo"]: m for m in _carregar_ofertadas()}
    encontrados, nao_encontrados, total = [], [], 0
    for codigo in lista_codigos:
        materia = ofertadas.get(codigo)
        if materia is None:
            nao_encontrados.append(codigo)
            continue
        carga = int(materia["cargaHoraria"])
        total += carga
        encontrados.append((codigo, materia["nome"], carga))

    linhas = ["Carga horária por disciplina:"]
    for codigo, nome, carga in encontrados:
        linhas.append(f"- [{codigo}] {nome}: {carga}h")
    if nao_encontrados:
        linhas.append(f"Códigos não encontrados na oferta do semestre: {', '.join(nao_encontrados)}")
    linhas.append(f"Total: {total}h em {len(encontrados)} disciplina(s).")
    return "\n".join(linhas)


@tool
def recomenda_grade_disciplinas(aluno_id: int, carga_horaria_desejada: int, interesse: str = "") -> str:
    """Recomenda disciplinas elegíveis para um aluno, priorizando uma área de interesse, sem estourar a carga horária desejada nem gerar choque de horário."""
    resultado = _elegibilidade(aluno_id)
    if resultado is None:
        return f"aluno_id {aluno_id} não encontrado no histórico."
    aluno, pode_cursar, _, _ = resultado

    interesse_normalizado = interesse.strip().lower()

    def prioridade(materia: dict) -> tuple[int, str]:
        bate_interesse = bool(interesse_normalizado) and interesse_normalizado in materia["categoria"].lower()
        return (0 if bate_interesse else 1, materia["codigo"])

    candidatas = sorted(pode_cursar, key=prioridade)

    escolhidas: list[dict] = []
    total = 0
    for materia in candidatas:
        carga = int(materia["cargaHoraria"])
        if total + carga > carga_horaria_desejada:
            continue
        if any(_conflitam(materia["dia_horario"], m["dia_horario"]) for m in escolhidas):
            continue
        escolhidas.append(materia)
        total += carga

    cabecalho = f"Grade recomendada para {aluno['nome']} (meta: {carga_horaria_desejada}h"
    cabecalho += f", interesse: {interesse})" if interesse_normalizado else ")"
    linhas = [cabecalho, ""]

    if not escolhidas:
        linhas.append("Nenhuma disciplina elegível coube na carga horária desejada.")
    for m in escolhidas:
        linhas.append(
            f"- [{m['codigo']}] {m['nome']} ({m['cargaHoraria']}h) | {m['categoria']} | "
            f"turma {m['turma']} {m['dia_horario']} ({m['modalidade']}, {m['docente']})"
        )

    linhas.append("")
    linhas.append(f"Carga horária total: {total}h de {carga_horaria_desejada}h desejadas ({len(escolhidas)} disciplina(s)).")
    if total < carga_horaria_desejada:
        linhas.append("Não foi possível atingir a meta só com disciplinas elegíveis e sem choque de horário.")

    return "\n".join(linhas)
