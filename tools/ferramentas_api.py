"""Tools do agentkit que consultam, em tempo real, a API de turmas do bot."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from agentkit.tools import tool

API_TURMAS_URL = "https://btihelpbot.duckdns.org/api/turmas"


def _buscar_turmas(**parametros: str | int) -> dict:
    """Faz a requisição GET na API de turmas com os parâmetros informados."""
    query = urllib.parse.urlencode({k: v for k, v in parametros.items() if v is not None})
    with urllib.request.urlopen(f"{API_TURMAS_URL}?{query}", timeout=10) as response:
        return json.load(response)


@tool
def consulta_turma_api(nome_ou_codigo: str) -> str:
    """Consulta em tempo real, na API de turmas do IMD, disciplinas que combinam com um nome ou código."""
    try:
        dados = _buscar_turmas(q=nome_ou_codigo, tamanho=5)
    except Exception as erro:
        return f"Erro ao consultar a API de turmas: {erro}"

    itens = dados.get("itens", [])
    if not itens:
        return f"Nenhuma disciplina encontrada para '{nome_ou_codigo}'."

    linhas = [f"{len(itens)} disciplina(s) encontrada(s) para '{nome_ou_codigo}':", ""]
    for item in itens:
        taxa = item.get("taxaAprovacao") or 0
        linhas.append(
            f"- [{item['codigo']}] {item['nome']} ({item['cargaHoraria']}h)\n"
            f"  Setor: {item['setor']}\n"
            f"  Pré-requisito: {item.get('preRequisito') or 'nenhum'}\n"
            f"  Equivalências: {item.get('equivalencias') or 'nenhuma'}\n"
            f"  Taxa de aprovação: {taxa * 100:.0f}% "
            f"({item['aprovados']} aprovados de {item['totalAvaliados']} avaliados)"
        )
    return "\n".join(linhas)


@tool
def taxa_aprovacao_disciplina(codigo: str) -> str:
    """Consulta na API de turmas a taxa de aprovação e o histórico de resultados de uma disciplina pelo código exato."""
    try:
        dados = _buscar_turmas(q=codigo, tamanho=10)
    except Exception as erro:
        return f"Erro ao consultar a API de turmas: {erro}"

    item = next((i for i in dados.get("itens", []) if i["codigo"].upper() == codigo.upper()), None)
    if item is None:
        return f"Código '{codigo}' não encontrado na API de turmas."

    taxa = item.get("taxaAprovacao") or 0
    return (
        f"[{item['codigo']}] {item['nome']}\n"
        f"Taxa de aprovação: {taxa * 100:.0f}%\n"
        f"Aprovados: {item['aprovados']} | Reprovados por nota: {item['reprovadosNota']} | "
        f"Reprovados por falta: {item['reprovadosFalta']} | Trancados: {item['trancados']}\n"
        f"Total avaliados: {item['totalAvaliados']} | Total matriculados: {item['totalMatriculados']}"
    )
