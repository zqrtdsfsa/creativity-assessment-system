import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

_LOG_DIR = os.path.join(os.getcwd(), "log")
_APP_LOG_FILE = os.path.join(_LOG_DIR, "app.log")
_LLM_LOG_FILE = os.path.join(_LOG_DIR, "llm.log")

_DEF_FMT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

_initialized = False


def _ensure_dir() -> None:
    if not os.path.isdir(_LOG_DIR):
        os.makedirs(_LOG_DIR, exist_ok=True)


def _build_handler(filepath: str) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(filepath, when="midnight", interval=1, backupCount=7, encoding="utf-8")
    formatter = logging.Formatter(_DEF_FMT)
    handler.setFormatter(formatter)
    return handler


def _init_root() -> None:
    global _initialized
    if _initialized:
        return
    _ensure_dir()
    logging.basicConfig(level=logging.INFO, format=_DEF_FMT)
    _initialized = True


def get_app_logger(name: Optional[str] = None) -> logging.Logger:
    _init_root()
    logger_name = name or "app"
    logger = logging.getLogger(logger_name)
    # 防止重复添加 handler
    if not any(isinstance(h, TimedRotatingFileHandler) and getattr(h, "baseFilename", "").endswith("app.log") for h in logger.handlers):
        handler = _build_handler(_APP_LOG_FILE)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def get_llm_logger(name: Optional[str] = None) -> logging.Logger:
    _init_root()
    logger_name = name or "llm"
    logger = logging.getLogger(logger_name)
    if not any(isinstance(h, TimedRotatingFileHandler) and getattr(h, "baseFilename", "").endswith("llm.log") for h in logger.handlers):
        handler = _build_handler(_LLM_LOG_FILE)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
