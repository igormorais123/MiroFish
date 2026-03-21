"""
Modulo de configuracao de logs
Fornece gerenciamento unificado de logs, com saida simultanea para console e arquivo
"""

import os
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


def _ensure_utf8_stdout():
    """
    Garantir que stdout/stderr usem codificacao UTF-8
    Resolve problemas de caracteres especiais no console Windows
    """
    if sys.platform == 'win32':
        # No Windows, reconfigurar saida padrao para UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# Diretorio de logs
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')


def setup_logger(name: str = 'mirofish', level: int = logging.DEBUG) -> logging.Logger:
    """
    Configurar logger

    Args:
        name: Nome do logger
        level: Nivel de log

    Returns:
        Logger configurado
    """
    # Garantir que o diretorio de logs exista
    os.makedirs(LOG_DIR, exist_ok=True)

    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Impedir propagacao para o logger raiz, evitando saida duplicada
    logger.propagate = False

    # Se ja possui handlers, nao adicionar novamente
    if logger.handlers:
        return logger

    # Formato de log
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    # 1. Handler de arquivo - log detalhado (nomeado por data, com rotacao)
    log_filename = datetime.now().strftime('%Y-%m-%d') + '.log'
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, log_filename),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # 2. Handler de console - log simplificado (INFO e acima)
    # Garantir codificacao UTF-8 no Windows para evitar caracteres especiais ilegveis
    _ensure_utf8_stdout()
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # Adicionar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = 'mirofish') -> logging.Logger:
    """
    Obter logger (cria se nao existir)

    Args:
        name: Nome do logger

    Returns:
        Instancia do logger
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


# Criar logger padrao
logger = setup_logger()


# Metodos de conveniencia
def debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    logger.info(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    logger.warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    logger.critical(msg, *args, **kwargs)
