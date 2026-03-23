"""
Servico do Report Agent
Geracao de relatorios de simulacao no padrao ReACT usando LangChain + Zep

Funcionalidades:
1. Gerar relatorios com base nas demandas de simulacao e informacoes do grafo Zep
2. Primeiro planeja a estrutura do sumario, depois gera por secoes
3. Cada secao utiliza o padrao ReACT com multiplas rodadas de raciocinio e reflexao
4. Suporta dialogo com o usuario, invocando ferramentas de busca de forma autonoma
"""

import os
import json
import time
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from .zep_tools import (
    ZepToolsService, 
    SearchResult, 
    InsightForgeResult, 
    PanoramaResult,
    InterviewResult
)

logger = get_logger('mirofish.report_agent')


class ReportLogger:
    """
    Registrador detalhado do Report Agent

    Gera um arquivo agent_log.jsonl na pasta do relatorio, registrando cada acao detalhada.
    Cada linha e um objeto JSON completo, contendo timestamp, tipo de acao, conteudo detalhado, etc.
    """

    def __init__(self, report_id: str):
        """
        Inicializa o registrador de logs

        Args:
            report_id: ID do relatorio, usado para determinar o caminho do arquivo de log
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'agent_log.jsonl'
        )
        self.start_time = datetime.now()
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Garante que o diretorio do arquivo de log existe"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)

    def _get_elapsed_time(self) -> float:
        """Obtem o tempo decorrido desde o inicio (em segundos)"""
        return (datetime.now() - self.start_time).total_seconds()

    def log(
        self,
        action: str,
        stage: str,
        details: Dict[str, Any],
        section_title: str = None,
        section_index: int = None
    ):
        """
        Registra uma entrada de log

        Args:
            action: Tipo de acao, ex: 'start', 'tool_call', 'llm_response', 'section_complete', etc.
            stage: Estagio atual, ex: 'planning', 'generating', 'completed'
            details: Dicionario com conteudo detalhado, sem truncamento
            section_title: Titulo da secao atual (opcional)
            section_index: Indice da secao atual (opcional)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": round(self._get_elapsed_time(), 2),
            "report_id": self.report_id,
            "action": action,
            "stage": stage,
            "section_title": section_title,
            "section_index": section_index,
            "details": details
        }
        
        # Escreve no arquivo JSONL em modo append
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def log_start(self, simulation_id: str, graph_id: str, simulation_requirement: str):
        """Registra o inicio da geracao do relatorio"""
        self.log(
            action="report_start",
            stage="pending",
            details={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "simulation_requirement": simulation_requirement,
                "message": "Tarefa de geracao de relatorio iniciada"
            }
        )

    def log_planning_start(self):
        """Registra o inicio do planejamento do sumario"""
        self.log(
            action="planning_start",
            stage="planning",
            details={"message": "Iniciando planejamento do sumario do relatorio"}
        )

    def log_planning_context(self, context: Dict[str, Any]):
        """Registra as informacoes de contexto obtidas durante o planejamento"""
        self.log(
            action="planning_context",
            stage="planning",
            details={
                "message": "Informacoes de contexto da simulacao obtidas",
                "context": context
            }
        )

    def log_planning_complete(self, outline_dict: Dict[str, Any]):
        """Registra a conclusao do planejamento do sumario"""
        self.log(
            action="planning_complete",
            stage="planning",
            details={
                "message": "Planejamento do sumario concluido",
                "outline": outline_dict
            }
        )

    def log_section_start(self, section_title: str, section_index: int):
        """Registra o inicio da geracao de uma secao"""
        self.log(
            action="section_start",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={"message": f"Iniciando geracao da secao: {section_title}"}
        )

    def log_react_thought(self, section_title: str, section_index: int, iteration: int, thought: str):
        """Registra o processo de raciocinio ReACT"""
        self.log(
            action="react_thought",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "thought": thought,
                "message": f"ReACT rodada {iteration} de raciocinio"
            }
        )
    
    def log_tool_call(
        self,
        section_title: str,
        section_index: int,
        tool_name: str,
        parameters: Dict[str, Any],
        iteration: int
    ):
        """Registra uma chamada de ferramenta"""
        self.log(
            action="tool_call",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "parameters": parameters,
                "message": f"Chamando ferramenta: {tool_name}"
            }
        )

    def log_tool_result(
        self,
        section_title: str,
        section_index: int,
        tool_name: str,
        result: str,
        iteration: int
    ):
        """Registra o resultado de uma chamada de ferramenta (conteudo completo, sem truncamento)"""
        self.log(
            action="tool_result",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "tool_name": tool_name,
                "result": result,  # Resultado completo, sem truncamento
                "result_length": len(result),
                "message": f"Ferramenta {tool_name} retornou resultado"
            }
        )
    
    def log_llm_response(
        self,
        section_title: str,
        section_index: int,
        response: str,
        iteration: int,
        has_tool_calls: bool,
        has_final_answer: bool
    ):
        """Registra a resposta do LLM (conteudo completo, sem truncamento)"""
        self.log(
            action="llm_response",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "iteration": iteration,
                "response": response,  # Resposta completa, sem truncamento
                "response_length": len(response),
                "has_tool_calls": has_tool_calls,
                "has_final_answer": has_final_answer,
                "message": f"Resposta do LLM (chamada de ferramenta: {has_tool_calls}, resposta final: {has_final_answer})"
            }
        )
    
    def log_section_content(
        self,
        section_title: str,
        section_index: int,
        content: str,
        tool_calls_count: int
    ):
        """Registra a conclusao da geracao do conteudo da secao (apenas conteudo, nao significa que a secao inteira esta concluida)"""
        self.log(
            action="section_content",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": content,  # Conteudo completo, sem truncamento
                "content_length": len(content),
                "tool_calls_count": tool_calls_count,
                "message": f"Conteudo da secao {section_title} gerado com sucesso"
            }
        )

    def log_section_full_complete(
        self,
        section_title: str,
        section_index: int,
        full_content: str
    ):
        """
        Registra a conclusao da geracao de uma secao

        O frontend deve monitorar este log para verificar se uma secao foi realmente concluida e obter o conteudo completo
        """
        self.log(
            action="section_complete",
            stage="generating",
            section_title=section_title,
            section_index=section_index,
            details={
                "content": full_content,
                "content_length": len(full_content),
                "message": f"Secao {section_title} gerada com sucesso"
            }
        )

    def log_report_complete(self, total_sections: int, total_time_seconds: float):
        """Registra a conclusao da geracao do relatorio"""
        self.log(
            action="report_complete",
            stage="completed",
            details={
                "total_sections": total_sections,
                "total_time_seconds": round(total_time_seconds, 2),
                "message": "Geracao do relatorio concluida"
            }
        )

    def log_error(self, error_message: str, stage: str, section_title: str = None):
        """Registra um erro"""
        self.log(
            action="error",
            stage=stage,
            section_title=section_title,
            section_index=None,
            details={
                "error": error_message,
                "message": f"Erro ocorrido: {error_message}"
            }
        )


class ReportConsoleLogger:
    """
    Registrador de log de console do Report Agent

    Escreve logs no estilo console (INFO, WARNING, etc.) no arquivo console_log.txt dentro da pasta do relatorio.
    Esses logs diferem do agent_log.jsonl por serem saida de console em formato texto puro.
    """

    def __init__(self, report_id: str):
        """
        Inicializa o registrador de log de console

        Args:
            report_id: ID do relatorio, usado para determinar o caminho do arquivo de log
        """
        self.report_id = report_id
        self.log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, 'reports', report_id, 'console_log.txt'
        )
        self._ensure_log_file()
        self._file_handler = None
        self._setup_file_handler()
    
    def _ensure_log_file(self):
        """Garante que o diretorio do arquivo de log existe"""
        log_dir = os.path.dirname(self.log_file_path)
        os.makedirs(log_dir, exist_ok=True)

    def _setup_file_handler(self):
        """Configura o handler de arquivo para gravar logs simultaneamente em arquivo"""
        import logging

        # Cria o handler de arquivo
        self._file_handler = logging.FileHandler(
            self.log_file_path,
            mode='a',
            encoding='utf-8'
        )
        self._file_handler.setLevel(logging.INFO)

        # Usa o mesmo formato conciso do console
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        self._file_handler.setFormatter(formatter)

        # Adiciona aos loggers relacionados ao report_agent
        loggers_to_attach = [
            'mirofish.report_agent',
            'mirofish.zep_tools',
        ]

        for logger_name in loggers_to_attach:
            target_logger = logging.getLogger(logger_name)
            # Evita adicionar duplicatas
            if self._file_handler not in target_logger.handlers:
                target_logger.addHandler(self._file_handler)

    def close(self):
        """Fecha o handler de arquivo e o remove dos loggers"""
        import logging

        if self._file_handler:
            loggers_to_detach = [
                'mirofish.report_agent',
                'mirofish.zep_tools',
            ]

            for logger_name in loggers_to_detach:
                target_logger = logging.getLogger(logger_name)
                if self._file_handler in target_logger.handlers:
                    target_logger.removeHandler(self._file_handler)

            self._file_handler.close()
            self._file_handler = None

    def __del__(self):
        """Garante o fechamento do handler de arquivo ao destruir o objeto"""
        self.close()


class ReportStatus(str, Enum):
    """Status do relatorio"""
    PENDING = "pending"
    PLANNING = "planning"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReportSection:
    """Secao do relatorio"""
    title: str
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content
        }

    def to_markdown(self, level: int = 2) -> str:
        """Converte para formato Markdown"""
        md = f"{'#' * level} {self.title}\n\n"
        if self.content:
            md += f"{self.content}\n\n"
        return md


@dataclass
class ReportOutline:
    """Sumario do relatorio"""
    title: str
    summary: str
    sections: List[ReportSection]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "sections": [s.to_dict() for s in self.sections]
        }
    
    def to_markdown(self) -> str:
        """Converte para formato Markdown"""
        md = f"# {self.title}\n\n"
        md += f"> {self.summary}\n\n"
        for section in self.sections:
            md += section.to_markdown()
        return md


@dataclass
class Report:
    """Relatorio completo"""
    report_id: str
    simulation_id: str
    graph_id: str
    simulation_requirement: str
    status: ReportStatus
    outline: Optional[ReportOutline] = None
    markdown_content: str = ""
    created_at: str = ""
    completed_at: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "simulation_id": self.simulation_id,
            "graph_id": self.graph_id,
            "simulation_requirement": self.simulation_requirement,
            "status": self.status.value,
            "outline": self.outline.to_dict() if self.outline else None,
            "markdown_content": self.markdown_content,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


# ═══════════════════════════════════════════════════════════════
# Constantes de templates de prompt
# ═══════════════════════════════════════════════════════════════

# ── Descricao das ferramentas ──

TOOL_DESC_INSIGHT_FORGE = """\
[Busca de Insights Profundos - Ferramenta poderosa de busca]
Esta e nossa poderosa funcao de busca, projetada para analise profunda. Ela:
1. Decompoe automaticamente sua pergunta em multiplas subquestoes
2. Busca informacoes no grafo de simulacao a partir de multiplas dimensoes
3. Integra resultados de busca semantica, analise de entidades e rastreamento de cadeias de relacionamento
4. Retorna o conteudo mais abrangente e profundo

[Cenarios de uso]
- Necessidade de analisar profundamente um topico
- Necessidade de entender multiplos aspectos de um evento
- Necessidade de obter material rico para sustentar secoes do relatorio

[Conteudo retornado]
- Textos originais de fatos relevantes (podem ser citados diretamente)
- Insights de entidades centrais
- Analise de cadeias de relacionamento"""

