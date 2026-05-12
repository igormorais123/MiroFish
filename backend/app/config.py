"""
Gerenciamento central de configuracao.

Carrega variaveis de ambiente a partir do `.env` na raiz do projeto e aplica
defaults compativeis com a integracao da INTEIA.
"""

import json
import os
import secrets

from dotenv import load_dotenv

# Carrega o `.env` da raiz do projeto.
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=False)
else:
    # Fallback para ambientes onde as variaveis ja foram injetadas externamente.
    load_dotenv(override=False)


def _first_non_empty(*values):
    """Retorna o primeiro valor nao vazio."""
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return None


def _env_flag(name: str, default: bool = False) -> bool:
    """Le booleanos de ambiente com default seguro."""
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _default_llm_base_url() -> str:
    """Escolhe o gateway padrao de LLM priorizando OmniRoute."""
    return _first_non_empty(
        os.environ.get('LLM_BASE_URL'),
        os.environ.get('OMNIROUTE_URL') and f"{os.environ.get('OMNIROUTE_URL').rstrip('/')}/v1",
        'https://api.openai.com/v1',
    ) or 'https://api.openai.com/v1'


def _default_llm_api_key():
    """Escolhe a chave padrao de LLM priorizando o token operacional da INTEIA."""
    return _first_non_empty(
        os.environ.get('LLM_API_KEY'),
        os.environ.get('OMNIROUTE_API_KEY'),
    )


def _default_llm_model_name() -> str:
    """Escolhe o modelo padrao conforme o gateway configurado."""
    explicit_model = _first_non_empty(os.environ.get('LLM_MODEL_NAME'))
    if explicit_model:
        return explicit_model

    base_url = _default_llm_base_url().lower()
    if 'omniroute' in base_url:
        return 'haiku-tasks'
    return 'gpt-4o-mini'


def _parse_alias_map() -> dict:
    """
    Le um mapa opcional de aliases de modelos.

    Formatos aceitos:
    - JSON: {"helena-premium":"cc/claude-sonnet-4-6"}
    - CSV simples: alias=modelo,alias2=modelo2
    """
    raw_value = os.environ.get('LLM_MODEL_ALIASES', '').strip()
    if not raw_value:
        return {}

    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
    except json.JSONDecodeError:
        pass

    aliases = {}
    for pair in raw_value.split(','):
        if '=' not in pair:
            continue
        alias, model = pair.split('=', 1)
        alias = alias.strip()
        model = model.strip()
        if alias and model:
            aliases[alias] = model
    return aliases


