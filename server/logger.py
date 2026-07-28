import logging
import sys
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# Reference to active state container for real-time web console streaming
_global_state_ref = None

def set_global_state_ref(state: dict):
    global _global_state_ref
    _global_state_ref = state


class WebStreamHandler(logging.Handler):
    """Custom Log Handler that streams all internal Playwright logger statements to the web UI console!"""
    def emit(self, record):
        try:
            msg = self.format(record)
            if _global_state_ref and "logs" in _global_state_ref:
                log_entry = {
                    "log": f"[{record.levelname}] {record.getMessage()}",
                    "metrics": {
                        "completed": _global_state_ref["progress"]["completed"],
                        "failed": _global_state_ref["progress"]["failed"],
                        "total": _global_state_ref["progress"]["total"]
                    }
                }
                _global_state_ref["logs"].append(log_entry)
        except Exception:
            pass


class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.CYAN + "%(asctime)s [%(levelname)s] %(message)s" + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + "%(asctime)s [%(levelname)s] %(message)s" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + "%(asctime)s [%(levelname)s] %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "%(asctime)s [%(levelname)s] %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + "%(asctime)s [%(levelname)s] %(message)s" + Style.RESET_ALL,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "%(asctime)s [%(levelname)s] %(message)s")
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(log_file_path: Path = None) -> logging.Logger:
    logger = logging.getLogger("AutoFormPlatform")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)

    web_handler = WebStreamHandler()
    logger.addHandler(web_handler)

    if log_file_path:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger(Path(__file__).resolve().parent / "logs" / "automation.log")


def print_success(msg: str):
    logger.info(f"✔ {msg}")


def print_failure(msg: str):
    logger.error(f"✘ {msg}")


def print_warning(msg: str):
    logger.warning(f"⚠ {msg}")