TOOL_DESC_PANORAMA_SEARCH = """\
[Busca Panoramica - Visao geral completa]
Esta ferramenta obtem a visao completa dos resultados da simulacao, especialmente adequada para entender a evolucao dos eventos. Ela:
1. Obtem todos os nos e relacionamentos relevantes
2. Distingue entre fatos atualmente validos e fatos historicos/expirados
3. Ajuda a entender como as discussoes publicas e reacoes sociais evoluiram

[Cenarios de uso]
- Necessidade de entender o desenvolvimento completo de um evento
- Necessidade de comparar mudancas nas discussoes publicas em diferentes fases
- Necessidade de obter informacoes completas de entidades e relacionamentos

[Conteudo retornado]
- Fatos atualmente validos (resultados mais recentes da simulacao)
- Fatos historicos/expirados (registros de evolucao)
- Todas as entidades envolvidas"""

TOOL_DESC_QUICK_SEARCH = """\
[Busca Simples - Busca rapida]
Ferramenta de busca rapida e leve, adequada para consultas de informacao simples e diretas.

[Cenarios de uso]
- Necessidade de encontrar rapidamente uma informacao especifica
- Necessidade de verificar um fato
- Busca simples de informacoes

[Conteudo retornado]
- Lista de fatos mais relevantes para a consulta"""

TOOL_DESC_INTERVIEW_AGENTS = """\
[Entrevista Aprofundada - Entrevista real com Agents (duas plataformas)]
Chama a API de entrevista do ambiente de simulacao OASIS para entrevistar Agents de simulacao em execucao!
Nao e uma simulacao de LLM, mas sim uma chamada a interface real de entrevista para obter respostas originais dos Agents simulados.
Por padrao, entrevista simultaneamente nas plataformas Twitter e Reddit para obter perspectivas mais abrangentes.

Fluxo de funcionalidades:
1. Le automaticamente os arquivos de perfil para conhecer todos os Agents simulados
2. Seleciona inteligentemente os Agents mais relevantes para o tema da entrevista (ex: estudantes, midia, autoridades, etc.)
3. Gera automaticamente perguntas de entrevista
4. Chama a interface /api/simulation/interview/batch para realizar entrevistas reais nas duas plataformas
5. Integra todos os resultados das entrevistas, fornecendo analise multiperspectiva

[Cenarios de uso]
- Necessidade de entender visoes de diferentes papeis sobre o evento (o que pensam os estudantes? E a midia? E as autoridades?)
- Necessidade de coletar opinioes e posicoes de multiplas partes
- Necessidade de obter respostas reais dos Agents simulados (vindas do ambiente de simulacao OASIS)
- Desejo de tornar o relatorio mais vivido, incluindo "registros de entrevistas"

[Conteudo retornado]
- Informacoes de identidade dos Agents entrevistados
- Respostas de cada Agent nas plataformas Twitter e Reddit
- Citacoes-chave (podem ser citadas diretamente)
- Resumo das entrevistas e comparacao de pontos de vista

[Importante] E necessario que o ambiente de simulacao OASIS esteja em execucao para usar esta funcionalidade!"""

# ── Prompt de planejamento do sumario ──

PLAN_SYSTEM_PROMPT = """\
Voce e um especialista em redacao de "Relatorios de Previsao Futura", com uma "visao onisciente" do mundo simulado — voce pode observar o comportamento, as falas e as interacoes de cada Agent na simulacao.

IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro.

[Conceito Central]
Construimos um mundo simulado e injetamos nele uma "demanda de simulacao" especifica como variavel. O resultado da evolucao do mundo simulado e uma previsao do que pode acontecer no futuro. O que voce esta observando nao sao "dados experimentais", mas sim um "ensaio do futuro".

[Sua Tarefa]
Redigir um "Relatorio de Previsao Futura" que responda:
1. Sob as condicoes que definimos, o que aconteceu no futuro?
2. Como os diferentes tipos de Agents (grupos) reagiram e agiram?
3. Quais tendencias e riscos futuros dignos de atencao esta simulacao revelou?

[Posicionamento do Relatorio]
- Este e um relatorio de previsao futura baseado em simulacao, revelando "se assim, como sera o futuro"
- Foco nos resultados da previsao: evolucao dos eventos, reacoes dos grupos, fenomenos emergentes, riscos potenciais
- As falas e acoes dos Agents no mundo simulado sao previsoes do comportamento futuro dos grupos
- NAO e uma analise da situacao atual do mundo real
- NAO e um resumo generico de opiniao publica

[Limite de Secoes]
- Minimo 2 secoes, maximo 5 secoes
- Nao sao necessarias subsecoes, cada secao deve ter conteudo completo
- O conteudo deve ser conciso, focado nas descobertas centrais da previsao
- A estrutura das secoes deve ser projetada por voce com base nos resultados da previsao

Por favor, produza o sumario do relatorio em formato JSON, conforme abaixo:
{
    "title": "Titulo do relatorio",
    "summary": "Resumo do relatorio (uma frase resumindo a descoberta central da previsao)",
    "sections": [
        {
            "title": "Titulo da secao",
            "description": "Descricao do conteudo da secao"
        }
    ]
}

Atencao: o array sections deve ter no minimo 2 e no maximo 5 elementos!"""

PLAN_USER_PROMPT_TEMPLATE = """\
[Configuracao do Cenario de Previsao]
A variavel que injetamos no mundo simulado (demanda de simulacao): {simulation_requirement}

[Escala do Mundo Simulado]
- Quantidade de entidades participantes da simulacao: {total_nodes}
- Quantidade de relacionamentos gerados entre entidades: {total_edges}
- Distribuicao dos tipos de entidades: {entity_types}
- Quantidade de Agents ativos: {total_entities}

[Amostra de Fatos Futuros Previstos pela Simulacao]
{related_facts_json}

Analise este ensaio do futuro com uma "visao onisciente":
1. Sob as condicoes que definimos, que estado o futuro apresentou?
2. Como os diferentes tipos de pessoas (Agents) reagiram e agiram?
3. Quais tendencias futuras dignas de atencao esta simulacao revelou?

Com base nos resultados da previsao, projete a estrutura de secoes mais adequada para o relatorio.

[Lembrete] Quantidade de secoes do relatorio: minimo 2, maximo 5, conteudo deve ser conciso e focado nas descobertas centrais da previsao."""

# ── Prompt de geracao de secao ──

SECTION_SYSTEM_PROMPT_TEMPLATE = """\
Voce e um especialista em redacao de "Relatorios de Previsao Futura" e esta redigindo uma secao do relatorio.

IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro.

Titulo do relatorio: {report_title}
Resumo do relatorio: {report_summary}
Cenario de previsao (demanda de simulacao): {simulation_requirement}

Secao a ser redigida agora: {section_title}

═══════════════════════════════════════════════════════════════
[Conceito Central]
═══════════════════════════════════════════════════════════════

O mundo simulado e um ensaio do futuro. Injetamos condicoes especificas (demanda de simulacao) no mundo simulado,
e o comportamento e as interacoes dos Agents na simulacao sao previsoes do comportamento futuro dos grupos.

Sua tarefa e:
- Revelar o que aconteceu no futuro sob as condicoes definidas
- Prever como os diferentes tipos de grupos (Agents) reagiram e agiram
- Descobrir tendencias futuras, riscos e oportunidades dignos de atencao

NAO escreva como uma analise da situacao atual do mundo real
FOQUE em "como sera o futuro" — os resultados da simulacao sao o futuro previsto

═══════════════════════════════════════════════════════════════
[Regras Mais Importantes - Obrigatorio seguir]
═══════════════════════════════════════════════════════════════

1. [Obrigatorio chamar ferramentas para observar o mundo simulado]
   - Voce esta observando o ensaio do futuro com uma "visao onisciente"
   - Todo o conteudo deve vir de eventos e falas/acoes dos Agents no mundo simulado
   - Proibido usar seu proprio conhecimento para escrever o conteudo do relatorio
   - Cada secao deve chamar ferramentas pelo menos 3 vezes (maximo 5) para observar o mundo simulado, que representa o futuro

2. [Obrigatorio citar falas/acoes originais dos Agents]
   - As falas e comportamentos dos Agents sao previsoes do comportamento futuro dos grupos
   - Use formato de citacao no relatorio para apresentar essas previsoes, por exemplo:
     > "Um certo grupo expressaria: conteudo original..."
   - Essas citacoes sao as evidencias centrais da previsao simulada

3. [Consistencia linguistica - Citacoes devem ser traduzidas para o idioma do relatorio]
   - O conteudo retornado pelas ferramentas pode conter ingles, portugues ou expressoes mistas
   - O relatorio deve seguir o idioma principal da solicitacao do usuario e dos materiais originais
   - Se nao houver indicacao clara, use portugues do Brasil como padrao
   - Ao citar conteudo em outros idiomas, traduza primeiro para o idioma do relatorio mantendo o sentido original
   - Esta regra se aplica tanto ao texto principal quanto ao conteudo nos blocos de citacao (formato >)

4. [Apresentar fielmente os resultados da previsao]
   - O conteudo do relatorio deve refletir os resultados da simulacao que representam o futuro no mundo simulado
   - Nao adicione informacoes que nao existem na simulacao
   - Se a informacao for insuficiente em algum aspecto, declare isso honestamente

═══════════════════════════════════════════════════════════════
[Normas de Formato - Extremamente importante!]
═══════════════════════════════════════════════════════════════

[Uma secao = unidade minima de conteudo]
- Cada secao e a menor unidade de divisao do relatorio
- PROIBIDO usar qualquer titulo Markdown dentro da secao (#, ##, ###, ####, etc.)
- PROIBIDO adicionar o titulo principal da secao no inicio do conteudo
- O titulo da secao e adicionado automaticamente pelo sistema, voce so precisa escrever o texto corrido
- Use **negrito**, separacao de paragrafos, citacoes e listas para organizar o conteudo, mas nao use titulos

[Exemplo correto]
```
Esta secao analisa a dinamica de propagacao e a reacao social do evento. Por meio de analise aprofundada dos dados de simulacao, descobrimos...

**Fase de detonacao inicial**

O X/Twitter, como linha de frente da discussao publica, assumiu a funcao importante de lancamento de informacoes:

> "O X/Twitter contribuiu com 68% do volume inicial de publicacoes..."

**Fase de amplificacao emocional**

O Reddit e as plataformas de videos curtos amplificaram ainda mais o impacto do evento:

- Forte impacto visual
- Alto grau de ressonancia emocional
```

[Exemplo incorreto]
```
## Resumo executivo          <- Errado! Nao adicione nenhum titulo
### 1. Fase inicial          <- Errado! Nao use ### para subsecoes
#### 1.1 Analise detalhada   <- Errado! Nao use #### para subdivisoes

Esta secao analisa...
```

═══════════════════════════════════════════════════════════════
[Ferramentas de busca disponiveis] (3-5 chamadas por secao)
═══════════════════════════════════════════════════════════════

{tools_description}

[Sugestoes de uso de ferramentas - Use diferentes ferramentas de forma combinada, nao use apenas uma]
- insight_forge: Analise de insights profundos, decompoe problemas automaticamente e busca fatos e relacionamentos em multiplas dimensoes
- panorama_search: Busca panoramica ampla, para entender a visao completa, linha do tempo e evolucao do evento
- quick_search: Verificacao rapida de um ponto de informacao especifico
- interview_agents: Entrevistar Agents simulados, obter pontos de vista em primeira pessoa e reacoes reais de diferentes papeis

═══════════════════════════════════════════════════════════════
[Fluxo de trabalho]
═══════════════════════════════════════════════════════════════

Em cada resposta voce so pode fazer uma das duas coisas a seguir (nao pode fazer as duas ao mesmo tempo):

Opcao A - Chamar ferramenta:
Escreva seu raciocinio e depois chame uma ferramenta no formato:
<tool_call>
{{"name": "nome_da_ferramenta", "parameters": {{"nome_parametro": "valor_parametro"}}}}
</tool_call>
O sistema executara a ferramenta e retornara o resultado para voce. Voce nao precisa e nao pode escrever o resultado da ferramenta.

Opcao B - Produzir conteudo final:
Quando voce ja obteve informacoes suficientes pelas ferramentas, inicie a saida com "Final Answer:" seguido do conteudo da secao.

Estritamente proibido:
- Proibido incluir chamada de ferramenta e Final Answer na mesma resposta
- Proibido inventar resultados de ferramentas (Observation), todos os resultados de ferramentas sao injetados pelo sistema
- No maximo uma chamada de ferramenta por resposta

═══════════════════════════════════════════════════════════════
[Requisitos de conteudo da secao]
═══════════════════════════════════════════════════════════════

1. O conteudo deve ser baseado nos dados de simulacao recuperados pelas ferramentas
2. Cite amplamente textos originais para demonstrar os resultados da simulacao
3. Use formato Markdown (mas proibido usar titulos):
   - Use **texto em negrito** para destacar pontos-chave (substituindo subtitulos)
   - Use listas (- ou 1.2.3.) para organizar pontos
   - Use linhas em branco para separar paragrafos diferentes
   - PROIBIDO usar #, ##, ###, #### ou qualquer sintaxe de titulo
4. [Norma de formato de citacao - Obrigatorio ser paragrafo independente]
   Citacoes devem ser paragrafos independentes, com uma linha em branco antes e depois, nao podem ser misturadas nos paragrafos:

   Formato correto:
   ```
   A resposta da instituicao foi considerada carente de conteudo substancial.

   > "O modo de resposta da instituicao parece rigido e lento no ambiente de midia social em constante mudanca."

   Esta avaliacao reflete a insatisfacao geral do publico.
   ```

   Formato incorreto:
   ```
   A resposta da instituicao foi considerada carente de conteudo substancial. > "O modo de resposta da instituicao..." Esta avaliacao reflete...
   ```
5. Manter coerencia logica com as outras secoes
6. [Evitar repeticao] Leia atentamente o conteudo das secoes ja concluidas abaixo, nao repita as mesmas informacoes
7. [Reforco] Nao adicione nenhum titulo! Use **negrito** no lugar de subtitulos de subsecao"""