class Config:
    """Configuracao principal do backend Flask."""

    # Identidade da aplicacao
    APP_NAME = os.environ.get('APP_NAME', 'MiroFish-Inteia')
    APP_CODE = os.environ.get('APP_CODE', 'mirofish-inteia')

    # Flask
    _SECRET_KEY_FROM_ENV = _first_non_empty(
        os.environ.get('SECRET_KEY'), os.environ.get('FLASK_SECRET_KEY')
    )
    SECRET_KEY = _SECRET_KEY_FROM_ENV or secrets.token_hex(32)
    # True quando a chave foi gerada em runtime — sessoes/CSRF nao sobrevivem a
    # reinicializacao nem sincronizam entre multiplos workers gunicorn.
    SECRET_KEY_FROM_FALLBACK = _SECRET_KEY_FROM_ENV is None
    DEBUG = _env_flag('FLASK_DEBUG', False)

    # JSON
    JSON_AS_ASCII = False

    # LLM
    LLM_API_KEY = _default_llm_api_key()
    LLM_BASE_URL = _default_llm_base_url()
    LLM_MODEL_NAME = _default_llm_model_name()
    LLM_TIMEOUT_SECONDS = float(os.environ.get('LLM_TIMEOUT_SECONDS', '90'))
    LLM_MAX_RETRIES = int(os.environ.get('LLM_MAX_RETRIES', '8'))
    LLM_MODEL_ALIASES = _parse_alias_map()

    # Modelo para acoes de agentes na simulacao (barato, rapido)
    LLM_AGENT_MODEL = os.environ.get('LLM_AGENT_MODEL', 'haiku-tasks')
    # Modelo para relatorios, ontologia e analises complexas (premium)
    LLM_PREMIUM_MODEL = os.environ.get('LLM_PREMIUM_MODEL', 'sonnet-tasks')
    # Modelo Helena Strategos — maximo poder analitico (opus-4.6, gpt-5.4-thinking, gemini-4.1)
    LLM_HELENA_MODEL = os.environ.get('LLM_HELENA_MODEL', 'opus-tasks')

    # Gateway interno INTEIA / OmniRoute
    OMNIROUTE_URL = os.environ.get('OMNIROUTE_URL', '')
    OMNIROUTE_API_KEY = os.environ.get('OMNIROUTE_API_KEY', '')

    # Graphiti Server (backend de grafo de memoria temporal)
    GRAPHITI_BASE_URL = os.environ.get('GRAPHITI_BASE_URL', 'http://localhost:8003')
    GRAPHITI_TIMEOUT = int(os.environ.get('GRAPHITI_TIMEOUT', '60'))
    GRAPHITI_REQUIRED = os.environ.get('GRAPHITI_REQUIRED', 'false').lower() == 'true'

    # Auth entre servicos
    INTERNAL_API_TOKEN = os.environ.get('INTERNAL_API_TOKEN', '')

    # Upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # Texto
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    # OASIS
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    # Acoes por plataforma
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))
    REPORT_MIN_ACTIONS = int(os.environ.get('REPORT_MIN_ACTIONS', '10'))
    REPORT_REQUIRE_COMPLETED_SIMULATION = os.environ.get('REPORT_REQUIRE_COMPLETED_SIMULATION', 'true').lower() == 'true'
    REPORT_REQUIRE_SOURCE_TEXT = os.environ.get('REPORT_REQUIRE_SOURCE_TEXT', 'true').lower() == 'true'
    REPORT_FAIL_ON_UNSUPPORTED_QUOTES = os.environ.get('REPORT_FAIL_ON_UNSUPPORTED_QUOTES', 'true').lower() == 'true'
    REPORT_MIN_DISTINCT_2 = float(os.environ.get('REPORT_MIN_DISTINCT_2', '0.30'))
    REPORT_MIN_AGENT_ACTIVITY_ENTROPY = float(os.environ.get('REPORT_MIN_AGENT_ACTIVITY_ENTROPY', '0.25'))
    REPORT_MIN_BEHAVIOR_ENTROPY = float(os.environ.get('REPORT_MIN_BEHAVIOR_ENTROPY', '0.20'))
    REPORT_REQUIRE_ACTION_TYPE_DIVERSITY = os.environ.get('REPORT_REQUIRE_ACTION_TYPE_DIVERSITY', 'true').lower() == 'true'
    REPORT_DELIVERY_MODE = os.environ.get('REPORT_DELIVERY_MODE', 'client').strip().lower()
    REPORT_DEMO_MIN_ACTIONS = int(os.environ.get('REPORT_DEMO_MIN_ACTIONS', '3'))
    REPORT_DEMO_REQUIRE_COMPLETED_SIMULATION = (
        os.environ.get('REPORT_DEMO_REQUIRE_COMPLETED_SIMULATION', 'false').lower() == 'true'
    )
    REPORT_DEMO_REQUIRE_SOURCE_TEXT = os.environ.get('REPORT_DEMO_REQUIRE_SOURCE_TEXT', 'false').lower() == 'true'
    REPORT_FAIL_ON_UNSUPPORTED_NUMBERS = (
        os.environ.get('REPORT_FAIL_ON_UNSUPPORTED_NUMBERS', 'true').lower() == 'true'
    )

    @classmethod
    def resolve_model_name(cls, model_name=None) -> str:
        """Resolve aliases internos de modelo para o nome real a ser chamado."""
        candidate = (model_name or cls.LLM_MODEL_NAME or '').strip()
        if not candidate:
            return cls.LLM_MODEL_NAME
        return cls.LLM_MODEL_ALIASES.get(candidate, candidate)

    @classmethod
    def validate(cls):
        """Valida configuracoes obrigatorias para o backend."""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY ou OMNIROUTE_API_KEY nao configurada")
        if not cls.GRAPHITI_BASE_URL:
            errors.append("GRAPHITI_BASE_URL nao configurada")
        return errors
