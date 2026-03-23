"""Fabrica da aplicacao Flask do MiroFish-Inteia."""

import os
import warnings

# Suprime warnings ruidosos de libs de terceiros em ambientes Windows/Linux.
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Cria e configura a aplicacao Flask."""
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
    
    # CORS — restringe origens em producao
    allowed_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
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
        logger.debug(f"Requisicao: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Corpo da requisicao: {request.get_json(silent=True)}")
    
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
    
    # Healthcheck
    @app.route('/health')
    def health():
        return {
            'status': 'ok',
            'service': Config.APP_NAME,
            'code': Config.APP_CODE,
            'llm_base_url': Config.LLM_BASE_URL,
            'llm_model': Config.LLM_MODEL_NAME,
        }
    
    if should_log_startup:
        logger.info(f"{Config.APP_NAME} backend pronto")
    
    return app