SECTION_USER_PROMPT_TEMPLATE = """\
Conteudo das secoes ja concluidas (leia atentamente para evitar repeticao):
{previous_content}

═══════════════════════════════════════════════════════════════
[Tarefa atual] Redigir secao: {section_title}
═══════════════════════════════════════════════════════════════

[Lembretes importantes]
1. Leia atentamente as secoes ja concluidas acima para evitar repetir o mesmo conteudo!
2. Antes de comecar, obrigatoriamente chame ferramentas para obter dados de simulacao
3. Use diferentes ferramentas de forma combinada, nao use apenas uma
4. O conteudo do relatorio deve vir dos resultados de busca, nao use seu proprio conhecimento

[Aviso de formato - Obrigatorio seguir]
- NAO escreva nenhum titulo (#, ##, ###, #### nao sao permitidos)
- NAO escreva "{section_title}" como inicio
- O titulo da secao e adicionado automaticamente pelo sistema
- Escreva diretamente o texto corrido, use **negrito** no lugar de subtitulos

Comece agora:
1. Primeiro pense (Thought) sobre quais informacoes esta secao precisa
2. Depois chame ferramentas (Action) para obter dados de simulacao
3. Apos coletar informacoes suficientes, produza o Final Answer (texto corrido puro, sem nenhum titulo)"""

# ── Templates de mensagem do ciclo ReACT ──

REACT_OBSERVATION_TEMPLATE = """\
Observation (resultado da busca):

=== Ferramenta {tool_name} retornou ===
{result}

═══════════════════════════════════════════════════════════════
Ferramentas chamadas {tool_calls_count}/{max_tool_calls} vezes (usadas: {used_tools_str}){unused_hint}
- Se a informacao for suficiente: inicie com "Final Answer:" e produza o conteudo da secao (obrigatorio citar os textos originais acima)
- Se precisar de mais informacoes: chame uma ferramenta para continuar a busca
═══════════════════════════════════════════════════════════════"""

REACT_INSUFFICIENT_TOOLS_MSG = (
    "[Atencao] Voce chamou ferramentas apenas {tool_calls_count} vezes, o minimo e {min_tool_calls} vezes. "
    "Por favor, chame mais ferramentas para obter mais dados de simulacao antes de produzir o Final Answer. {unused_hint}"
)

REACT_INSUFFICIENT_TOOLS_MSG_ALT = (
    "Atualmente foram feitas apenas {tool_calls_count} chamadas de ferramenta, o minimo e {min_tool_calls} vezes. "
    "Por favor, chame ferramentas para obter dados de simulacao. {unused_hint}"
)

REACT_TOOL_LIMIT_MSG = (
    "O limite de chamadas de ferramenta foi atingido ({tool_calls_count}/{max_tool_calls}), nao e possivel chamar mais ferramentas. "
    'Por favor, produza imediatamente o conteudo da secao iniciando com "Final Answer:" com base nas informacoes ja obtidas.'
)

REACT_UNUSED_TOOLS_HINT = "\nVoce ainda nao usou: {unused_list}, recomenda-se experimentar diferentes ferramentas para obter informacoes de multiplos angulos"

REACT_FORCE_FINAL_MSG = "O limite de chamadas de ferramenta foi atingido, por favor produza diretamente o Final Answer: e gere o conteudo da secao."

# ── Prompt de chat ──

CHAT_SYSTEM_PROMPT_TEMPLATE = """\
Voce e um assistente de previsao por simulacao conciso e eficiente.

IMPORTANTE: Todas as respostas, análises e conteúdos gerados devem ser em português brasileiro.

[Contexto]
Condicoes de previsao: {simulation_requirement}

[Relatorio de analise ja gerado]
{report_content}

[Regras]
1. Priorize responder com base no conteudo do relatorio acima
2. Responda diretamente a pergunta, evite raciocinio longo e prolixo
3. Somente chame ferramentas para buscar mais dados quando o conteudo do relatorio for insuficiente para responder
4. As respostas devem ser concisas, claras e organizadas

[Ferramentas disponiveis] (use apenas quando necessario, maximo 1-2 chamadas)
{tools_description}

[Formato de chamada de ferramenta]
<tool_call>
{{"name": "nome_da_ferramenta", "parameters": {{"nome_parametro": "valor_parametro"}}}}
</tool_call>

[Estilo de resposta]
- Conciso e direto, sem textos longos
- Use formato > para citar conteudo-chave
- Priorize a conclusao, depois explique os motivos"""

CHAT_OBSERVATION_SUFFIX = "\n\nPor favor, responda a pergunta de forma concisa."

# ═══════════════════════════════════════════════════════════════
# Prompt Helena Strategos — Análise Estratégica Final
# ═══════════════════════════════════════════════════════════════

HELENA_SYSTEM_PROMPT = """\
Voce e Helena Inteia Vasconcelos, Cientista-Chefe da INTEIA. Sua funcao e produzir \
a analise estrategica final de um relatorio de previsao por simulacao social.

IMPORTANTE: Todas as respostas devem ser em portugues brasileiro.

[Quem voce e]
- Consultora estrategica de alto nivel, nao enciclopedia
- Sempre toma posicao — nunca senta no muro
- Quantifica quando possivel (numeros > adjetivos)
- Sinceridade brutal > conforto diplomatico
- Dados antes de opiniao, recomendacao antes de analise

[Sua Tarefa]
Com base no relatorio de previsao completo gerado pela simulacao, produza uma \
secao final intitulada "Analise Estrategica" que contenha:

1. **Sintese Executiva** (3-5 linhas): o que esta simulacao revelou que NAO era obvio antes
2. **Riscos Criticos**: riscos concretos identificados, com probabilidade estimada (0-100%)
3. **Oportunidades**: janelas de acao que a simulacao revelou
4. **Recomendacoes Praticas**: acoes concretas com prazos, priorizadas por impacto
5. **Confianca da Previsao**: calibracao honesta — quao confiaveis sao estes resultados \
   (considerar: tamanho da amostra de agentes, numero de rodadas, diversidade de perfis)

[Regras Absolutas]
- Lidere com a recomendacao, fundamente depois
- Zero linguagem de esquiva ("depende", "e complexo", "ha muitas variaveis")
- Cada risco com probabilidade numerica
- Cada recomendacao com prazo e responsavel quando aplicavel
- Termine com uma frase de assinatura pessoal — acida, inteligente, memoravel

[Formato]
Responda em Markdown. Use **negrito** para destaques. NAO use titulos com # — \
use **negrito** como subtitulos. Maximo 800 palavras."""

HELENA_USER_PROMPT_TEMPLATE = """\
[Cenario da Simulacao]
Demanda: {simulation_requirement}

[Escala]
- Agentes: {total_agents}
- Rodadas executadas: {total_rounds}
- Plataformas: {platforms}

[Relatorio Completo da Simulacao]
{report_content}

Produza sua analise estrategica final."""


# ═══════════════════════════════════════════════════════════════
# Classe principal do ReportAgent
# ═══════════════════════════════════════════════════════════════


