from .ferramentas_api import (
    consulta_turma_api,
    taxa_aprovacao_disciplina
)
from .ferramentas_feedback import (
    coleta_feedback
)
from .ferramentas_interacao_usuario import (
    configura_llm,
    recebe_input_usuario,
    classifica_intencao_usuario,
    encerra_planejamento
)

from .ferramentas_materias import (
    calcula_carga_hora_disciplinas,
    comparar_materias_aluno,
    recomenda_grade_disciplinas
)