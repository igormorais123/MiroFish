"""Fabrica da aplicacao Flask do MiroFish-Inteia."""

import os
import warnings

# Suprime warnings ruidosos de libs de terceiros em ambientes Windows/Linux.
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request, send_from_directory, abort
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


_PRODUCTION_CORS_ORIGINS = (
    'https://inteia.com.br',
    'https://mirofish-inteia.vercel.app',
)

_DEVELOPMENT_CORS_ORIGINS = (
    'http://localhost:3000',
    'http://127.0.0.1:3000',
)


def _resolve_cors_origins(debug_mode: bool):
    """Resolve CORS sem wildcard implicito em ambientes publicos."""
    configured = os.environ.get('CORS_ORIGINS')
    if configured is not None:
        origins = [origin.strip() for origin in configured.split(',') if origin.strip()]
        return origins or _PRODUCTION_CORS_ORIGINS

    if debug_mode:
        return _PRODUCTION_CORS_ORIGINS + _DEVELOPMENT_CORS_ORIGINS
    return _PRODUCTION_CORS_ORIGINS


def create_app(config_class=Config):
    """Cria e configura a aplicacao Flask."""
    # Serve frontend/dist como static se existir (evita CORS em dev local)
    _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    _frontend_dist = os.path.join(_project_root, 'frontend', 'dist')
    _has_frontend = os.path.isdir(_frontend_dist) and os.path.exists(os.path.join(_frontend_dist, 'index.html'))
    if _has_frontend:
        app = Flask(__name__, static_folder=_frontend_dist, static_url_path='')
    else:
        app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Mantem JSON legivel sem escape ASCII agressivo.
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # Logs
    logger = setup_logger('mirofish')
    
    # Evita log duplicado no reloader do Flask.
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info(f"{Config.APP_NAME} backend iniciando...")
        logger.info("=" * 50)

    # Aviso quando SECRET_KEY foi gerada em runtime (fallback) com debug desligado.
    # Em producao isso quebra sessoes apos reinicio e dessincroniza multiplos workers.
    if not debug_mode and getattr(Config, 'SECRET_KEY_FROM_FALLBACK', False):
        logger.warning(
            "SECRET_KEY nao definida em ambiente — usando fallback aleatorio. "
            "Defina SECRET_KEY ou FLASK_SECRET_KEY como segredo persistente em producao."
        )

    # CORS - restringe origens por padrao; use CORS_ORIGINS para sobrescrever.
    allowed_origins = _resolve_cors_origins(debug_mode)
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
    
    # Garante limpeza dos processos de simulacao em desligamentos.
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Cleanup de simulacoes registrado")
    
    # Middleware de log
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(
            "Requisicao: "
            f"{request.method} {request.path} "
            f"content_type={request.content_type or '-'} "
            f"content_length={request.content_length or 0}"
        )
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"Resposta: {response.status_code}")
        # Headers de seguranca no nivel Flask (complementa nginx)
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        return response
    
    # Blueprints
    from .api import graph_bp, simulation_bp, report_bp, internal_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(internal_bp, url_prefix='/api/internal/v1')
    
    def _public_health_payload():
        return {
            'status': 'ok',
            'service': app.config.get('APP_NAME', Config.APP_NAME),
            'code': app.config.get('APP_CODE', Config.APP_CODE),
            'has_frontend': _has_frontend,
        }

    # Healthcheck publico: sem URL/modelo/chaves ou detalhes de infra.
    @app.route('/health')
    @app.route('/health/public')
    def health():
        return _public_health_payload()

    @app.route('/health/internal')
    def health_internal():
        expected_token = app.config.get('INTERNAL_API_TOKEN', Config.INTERNAL_API_TOKEN).strip()
        provided_token = request.headers.get('X-Internal-Token', '').strip()
        if not expected_token or provided_token != expected_token:
            return {'success': False, 'error': 'Nao autorizado para health interno'}, 401

        from .utils.graphiti_client import GraphitiClient

        graphiti = GraphitiClient(timeout=2).status()
        return {
            'success': True,
            'data': {
                'status': 'ok',
                'service': app.config.get('APP_NAME', Config.APP_NAME),
                'code': app.config.get('APP_CODE', Config.APP_CODE),
                'has_frontend': _has_frontend,
                'llm_base_url': app.config.get('LLM_BASE_URL', Config.LLM_BASE_URL),
                'llm_model': app.config.get('LLM_MODEL_NAME', Config.LLM_MODEL_NAME),
                'graphiti': graphiti,
            },
        }

    # SPA fallback: serve index.html para rotas nao-API quando frontend/dist existe
    if _has_frontend:
        @app.route('/')
        def _frontend_root():
            return send_from_directory(_frontend_dist, 'index.html')

        @app.route('/<path:path>')
        def _frontend_catch(path):
            if path.startswith('api/') or path == 'health':
                abort(404)
            full = os.path.join(_frontend_dist, path)
            if os.path.isfile(full):
                return send_from_directory(_frontend_dist, path)
            return send_from_directory(_frontend_dist, 'index.html')

    if should_log_startup:
        logger.info(f"{Config.APP_NAME} backend pronto (frontend={'on' if _has_frontend else 'off'})")
    
    return app