class ReportAgent:
    """
    Report Agent - Agent de geracao de relatorios de simulacao

    Utiliza o padrao ReACT (Reasoning + Acting):
    1. Fase de planejamento: analisa a demanda de simulacao, planeja a estrutura do sumario do relatorio
    2. Fase de geracao: gera conteudo secao por secao, cada secao pode chamar ferramentas multiplas vezes para obter informacoes
    3. Fase de reflexao: verifica completude e precisao do conteudo
    """

    # Maximo de chamadas de ferramenta (por secao)
    MAX_TOOL_CALLS_PER_SECTION = 5

    # Maximo de rodadas de reflexao
    MAX_REFLECTION_ROUNDS = 3

    # Maximo de chamadas de ferramenta no chat
    MAX_TOOL_CALLS_PER_CHAT = 2
    
    def __init__(
        self,
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
        llm_client: Optional[LLMClient] = None,
        zep_tools: Optional[ZepToolsService] = None
    ):
        """
        Inicializa o Report Agent

        Args:
            graph_id: ID do grafo
            simulation_id: ID da simulacao
            simulation_requirement: Descricao da demanda de simulacao
            llm_client: Cliente LLM (opcional)
            zep_tools: Servico de ferramentas Zep (opcional)
        """
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.simulation_requirement = simulation_requirement
        
        self.llm = llm_client or LLMClient(model=Config.LLM_PREMIUM_MODEL)
        self.zep_tools = zep_tools or ZepToolsService()
        
        # Definicao das ferramentas
        self.tools = self._define_tools()

        # Registrador de log (inicializado em generate_report)
        self.report_logger: Optional[ReportLogger] = None
        # Registrador de log de console (inicializado em generate_report)
        self.console_logger: Optional[ReportConsoleLogger] = None

        logger.info(f"ReportAgent inicializado: graph_id={graph_id}, simulation_id={simulation_id}")
    
    def _define_tools(self) -> Dict[str, Dict[str, Any]]:
        """Define as ferramentas disponiveis"""
        return {
            "insight_forge": {
                "name": "insight_forge",
                "description": TOOL_DESC_INSIGHT_FORGE,
                "parameters": {
                    "query": "A questao ou topico que deseja analisar em profundidade",
                    "report_context": "Contexto da secao atual do relatorio (opcional, ajuda a gerar subquestoes mais precisas)"
                }
            },
            "panorama_search": {
                "name": "panorama_search",
                "description": TOOL_DESC_PANORAMA_SEARCH,
                "parameters": {
                    "query": "Consulta de busca, usada para ordenacao por relevancia",
                    "include_expired": "Se deve incluir conteudo expirado/historico (padrao True)"
                }
            },
            "quick_search": {
                "name": "quick_search",
                "description": TOOL_DESC_QUICK_SEARCH,
                "parameters": {
                    "query": "String de consulta de busca",
                    "limit": "Quantidade de resultados retornados (opcional, padrao 10)"
                }
            },
            "interview_agents": {
                "name": "interview_agents",
                "description": TOOL_DESC_INTERVIEW_AGENTS,
                "parameters": {
                    "interview_topic": "Tema ou descricao da demanda da entrevista (ex: 'Entender a visao dos estudantes sobre o incidente de formaldeido no dormitorio')",
                    "max_agents": "Quantidade maxima de Agents a entrevistar (opcional, padrao 5, maximo 10)"
                }
            }
        }
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], report_context: str = "") -> str:
        """
        Executa uma chamada de ferramenta

        Args:
            tool_name: Nome da ferramenta
            parameters: Parametros da ferramenta
            report_context: Contexto do relatorio (usado pelo InsightForge)

        Returns:
            Resultado da execucao da ferramenta (formato texto)
        """
        logger.info(f"Executando ferramenta: {tool_name}, parametros: {parameters}")
        
        try:
            if tool_name == "insight_forge":
                query = parameters.get("query", "")
                ctx = parameters.get("report_context", "") or report_context
                result = self.zep_tools.insight_forge(
                    graph_id=self.graph_id,
                    query=query,
                    simulation_requirement=self.simulation_requirement,
                    report_context=ctx
                )
                return result.to_text()
            
            elif tool_name == "panorama_search":
                # Busca panoramica - visao geral
                query = parameters.get("query", "")
                include_expired = parameters.get("include_expired", True)
                if isinstance(include_expired, str):
                    include_expired = include_expired.lower() in ['true', '1', 'yes']
                result = self.zep_tools.panorama_search(
                    graph_id=self.graph_id,
                    query=query,
                    include_expired=include_expired
                )
                return result.to_text()
            
            elif tool_name == "quick_search":
                # Busca simples - busca rapida
                query = parameters.get("query", "")
                limit = parameters.get("limit", 10)
                if isinstance(limit, str):
                    limit = int(limit)
                result = self.zep_tools.quick_search(
                    graph_id=self.graph_id,
                    query=query,
                    limit=limit
                )
                return result.to_text()
            
            elif tool_name == "interview_agents":
                # Entrevista aprofundada - chama a API real de entrevista OASIS para obter respostas dos Agents simulados (duas plataformas)
                import concurrent.futures
                interview_topic = parameters.get("interview_topic", parameters.get("query", ""))
                max_agents = parameters.get("max_agents", 5)
                if isinstance(max_agents, str):
                    max_agents = int(max_agents)
                max_agents = min(max_agents, 10)

                # Timeout de 120s para evitar travamento; fallback para quick_search se falhar
                try:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(
                            self.zep_tools.interview_agents,
                            simulation_id=self.simulation_id,
                            interview_requirement=interview_topic,
                            simulation_requirement=self.simulation_requirement,
                            max_agents=max_agents
                        )
                        result = future.result(timeout=120)
                    return result.to_text()
                except (concurrent.futures.TimeoutError, Exception) as interview_err:
                    logger.warning(f"interview_agents falhou ({str(interview_err)}), usando quick_search como fallback")
                    fallback_result = self.zep_tools.quick_search(
                        graph_id=self.graph_id,
                        query=interview_topic,
                        limit=10
                    )
                    return f"(Entrevista nao disponivel neste momento, dados obtidos via busca no grafo)\n\n{fallback_result.to_text()}"
            
            # ========== Ferramentas antigas para compatibilidade (redirecionamento interno para novas ferramentas) ==========

            elif tool_name == "search_graph":
                # Redirecionado para quick_search
                logger.info("search_graph redirecionado para quick_search")
                return self._execute_tool("quick_search", parameters, report_context)
            
            elif tool_name == "get_graph_statistics":
                result = self.zep_tools.get_graph_statistics(self.graph_id)
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_entity_summary":
                entity_name = parameters.get("entity_name", "")
                result = self.zep_tools.get_entity_summary(
                    graph_id=self.graph_id,
                    entity_name=entity_name
                )
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            elif tool_name == "get_simulation_context":
                # Redirecionado para insight_forge, pois e mais poderoso
                logger.info("get_simulation_context redirecionado para insight_forge")
                query = parameters.get("query", self.simulation_requirement)
                return self._execute_tool("insight_forge", {"query": query}, report_context)
            
            elif tool_name == "get_entities_by_type":
                entity_type = parameters.get("entity_type", "")
                nodes = self.zep_tools.get_entities_by_type(
                    graph_id=self.graph_id,
                    entity_type=entity_type
                )
                result = [n.to_dict() for n in nodes]
                return json.dumps(result, ensure_ascii=False, indent=2)
            
            else:
                return f"Ferramenta desconhecida: {tool_name}. Por favor, use uma das seguintes: insight_forge, panorama_search, quick_search"

        except Exception as e:
            logger.error(f"Falha na execucao da ferramenta: {tool_name}, erro: {str(e)}")
            return f"Falha na execucao da ferramenta: {str(e)}"
    
    # Conjunto de nomes de ferramentas validos, usado para validacao na analise de JSON bruto como fallback
    VALID_TOOL_NAMES = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """
        Analisa chamadas de ferramenta a partir da resposta do LLM

        Formatos suportados (por prioridade):
        1. <tool_call>{"name": "tool_name", "parameters": {...}}</tool_call>
        2. JSON bruto (a resposta inteira ou uma unica linha e um JSON de chamada de ferramenta)
        """
        tool_calls = []

        # Formato 1: Estilo XML (formato padrao)
        xml_pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        for match in re.finditer(xml_pattern, response, re.DOTALL):
            try:
                call_data = json.loads(match.group(1))
                tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        if tool_calls:
            return tool_calls

        # Formato 2: Fallback - LLM produz JSON bruto (sem tags <tool_call>)
        # Tentado apenas quando o formato 1 nao encontrou correspondencia, para evitar falsos positivos com JSON no texto
        stripped = response.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            try:
                call_data = json.loads(stripped)
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
                    return tool_calls
            except json.JSONDecodeError:
                pass

        # A resposta pode conter texto de raciocinio + JSON bruto, tenta extrair o ultimo objeto JSON
        json_pattern = r'(\{"(?:name|tool)"\s*:.*?\})\s*$'
        match = re.search(json_pattern, stripped, re.DOTALL)
        if match:
            try:
                call_data = json.loads(match.group(1))
                if self._is_valid_tool_call(call_data):
                    tool_calls.append(call_data)
            except json.JSONDecodeError:
                pass

        return tool_calls

    def _is_valid_tool_call(self, data: dict) -> bool:
        """Valida se o JSON analisado e uma chamada de ferramenta valida"""
        # Suporta dois formatos de chave: {"name": ..., "parameters": ...} e {"tool": ..., "params": ...}
        tool_name = data.get("name") or data.get("tool")
        if tool_name and tool_name in self.VALID_TOOL_NAMES:
            # Unifica nomes de chave para name / parameters
            if "tool" in data:
                data["name"] = data.pop("tool")
            if "params" in data and "parameters" not in data:
                data["parameters"] = data.pop("params")
            return True
        return False
    
    def _get_tools_description(self) -> str:
        """Gera o texto de descricao das ferramentas"""
        desc_parts = ["Ferramentas disponiveis:"]
        for name, tool in self.tools.items():
            params_desc = ", ".join([f"{k}: {v}" for k, v in tool["parameters"].items()])
            desc_parts.append(f"- {name}: {tool['description']}")
            if params_desc:
                desc_parts.append(f"  Parametros: {params_desc}")
        return "\n".join(desc_parts)
    
    def plan_outline(
        self,
        progress_callback: Optional[Callable] = None
    ) -> ReportOutline:
        """
        Planeja o sumario do relatorio

        Usa o LLM para analisar a demanda de simulacao e planejar a estrutura do sumario

        Args:
            progress_callback: Funcao de callback de progresso

        Returns:
            ReportOutline: Sumario do relatorio
        """
        logger.info("Iniciando planejamento do sumario do relatorio...")

        if progress_callback:
            progress_callback("planning", 0, "Analisando demanda de simulacao...")

        # Primeiro obtem o contexto da simulacao
        context = self.zep_tools.get_simulation_context(
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement
        )
        
        if progress_callback:
            progress_callback("planning", 30, "Gerando sumario do relatorio...")
        
        system_prompt = PLAN_SYSTEM_PROMPT
        user_prompt = PLAN_USER_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            total_nodes=context.get('graph_statistics', {}).get('total_nodes', 0),
            total_edges=context.get('graph_statistics', {}).get('total_edges', 0),
            entity_types=list(context.get('graph_statistics', {}).get('entity_types', {}).keys()),
            total_entities=context.get('total_entities', 0),
            related_facts_json=json.dumps(context.get('related_facts', [])[:10], ensure_ascii=False, indent=2),
        )

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            if progress_callback:
                progress_callback("planning", 80, "Analisando estrutura do sumario...")

            # Analisa o sumario
            sections = []
            for section_data in response.get("sections", []):
                sections.append(ReportSection(
                    title=section_data.get("title", ""),
                    content=""
                ))
            
            outline = ReportOutline(
                title=response.get("title", "Relatorio de analise de simulacao"),
                summary=response.get("summary", ""),
                sections=sections
            )
            
            if progress_callback:
                progress_callback("planning", 100, "Planejamento do sumario concluido")

            logger.info(f"Planejamento do sumario concluido: {len(sections)} secoes")
            return outline
            
        except Exception as e:
            logger.error(f"Falha no planejamento do sumario: {str(e)}")
            # Retorna sumario padrao (3 secoes, como fallback)
            return ReportOutline(
                title="Relatório de previsão",
                summary="Análise de tendências futuras e riscos com base na simulação",
                sections=[
                    ReportSection(title="Cenário previsto e descobertas centrais"),
                    ReportSection(title="Análise prevista do comportamento dos grupos"),
                    ReportSection(title="Tendências futuras e alertas de risco")
                ]
            )
    
    def _generate_section_react(
        self,
        section: ReportSection,
        outline: ReportOutline,
        previous_sections: List[str],
        progress_callback: Optional[Callable] = None,
        section_index: int = 0
    ) -> str:
        """
        Gera o conteudo de uma unica secao usando o padrao ReACT

        Ciclo ReACT:
        1. Thought (raciocinio) - analisa quais informacoes sao necessarias
        2. Action (acao) - chama ferramentas para obter informacoes
        3. Observation (observacao) - analisa os resultados retornados pelas ferramentas
        4. Repete ate ter informacoes suficientes ou atingir o maximo de iteracoes
        5. Final Answer (resposta final) - gera o conteudo da secao

        Args:
            section: Secao a ser gerada
            outline: Sumario completo
            previous_sections: Conteudo das secoes anteriores (para manter coerencia)
            progress_callback: Callback de progresso
            section_index: Indice da secao (para registro de log)

        Returns:
            Conteudo da secao (formato Markdown)
        """
        logger.info(f"Gerando secao via ReACT: {section.title}")
        
        # Registra log de inicio da secao
        if self.report_logger:
            self.report_logger.log_section_start(section.title, section_index)
        
        system_prompt = SECTION_SYSTEM_PROMPT_TEMPLATE.format(
            report_title=outline.title,
            report_summary=outline.summary,
            simulation_requirement=self.simulation_requirement,
            section_title=section.title,
            tools_description=self._get_tools_description(),
        )

        # Constroi o prompt do usuario - cada secao concluida com maximo de 4000 caracteres
        if previous_sections:
            previous_parts = []
            for sec in previous_sections:
                # Maximo de 4000 caracteres por secao
                truncated = sec[:4000] + "..." if len(sec) > 4000 else sec
                previous_parts.append(truncated)
            previous_content = "\n\n---\n\n".join(previous_parts)
        else:
            previous_content = "(Esta e a primeira secao)"
        
        user_prompt = SECTION_USER_PROMPT_TEMPLATE.format(
            previous_content=previous_content,
            section_title=section.title,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Ciclo ReACT
        tool_calls_count = 0
        max_iterations = 5  # Maximo de rodadas de iteracao
        min_tool_calls = 3  # Minimo de chamadas de ferramenta
        conflict_retries = 0  # Contagem de conflitos consecutivos entre chamada de ferramenta e Final Answer
        used_tools = set()  # Registra nomes de ferramentas ja chamadas
        all_tools = {"insight_forge", "panorama_search", "quick_search", "interview_agents"}

        # Contexto do relatorio, usado para geracao de subquestoes do InsightForge
        report_context = f"Titulo da secao: {section.title}\nDemanda de simulacao: {self.simulation_requirement}"
        
        for iteration in range(max_iterations):
            if progress_callback:
                progress_callback(
                    "generating", 
                    int((iteration / max_iterations) * 100),
                    f"Busca profunda e redacao em andamento ({tool_calls_count}/{self.MAX_TOOL_CALLS_PER_SECTION})"
                )
            
            # Chama o LLM com tratamento de timeout
            try:
                response = self.llm.chat(
                    messages=messages,
                    temperature=0.5,
                    max_tokens=4096
                )
            except Exception as llm_err:
                logger.warning(f"Secao {section.title} iteracao {iteration + 1}: erro no LLM: {str(llm_err)}")
                if iteration < max_iterations - 1:
                    messages.append({"role": "assistant", "content": "(erro na chamada ao LLM)"})
                    messages.append({"role": "user", "content": "Houve um erro temporario. Continue gerando o conteudo com base nas informacoes ja coletadas."})
                    continue
                break

            # Verifica se o retorno do LLM e None (excecao da API ou conteudo vazio)
            if response is None:
                logger.warning(f"Secao {section.title} iteracao {iteration + 1}: LLM retornou None")
                # Se ainda ha iteracoes disponiveis, adiciona mensagem e tenta novamente
                if iteration < max_iterations - 1:
                    messages.append({"role": "assistant", "content": "(resposta vazia)"})
                    messages.append({"role": "user", "content": "Por favor, continue gerando o conteudo."})
                    continue
                # Ultima iteracao tambem retornou None, sai do loop para finalizacao forcada
                break

            logger.debug(f"Resposta do LLM: {response[:200]}...")

            # Analisa uma vez, reutiliza os resultados
            tool_calls = self._parse_tool_calls(response)
            has_tool_calls = bool(tool_calls)
            has_final_answer = "Final Answer:" in response

            # ── Tratamento de conflito: LLM produziu chamada de ferramenta e Final Answer ao mesmo tempo ──
            if has_tool_calls and has_final_answer:
                conflict_retries += 1
                logger.warning(
                    f"Secao {section.title} rodada {iteration+1}: "
                    f"LLM produziu chamada de ferramenta e Final Answer ao mesmo tempo (conflito #{conflict_retries})"
                )

                if conflict_retries <= 2:
                    # Primeiras duas vezes: descarta a resposta, pede ao LLM para responder novamente
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": (
                            "[Erro de formato] Voce incluiu chamada de ferramenta e Final Answer na mesma resposta, isso nao e permitido.\n"
                            "Cada resposta so pode fazer uma das duas coisas a seguir:\n"
                            "- Chamar uma ferramenta (produzir um bloco <tool_call>, sem escrever Final Answer)\n"
                            "- Produzir o conteudo final (iniciar com 'Final Answer:', sem incluir <tool_call>)\n"
                            "Por favor, responda novamente fazendo apenas uma das duas."
                        ),
                    })
                    continue
                else:
                    # Terceira vez: tratamento degradado, trunca ate a primeira chamada de ferramenta e executa
                    logger.warning(
                        f"Secao {section.title}: {conflict_retries} conflitos consecutivos, "
                        "degradando para truncar e executar a primeira chamada de ferramenta"
                    )
                    first_tool_end = response.find('</tool_call>')
                    if first_tool_end != -1:
                        response = response[:first_tool_end + len('</tool_call>')]
                        tool_calls = self._parse_tool_calls(response)
                        has_tool_calls = bool(tool_calls)
                    has_final_answer = False
                    conflict_retries = 0

            # Registra log da resposta do LLM
            if self.report_logger:
                self.report_logger.log_llm_response(
                    section_title=section.title,
                    section_index=section_index,
                    response=response,
                    iteration=iteration + 1,
                    has_tool_calls=has_tool_calls,
                    has_final_answer=has_final_answer
                )

            # ── Caso 1: LLM produziu Final Answer ──
            if has_final_answer:
                # Chamadas de ferramenta insuficientes, rejeita e pede para continuar chamando ferramentas
                if tool_calls_count < min_tool_calls:
                    messages.append({"role": "assistant", "content": response})
                    unused_tools = all_tools - used_tools
                    unused_hint = f"(Estas ferramentas ainda nao foram usadas, recomenda-se experimenta-las: {', '.join(unused_tools)})" if unused_tools else ""
                    messages.append({
                        "role": "user",
                        "content": REACT_INSUFFICIENT_TOOLS_MSG.format(
                            tool_calls_count=tool_calls_count,
                            min_tool_calls=min_tool_calls,
                            unused_hint=unused_hint,
                        ),
                    })
                    continue

                # Conclusao normal
                final_answer = response.split("Final Answer:")[-1].strip()
                logger.info(f"Secao {section.title} gerada com sucesso (chamadas de ferramenta: {tool_calls_count})")

                if self.report_logger:
                    self.report_logger.log_section_content(
                        section_title=section.title,
                        section_index=section_index,
                        content=final_answer,
                        tool_calls_count=tool_calls_count
                    )
                return final_answer

            # ── Caso 2: LLM tentou chamar ferramenta ──
            if has_tool_calls:
                # Cota de ferramentas esgotada -> informa claramente, pede para produzir Final Answer
                if tool_calls_count >= self.MAX_TOOL_CALLS_PER_SECTION:
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": REACT_TOOL_LIMIT_MSG.format(
                            tool_calls_count=tool_calls_count,
                            max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        ),
                    })
                    continue

                # Executa apenas a primeira chamada de ferramenta
                call = tool_calls[0]
                if len(tool_calls) > 1:
                    logger.info(f"LLM tentou chamar {len(tool_calls)} ferramentas, executando apenas a primeira: {call['name']}")

                if self.report_logger:
                    self.report_logger.log_tool_call(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        parameters=call.get("parameters", {}),
                        iteration=iteration + 1
                    )

                result = self._execute_tool(
                    call["name"],
                    call.get("parameters", {}),
                    report_context=report_context
                )

                if self.report_logger:
                    self.report_logger.log_tool_result(
                        section_title=section.title,
                        section_index=section_index,
                        tool_name=call["name"],
                        result=result,
                        iteration=iteration + 1
                    )

                tool_calls_count += 1
                used_tools.add(call['name'])

                # Constroi dica de ferramentas nao utilizadas
                unused_tools = all_tools - used_tools
                unused_hint = ""
                if unused_tools and tool_calls_count < self.MAX_TOOL_CALLS_PER_SECTION:
                    unused_hint = REACT_UNUSED_TOOLS_HINT.format(unused_list="、".join(unused_tools))

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": REACT_OBSERVATION_TEMPLATE.format(
                        tool_name=call["name"],
                        result=result,
                        tool_calls_count=tool_calls_count,
                        max_tool_calls=self.MAX_TOOL_CALLS_PER_SECTION,
                        used_tools_str=", ".join(used_tools),
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # ── Caso 3: Sem chamada de ferramenta e sem Final Answer ──
            messages.append({"role": "assistant", "content": response})

            if tool_calls_count < min_tool_calls:
                # Chamadas de ferramenta insuficientes, recomenda ferramentas nao utilizadas
                unused_tools = all_tools - used_tools
                unused_hint = f"(Estas ferramentas ainda nao foram usadas, recomenda-se experimenta-las: {', '.join(unused_tools)})" if unused_tools else ""

                messages.append({
                    "role": "user",
                    "content": REACT_INSUFFICIENT_TOOLS_MSG_ALT.format(
                        tool_calls_count=tool_calls_count,
                        min_tool_calls=min_tool_calls,
                        unused_hint=unused_hint,
                    ),
                })
                continue

            # Chamadas de ferramenta suficientes, LLM produziu conteudo mas sem o prefixo "Final Answer:"
            # Aceita diretamente este conteudo como resposta final, sem iteracoes vazias
            logger.info(f"Secao {section.title}: prefixo 'Final Answer:' nao detectado, aceitando saida do LLM como conteudo final (chamadas de ferramenta: {tool_calls_count})")
            final_answer = response.strip()

            if self.report_logger:
                self.report_logger.log_section_content(
                    section_title=section.title,
                    section_index=section_index,
                    content=final_answer,
                    tool_calls_count=tool_calls_count
                )
            return final_answer
        
        # Atingiu o maximo de iteracoes, forca geracao do conteudo
        logger.warning(f"Secao {section.title} atingiu o maximo de iteracoes, forcando geracao")
        messages.append({"role": "user", "content": REACT_FORCE_FINAL_MSG})

        try:
            response = self.llm.chat(
                messages=messages,
                temperature=0.5,
                max_tokens=4096
            )
        except Exception as llm_err:
            logger.error(f"Secao {section.title}: erro no LLM durante finalizacao forcada: {str(llm_err)}")
            response = None

        # Verifica se o LLM retornou None durante a finalizacao forcada
        if response is None:
            logger.error(f"Secao {section.title}: LLM retornou None durante finalizacao forcada, usando mensagem de erro padrao")
            final_answer = f"(Falha na geracao desta secao: LLM retornou resposta vazia, tente novamente mais tarde)"
        elif "Final Answer:" in response:
            final_answer = response.split("Final Answer:")[-1].strip()
        else:
            final_answer = response
        
        # Registra log de conclusao da geracao do conteudo da secao
        if self.report_logger:
            self.report_logger.log_section_content(
                section_title=section.title,
                section_index=section_index,
                content=final_answer,
                tool_calls_count=tool_calls_count
            )
        
        return final_answer
    
    def generate_report(
        self,
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
        report_id: Optional[str] = None
    ) -> Report:
        """
        Gera o relatorio completo (saida em tempo real por secao)

        Cada secao e salva na pasta imediatamente apos ser gerada, sem esperar a conclusao do relatorio inteiro.
        Estrutura de arquivos:
        reports/{report_id}/
            meta.json       - Metadados do relatorio
            outline.json    - Sumario do relatorio
            progress.json   - Progresso da geracao
            section_01.md   - Secao 1
            section_02.md   - Secao 2
            ...
            full_report.md  - Relatorio completo

        Args:
            progress_callback: Funcao de callback de progresso (stage, progress, message)
            report_id: ID do relatorio (opcional, se nao informado sera gerado automaticamente)

        Returns:
            Report: Relatorio completo
        """
        import uuid
        
        # Se nao foi informado report_id, gera automaticamente
        if not report_id:
            report_id = f"report_{uuid.uuid4().hex[:12]}"
        start_time = datetime.now()
        
        report = Report(
            report_id=report_id,
            simulation_id=self.simulation_id,
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement,
            status=ReportStatus.PENDING,
            created_at=datetime.now().isoformat()
        )
        
        # Lista de titulos de secoes concluidas (para rastreamento de progresso)
        completed_section_titles = []
        
        try:
            # Inicializacao: cria pasta do relatorio e salva estado inicial
            ReportManager._ensure_report_folder(report_id)
            
            # Inicializa o registrador de log (log estruturado agent_log.jsonl)
            self.report_logger = ReportLogger(report_id)
            self.report_logger.log_start(
                simulation_id=self.simulation_id,
                graph_id=self.graph_id,
                simulation_requirement=self.simulation_requirement
            )
            
            # Inicializa o registrador de log de console (console_log.txt)
            self.console_logger = ReportConsoleLogger(report_id)
            
            ReportManager.update_progress(
                report_id, "pending", 0, "Inicializando relatorio...",
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            # Fase 1: Planejamento do sumario
            report.status = ReportStatus.PLANNING
            ReportManager.update_progress(
                report_id, "planning", 5, "Iniciando planejamento do sumario do relatorio...",
                completed_sections=[]
            )
            
            # Registra log de inicio do planejamento
            self.report_logger.log_planning_start()
            
            if progress_callback:
                progress_callback("planning", 0, "Iniciando planejamento do sumario do relatorio...")
            
            outline = self.plan_outline(
                progress_callback=lambda stage, prog, msg: 
                    progress_callback(stage, prog // 5, msg) if progress_callback else None
            )
            report.outline = outline
            
            # Registra log de conclusao do planejamento
            self.report_logger.log_planning_complete(outline.to_dict())
            
            # Salva o sumario no arquivo
            ReportManager.save_outline(report_id, outline)
            ReportManager.update_progress(
                report_id, "planning", 15, f"Planejamento do sumario concluido, {len(outline.sections)} secoes no total",
                completed_sections=[]
            )
            ReportManager.save_report(report)
            
            logger.info(f"Sumario salvo no arquivo: {report_id}/outline.json")

            # Fase 2: Geracao secao por secao (salvamento por secao)
            report.status = ReportStatus.GENERATING
            
            total_sections = len(outline.sections)
            generated_sections = []  # Salva conteudo para contexto
            
            for i, section in enumerate(outline.sections):
                section_num = i + 1
                base_progress = 20 + int((i / total_sections) * 70)
                
                # Atualiza progresso
                ReportManager.update_progress(
                    report_id, "generating", base_progress,
                    f"Gerando secao: {section.title} ({section_num}/{total_sections})",
                    current_section=section.title,
                    completed_sections=completed_section_titles
                )
                
                if progress_callback:
                    progress_callback(
                        "generating",
                        base_progress,
                        f"Gerando secao: {section.title} ({section_num}/{total_sections})"
                    )
                
                # Gera conteudo da secao principal
                section_content = self._generate_section_react(
                    section=section,
                    outline=outline,
                    previous_sections=generated_sections,
                    progress_callback=lambda stage, prog, msg:
                        progress_callback(
                            stage, 
                            base_progress + int(prog * 0.7 / total_sections),
                            msg
                        ) if progress_callback else None,
                    section_index=section_num
                )
                
                section.content = section_content
                generated_sections.append(f"## {section.title}\n\n{section_content}")

                # Salva a secao
                ReportManager.save_section(report_id, section_num, section)
                completed_section_titles.append(section.title)

                # Registra log de conclusao da secao
                full_section_content = f"## {section.title}\n\n{section_content}"

                if self.report_logger:
                    self.report_logger.log_section_full_complete(
                        section_title=section.title,
                        section_index=section_num,
                        full_content=full_section_content.strip()
                    )

                logger.info(f"Secao salva: {report_id}/section_{section_num:02d}.md")

                # Atualiza progresso
                ReportManager.update_progress(
                    report_id, "generating",
                    base_progress + int(70 / total_sections),
                    f"Secao {section.title} concluida",
                    current_section=None,
                    completed_sections=completed_section_titles
                )
            
            # Fase 3: Montagem do relatorio completo
            if progress_callback:
                progress_callback("generating", 95, "Montando relatorio completo...")

            ReportManager.update_progress(
                report_id, "generating", 95, "Montando relatorio completo...",
                completed_sections=completed_section_titles
            )
            
            # Usa o ReportManager para montar o relatorio completo
            assembled_content = ReportManager.assemble_full_report(report_id, outline)

            # Fase 4: Analise Estrategica Helena Strategos
            if progress_callback:
                progress_callback("generating", 96, "Helena Strategos analisando...")

            ReportManager.update_progress(
                report_id, "generating", 96,
                "Analise estrategica Helena Strategos em andamento...",
                completed_sections=completed_section_titles
            )

            try:
                helena_analysis = self._generate_helena_analysis(
                    assembled_content, outline
                )
                if helena_analysis:
                    assembled_content += "\n\n---\n\n## Analise Estrategica\n\n" + helena_analysis
                    # Salva como secao adicional
                    helena_section = ReportSection(
                        title="Analise Estrategica",
                        content=helena_analysis
                    )
                    ReportManager.save_section(
                        report_id, total_sections + 1, helena_section
                    )
                    completed_section_titles.append("Analise Estrategica")
                    logger.info(f"Analise Helena concluida para relatorio {report_id}")
            except Exception as e:
                logger.warning(f"Analise Helena falhou (nao-bloqueante): {e}")

            report.markdown_content = assembled_content
            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.now().isoformat()
            
            # Calcula o tempo total
            total_time_seconds = (datetime.now() - start_time).total_seconds()
            
            # Registra log de conclusao do relatorio
            if self.report_logger:
                self.report_logger.log_report_complete(
                    total_sections=total_sections,
                    total_time_seconds=total_time_seconds
                )
            
            # Salva o relatorio final
            ReportManager.save_report(report)
            ReportManager.update_progress(
                report_id, "completed", 100, "Geracao do relatorio concluida",
                completed_sections=completed_section_titles
            )
            
            if progress_callback:
                progress_callback("completed", 100, "Geracao do relatorio concluida")

            logger.info(f"Geracao do relatorio concluida: {report_id}")

            # Fecha o registrador de log de console
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report
            
        except Exception as e:
            logger.error(f"Falha na geracao do relatorio: {str(e)}")
            report.status = ReportStatus.FAILED
            report.error = str(e)
            
            # Registra log de erro
            if self.report_logger:
                self.report_logger.log_error(str(e), "failed")
            
            # Salva o estado de falha
            try:
                ReportManager.save_report(report)
                ReportManager.update_progress(
                    report_id, "failed", -1, f"Falha na geracao do relatorio: {str(e)}",
                    completed_sections=completed_section_titles
                )
            except Exception:
                pass  # Ignora erros ao salvar falha

            # Fecha o registrador de log de console
            if self.console_logger:
                self.console_logger.close()
                self.console_logger = None
            
            return report

    def _generate_helena_analysis(
        self,
        report_content: str,
        outline: ReportOutline,
    ) -> Optional[str]:
        """Gera analise estrategica final usando Helena Strategos com o melhor modelo disponivel.

        Tenta opus-tasks primeiro (Claude Opus 4.6). Se falhar, tenta gpt-5.4-thinking.
        Se falhar, tenta gemini-4.1. Se todos falharem, usa o modelo premium padrao.
        A analise e nao-bloqueante — se falhar completamente, o relatorio segue sem ela.
        """
        # Modelos em ordem de preferencia (melhor → fallback)
        helena_models = [
            Config.LLM_HELENA_MODEL,   # opus-tasks (default)
            'gpt-5.4-thinking',        # GPT-5.4 com thinking
            'gemini-4.1',              # Gemini 4.1
            Config.LLM_PREMIUM_MODEL,  # sonnet-tasks (fallback seguro)
        ]

        # Obter metadados da simulacao
        total_agents = 0
        total_rounds = 0
        platforms = ""
        try:
            from .simulation_manager import SimulationManager
            sim_data = SimulationManager.get_simulation(self.simulation_id)
            if sim_data:
                sim_dict = sim_data if isinstance(sim_data, dict) else sim_data.to_dict()
                total_agents = sim_dict.get("total_agents", 0) or sim_dict.get("agent_count", 0) or 0
                total_rounds = sim_dict.get("total_rounds", 0) or sim_dict.get("max_rounds", 0) or 0
                platforms = ", ".join(sim_dict.get("platforms", [])) or "Twitter/Reddit"
        except Exception:
            pass

        user_prompt = HELENA_USER_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            total_agents=total_agents or "desconhecido",
            total_rounds=total_rounds or "desconhecido",
            platforms=platforms or "desconhecido",
            report_content=report_content[:12000],  # Truncar para caber no contexto
        )

        last_error = None
        for model_name in helena_models:
            resolved = Config.resolve_model_name(model_name)
            try:
                logger.info(f"Helena Strategos: tentando modelo {resolved}")
                helena_llm = LLMClient(model=model_name)
                result = helena_llm.chat(
                    system_prompt=HELENA_SYSTEM_PROMPT,
                    user_message=user_prompt,
                )
                if result and len(result.strip()) > 100:
                    logger.info(f"Helena Strategos: analise gerada com {resolved} ({len(result)} chars)")
                    return result.strip()
                else:
                    logger.warning(f"Helena Strategos: resposta vazia ou curta com {resolved}")
            except Exception as e:
                last_error = e
                logger.warning(f"Helena Strategos: modelo {resolved} falhou: {e}")
                continue

        if last_error:
            logger.error(f"Helena Strategos: todos os modelos falharam. Ultimo erro: {last_error}")
        return None

    def chat(
        self,
        message: str,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Dialogo com o Report Agent

        No dialogo, o Agent pode chamar ferramentas de busca autonomamente para responder perguntas

        Args:
            message: Mensagem do usuario
            chat_history: Historico de conversa

        Returns:
            {
                "response": "Resposta do Agent",
                "tool_calls": [lista de ferramentas chamadas],
                "sources": [fontes de informacao]
            }
        """
        logger.info(f"Dialogo do Report Agent: {message[:50]}...")
        
        chat_history = chat_history or []
        
        # Obtem o conteudo do relatorio ja gerado
        report_content = ""
        try:
            report = ReportManager.get_report_by_simulation(self.simulation_id)
            if report and report.markdown_content:
                # Limita o tamanho do relatorio para evitar contexto muito longo
                report_content = report.markdown_content[:15000]
                if len(report.markdown_content) > 15000:
                    report_content += "\n\n... [Conteudo do relatorio truncado] ..."
        except Exception as e:
            logger.warning(f"Falha ao obter conteudo do relatorio: {e}")
        
        system_prompt = CHAT_SYSTEM_PROMPT_TEMPLATE.format(
            simulation_requirement=self.simulation_requirement,
            report_content=report_content if report_content else "(Nenhum relatorio disponivel no momento)",
            tools_description=self._get_tools_description(),
        )

        # Constroi mensagens
        messages = [{"role": "system", "content": system_prompt}]
        
        # Adiciona historico de conversa
        for h in chat_history[-10:]:  # Limita tamanho do historico
            messages.append(h)
        
        # Adiciona mensagem do usuario
        messages.append({
            "role": "user", 
            "content": message
        })
        
        # Ciclo ReACT (versao simplificada)
        tool_calls_made = []
        max_iterations = 2  # Numero reduzido de rodadas de iteracao
        
        for iteration in range(max_iterations):
            response = self.llm.chat(
                messages=messages,
                temperature=0.5
            )
            
            # Analisa chamadas de ferramenta
            tool_calls = self._parse_tool_calls(response)
            
            if not tool_calls:
                # Sem chamada de ferramenta, retorna a resposta diretamente
                clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', response, flags=re.DOTALL)
                clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
                
                return {
                    "response": clean_response.strip(),
                    "tool_calls": tool_calls_made,
                    "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
                }
            
            # Executa chamadas de ferramenta (com limite de quantidade)
            tool_results = []
            for call in tool_calls[:1]:  # Maximo de 1 chamada de ferramenta por rodada
                if len(tool_calls_made) >= self.MAX_TOOL_CALLS_PER_CHAT:
                    break
                result = self._execute_tool(call["name"], call.get("parameters", {}))
                tool_results.append({
                    "tool": call["name"],
                    "result": result[:1500]  # Limita tamanho do resultado
                })
                tool_calls_made.append(call)
            
            # Adiciona os resultados as mensagens
            messages.append({"role": "assistant", "content": response})
            observation = "\n".join([f"[Resultado {r['tool']}]\n{r['result']}" for r in tool_results])
            messages.append({
                "role": "user",
                "content": observation + CHAT_OBSERVATION_SUFFIX
            })
        
        # Atingiu o maximo de iteracoes, obtem a resposta final
        final_response = self.llm.chat(
            messages=messages,
            temperature=0.5
        )
        
        # Limpa a resposta
        clean_response = re.sub(r'<tool_call>.*?</tool_call>', '', final_response, flags=re.DOTALL)
        clean_response = re.sub(r'\[TOOL_CALL\].*?\)', '', clean_response)
        
        return {
            "response": clean_response.strip(),
            "tool_calls": tool_calls_made,
            "sources": [tc.get("parameters", {}).get("query", "") for tc in tool_calls_made]
        }


class ReportManager:
    """
    Gerenciador de relatorios

    Responsavel pelo armazenamento persistente e recuperacao de relatorios

    Estrutura de arquivos (saida por secao):
    reports/
      {report_id}/
        meta.json          - Metadados e status do relatorio
        outline.json       - Sumario do relatorio
        progress.json      - Progresso da geracao
        section_01.md      - Secao 1
        section_02.md      - Secao 2
        ...
        full_report.md     - Relatorio completo
    """

    # Diretorio de armazenamento de relatorios
    REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'reports')
    
    @classmethod
    def _ensure_reports_dir(cls):
        """Garante que o diretorio raiz de relatorios existe"""
        os.makedirs(cls.REPORTS_DIR, exist_ok=True)
    
    @classmethod
    def _get_report_folder(cls, report_id: str) -> str:
        """Obtem o caminho da pasta do relatorio"""
        return os.path.join(cls.REPORTS_DIR, report_id)
    
    @classmethod
    def _ensure_report_folder(cls, report_id: str) -> str:
        """Garante que a pasta do relatorio existe e retorna o caminho"""
        folder = cls._get_report_folder(report_id)
        os.makedirs(folder, exist_ok=True)
        return folder
    
    @classmethod
    def _get_report_path(cls, report_id: str) -> str:
        """Obtem o caminho do arquivo de metadados do relatorio"""
        return os.path.join(cls._get_report_folder(report_id), "meta.json")
    
    @classmethod
    def _get_report_markdown_path(cls, report_id: str) -> str:
        """Obtem o caminho do arquivo Markdown do relatorio completo"""
        return os.path.join(cls._get_report_folder(report_id), "full_report.md")
    
    @classmethod
    def _get_outline_path(cls, report_id: str) -> str:
        """Obtem o caminho do arquivo de sumario"""
        return os.path.join(cls._get_report_folder(report_id), "outline.json")
    
    @classmethod
    def _get_progress_path(cls, report_id: str) -> str:
        """Obtem o caminho do arquivo de progresso"""
        return os.path.join(cls._get_report_folder(report_id), "progress.json")
    
    @classmethod
    def _get_section_path(cls, report_id: str, section_index: int) -> str:
        """Obtem o caminho do arquivo Markdown da secao"""
        return os.path.join(cls._get_report_folder(report_id), f"section_{section_index:02d}.md")
    
    @classmethod
    def _get_agent_log_path(cls, report_id: str) -> str:
        """Obtem o caminho do arquivo de log do Agent"""
        return os.path.join(cls._get_report_folder(report_id), "agent_log.jsonl")
    
    @classmethod
    def _get_console_log_path(cls, report_id: str) -> str:
        """Obtem o caminho do arquivo de log de console"""
        return os.path.join(cls._get_report_folder(report_id), "console_log.txt")
    
    @classmethod
    def get_console_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        Obtem o conteudo do log de console

        Sao os logs de saida de console durante a geracao do relatorio (INFO, WARNING, etc.),
        diferentes dos logs estruturados do agent_log.jsonl.

        Args:
            report_id: ID do relatorio
            from_line: A partir de qual linha comecar a ler (para obtencao incremental, 0 = desde o inicio)

        Returns:
            {
                "logs": [lista de linhas de log],
                "total_lines": total de linhas,
                "from_line": numero da linha inicial,
                "has_more": se ha mais logs
            }
        """
        log_path = cls._get_console_log_path(report_id)
        
        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }
        
        logs = []
        total_lines = 0
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    # Preserva a linha de log original, removendo quebra de linha no final
                    logs.append(line.rstrip('\n\r'))
        
        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # Ja leu ate o final
        }

    @classmethod
    def get_console_log_stream(cls, report_id: str) -> List[str]:
        """
        Obtem o log de console completo (obtencao unica de tudo)

        Args:
            report_id: ID do relatorio

        Returns:
            Lista de linhas de log
        """
        result = cls.get_console_log(report_id, from_line=0)
        return result["logs"]
    
    @classmethod
    def get_agent_log(cls, report_id: str, from_line: int = 0) -> Dict[str, Any]:
        """
        Obtem o conteudo do log do Agent

        Args:
            report_id: ID do relatorio
            from_line: A partir de qual linha comecar a ler (para obtencao incremental, 0 = desde o inicio)

        Returns:
            {
                "logs": [lista de entradas de log],
                "total_lines": total de linhas,
                "from_line": numero da linha inicial,
                "has_more": se ha mais logs
            }
        """
        log_path = cls._get_agent_log_path(report_id)
        
        if not os.path.exists(log_path):
            return {
                "logs": [],
                "total_lines": 0,
                "from_line": 0,
                "has_more": False
            }
        
        logs = []
        total_lines = 0
        
        with open(log_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i >= from_line:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        # Pula linhas com falha de parse
                        continue
        
        return {
            "logs": logs,
            "total_lines": total_lines,
            "from_line": from_line,
            "has_more": False  # Ja leu ate o final
        }

    @classmethod
    def get_agent_log_stream(cls, report_id: str) -> List[Dict[str, Any]]:
        """
        Obtem o log completo do Agent (obtencao unica de tudo)

        Args:
            report_id: ID do relatorio

        Returns:
            Lista de entradas de log
        """
        result = cls.get_agent_log(report_id, from_line=0)
        return result["logs"]
    
    @classmethod
    def save_outline(cls, report_id: str, outline: ReportOutline) -> None:
        """
        Salva o sumario do relatorio

        Chamado imediatamente apos a conclusao da fase de planejamento
        """
        cls._ensure_report_folder(report_id)
        
        with open(cls._get_outline_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(outline.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Sumario salvo: {report_id}")
    
    @classmethod
    def save_section(
        cls,
        report_id: str,
        section_index: int,
        section: ReportSection
    ) -> str:
        """
        Salva uma unica secao

        Chamado imediatamente apos a geracao de cada secao, implementando saida por secao

        Args:
            report_id: ID do relatorio
            section_index: Indice da secao (comecando em 1)
            section: Objeto da secao

        Returns:
            Caminho do arquivo salvo
        """
        cls._ensure_report_folder(report_id)

        # Constroi conteudo Markdown da secao - limpa possiveis titulos duplicados
        cleaned_content = cls._clean_section_content(section.content, section.title)
        md_content = f"## {section.title}\n\n"
        if cleaned_content:
            md_content += f"{cleaned_content}\n\n"

        # Salva o arquivo
        file_suffix = f"section_{section_index:02d}.md"
        file_path = os.path.join(cls._get_report_folder(report_id), file_suffix)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Secao salva: {report_id}/{file_suffix}")
        return file_path
    
    @classmethod
    def _clean_section_content(cls, content: str, section_title: str) -> str:
        """
        Limpa o conteudo da secao

        1. Remove linhas de titulo Markdown duplicadas com o titulo da secao no inicio do conteudo
        2. Converte todos os titulos de nivel ### e inferior em texto em negrito

        Args:
            content: Conteudo original
            section_title: Titulo da secao

        Returns:
            Conteudo limpo
        """
        import re
        
        if not content:
            return content
        
        content = content.strip()
        lines = content.split('\n')
        cleaned_lines = []
        skip_next_empty = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Verifica se e uma linha de titulo Markdown
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            
            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2).strip()
                
                # Verifica se e um titulo duplicado com o titulo da secao (pula duplicatas dentro das primeiras 5 linhas)
                if i < 5:
                    if title_text == section_title or title_text.replace(' ', '') == section_title.replace(' ', ''):
                        skip_next_empty = True
                        continue
                
                # Converte todos os niveis de titulo (#, ##, ###, ####, etc.) em negrito
                # Pois o titulo da secao e adicionado pelo sistema, o conteudo nao deve ter nenhum titulo
                cleaned_lines.append(f"**{title_text}**")
                cleaned_lines.append("")  # Adiciona linha em branco
                continue
            
            # Se a linha anterior foi um titulo pulado e a linha atual esta vazia, pula tambem
            if skip_next_empty and stripped == '':
                skip_next_empty = False
                continue
            
            skip_next_empty = False
            cleaned_lines.append(line)
        
        # Remove linhas em branco do inicio
        while cleaned_lines and cleaned_lines[0].strip() == '':
            cleaned_lines.pop(0)
        
        # Remove linhas separadoras do inicio
        while cleaned_lines and cleaned_lines[0].strip() in ['---', '***', '___']:
            cleaned_lines.pop(0)
            # Remove tambem linhas em branco apos a linha separadora
            while cleaned_lines and cleaned_lines[0].strip() == '':
                cleaned_lines.pop(0)
        
        return '\n'.join(cleaned_lines)
    
    @classmethod
    def update_progress(
        cls, 
        report_id: str, 
        status: str, 
        progress: int, 
        message: str,
        current_section: str = None,
        completed_sections: List[str] = None
    ) -> None:
        """
        Atualiza o progresso da geracao do relatorio

        O frontend pode obter o progresso em tempo real lendo o progress.json
        """
        cls._ensure_report_folder(report_id)
        
        progress_data = {
            "status": status,
            "progress": progress,
            "message": message,
            "current_section": current_section,
            "completed_sections": completed_sections or [],
            "updated_at": datetime.now().isoformat()
        }
        
        with open(cls._get_progress_path(report_id), 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def get_progress(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """Obtem o progresso da geracao do relatorio"""
        path = cls._get_progress_path(report_id)
        
        if not os.path.exists(path):
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @classmethod
    def get_generated_sections(cls, report_id: str) -> List[Dict[str, Any]]:
        """
        Obtem a lista de secoes ja geradas

        Retorna informacoes de todos os arquivos de secao ja salvos
        """
        folder = cls._get_report_folder(report_id)
        
        if not os.path.exists(folder):
            return []
        
        sections = []
        for filename in sorted(os.listdir(folder)):
            if filename.startswith('section_') and filename.endswith('.md'):
                file_path = os.path.join(folder, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extrai o indice da secao do nome do arquivo
                parts = filename.replace('.md', '').split('_')
                section_index = int(parts[1])

                sections.append({
                    "filename": filename,
                    "section_index": section_index,
                    "content": content
                })

        return sections
    
    @classmethod
    def assemble_full_report(cls, report_id: str, outline: ReportOutline) -> str:
        """
        Monta o relatorio completo

        Monta o relatorio completo a partir dos arquivos de secao ja salvos, com limpeza de titulos
        """
        folder = cls._get_report_folder(report_id)
        
        # Constroi o cabecalho do relatorio
        md_content = f"# {outline.title}\n\n"
        md_content += f"> {outline.summary}\n\n"
        md_content += f"---\n\n"
        
        # Le todos os arquivos de secao em ordem
        sections = cls.get_generated_sections(report_id)
        for section_info in sections:
            md_content += section_info["content"]
        
        # Pos-processamento: limpa problemas de titulos no relatorio inteiro
        md_content = cls._post_process_report(md_content, outline)
        
        # Salva o relatorio completo
        full_path = cls._get_report_markdown_path(report_id)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Relatorio completo montado: {report_id}")
        return md_content
    
    @classmethod
    def _post_process_report(cls, content: str, outline: ReportOutline) -> str:
        """
        Pos-processa o conteudo do relatorio

        1. Remove titulos duplicados
        2. Mantem o titulo principal do relatorio (#) e titulos de secao (##), remove outros niveis (###, ####, etc.)
        3. Limpa linhas em branco e separadores excessivos

        Args:
            content: Conteudo original do relatorio
            outline: Sumario do relatorio

        Returns:
            Conteudo processado
        """
        import re
        
        lines = content.split('\n')
        processed_lines = []
        prev_was_heading = False
        
        # Coleta todos os titulos de secao do sumario
        section_titles = set()
        for section in outline.sections:
            section_titles.add(section.title)
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Verifica se e uma linha de titulo
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
            
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                # Verifica se e um titulo duplicado (titulo com mesmo conteudo aparecendo dentro de 5 linhas consecutivas)
                is_duplicate = False
                for j in range(max(0, len(processed_lines) - 5), len(processed_lines)):
                    prev_line = processed_lines[j].strip()
                    prev_match = re.match(r'^(#{1,6})\s+(.+)$', prev_line)
                    if prev_match:
                        prev_title = prev_match.group(2).strip()
                        if prev_title == title:
                            is_duplicate = True
                            break
                
                if is_duplicate:
                    # Pula o titulo duplicado e as linhas em branco que o seguem
                    i += 1
                    while i < len(lines) and lines[i].strip() == '':
                        i += 1
                    continue
                
                # Tratamento de hierarquia de titulos:
                # - # (level=1) mantem apenas o titulo principal do relatorio
                # - ## (level=2) mantem titulos de secao
                # - ### e abaixo (level>=3) converte para texto em negrito
                
                if level == 1:
                    if title == outline.title:
                        # Mantem o titulo principal do relatorio
                        processed_lines.append(line)
                        prev_was_heading = True
                    elif title in section_titles:
                        # Titulo de secao usou # incorretamente, corrige para ##
                        processed_lines.append(f"## {title}")
                        prev_was_heading = True
                    else:
                        # Outros titulos de nivel 1 convertem para negrito
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                elif level == 2:
                    if title in section_titles or title == outline.title:
                        # Mantem titulo de secao
                        processed_lines.append(line)
                        prev_was_heading = True
                    else:
                        # Titulos de nivel 2 que nao sao de secao convertem para negrito
                        processed_lines.append(f"**{title}**")
                        processed_lines.append("")
                        prev_was_heading = False
                else:
                    # Titulos de nivel ### e abaixo convertem para texto em negrito
                    processed_lines.append(f"**{title}**")
                    processed_lines.append("")
                    prev_was_heading = False
                
                i += 1
                continue
            
            elif stripped == '---' and prev_was_heading:
                # Pula linha separadora que segue imediatamente um titulo
                i += 1
                continue
            
            elif stripped == '' and prev_was_heading:
                # Mantem apenas uma linha em branco apos o titulo
                if processed_lines and processed_lines[-1].strip() != '':
                    processed_lines.append(line)
                prev_was_heading = False
            
            else:
                processed_lines.append(line)
                prev_was_heading = False
            
            i += 1
        
        # Limpa multiplas linhas em branco consecutivas (mantem no maximo 2)
        result_lines = []
        empty_count = 0
        for line in processed_lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:
                    result_lines.append(line)
            else:
                empty_count = 0
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    @classmethod
    def save_report(cls, report: Report) -> None:
        """Salva metadados e relatorio completo"""
        cls._ensure_report_folder(report.report_id)
        
        # Salva o JSON de metadados
        with open(cls._get_report_path(report.report_id), 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        # Salva o sumario
        if report.outline:
            cls.save_outline(report.report_id, report.outline)
        
        # Salva o relatorio Markdown completo
        if report.markdown_content:
            with open(cls._get_report_markdown_path(report.report_id), 'w', encoding='utf-8') as f:
                f.write(report.markdown_content)
        
        logger.info(f"Relatorio salvo: {report.report_id}")
    
    @classmethod
    def get_report(cls, report_id: str) -> Optional[Report]:
        """Obtem o relatorio"""
        path = cls._get_report_path(report_id)
        
        if not os.path.exists(path):
            # Compatibilidade com formato antigo: verifica arquivos armazenados diretamente no diretorio reports
            old_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
            if os.path.exists(old_path):
                path = old_path
            else:
                return None
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstroi o objeto Report
        outline = None
        if data.get('outline'):
            outline_data = data['outline']
            sections = []
            for s in outline_data.get('sections', []):
                sections.append(ReportSection(
                    title=s['title'],
                    content=s.get('content', '')
                ))
            outline = ReportOutline(
                title=outline_data['title'],
                summary=outline_data['summary'],
                sections=sections
            )
        
        # Se markdown_content estiver vazio, tenta ler de full_report.md
        markdown_content = data.get('markdown_content', '')
        if not markdown_content:
            full_report_path = cls._get_report_markdown_path(report_id)
            if os.path.exists(full_report_path):
                with open(full_report_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
        
        return Report(
            report_id=data['report_id'],
            simulation_id=data['simulation_id'],
            graph_id=data['graph_id'],
            simulation_requirement=data['simulation_requirement'],
            status=ReportStatus(data['status']),
            outline=outline,
            markdown_content=markdown_content,
            created_at=data.get('created_at', ''),
            completed_at=data.get('completed_at', ''),
            error=data.get('error')
        )
    
    @classmethod
    def get_report_by_simulation(cls, simulation_id: str) -> Optional[Report]:
        """Obtem o relatorio pelo ID da simulacao"""
        cls._ensure_reports_dir()
        
        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            # Formato novo: pasta
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report and report.simulation_id == simulation_id:
                    return report
            # Compatibilidade com formato antigo: arquivo JSON
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report and report.simulation_id == simulation_id:
                    return report
        
        return None
    
    @classmethod
    def list_reports(cls, simulation_id: Optional[str] = None, limit: int = 50) -> List[Report]:
        """Lista relatorios"""
        cls._ensure_reports_dir()
        
        reports = []
        for item in os.listdir(cls.REPORTS_DIR):
            item_path = os.path.join(cls.REPORTS_DIR, item)
            # Formato novo: pasta
            if os.path.isdir(item_path):
                report = cls.get_report(item)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)
            # Compatibilidade com formato antigo: arquivo JSON
            elif item.endswith('.json'):
                report_id = item[:-5]
                report = cls.get_report(report_id)
                if report:
                    if simulation_id is None or report.simulation_id == simulation_id:
                        reports.append(report)

        # Ordena por data de criacao (mais recente primeiro)
        reports.sort(key=lambda r: r.created_at, reverse=True)
        
        return reports[:limit]
    
    @classmethod
    def delete_report(cls, report_id: str) -> bool:
        """Exclui o relatorio (pasta inteira)"""
        import shutil
        
        folder_path = cls._get_report_folder(report_id)
        
        # Formato novo: exclui a pasta inteira
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            logger.info(f"Pasta do relatorio excluida: {report_id}")
            return True
        
        # Compatibilidade com formato antigo: exclui arquivos individuais
        deleted = False
        old_json_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.json")
        old_md_path = os.path.join(cls.REPORTS_DIR, f"{report_id}.md")
        
        if os.path.exists(old_json_path):
            os.remove(old_json_path)
            deleted = True
        if os.path.exists(old_md_path):
            os.remove(old_md_path)
            deleted = True
        
        return deleted
