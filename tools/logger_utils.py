import logging
import os
import uuid
from pathlib import Path
from contextvars import ContextVar

run_id_var = ContextVar("run_id", default="no-run")

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"

def set_run_id(run_id: str | None = None) -> str:
    value = run_id or str(uuid.uuid4())
    run_id_var.set(value)
    return value

def get_run_id() -> str:
    return run_id_var.get()

class RunIdFilter(logging.Filter):
    def filter(self, record):
        record.run_id = get_run_id()
        return True

def get_logger(name: str, log_file: str = "workflow.log") -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | run_id=%(run_id)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(LOG_DIR / log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RunIdFilter())

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RunIdFilter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
