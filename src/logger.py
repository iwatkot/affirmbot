import logging
import os
import sys
from datetime import datetime

LOG_LEVEL = os.getenv("LOG_LEVEL", logging.DEBUG)
LOG_FORMATTER = "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


class Logger(logging.getLoggerClass()):
    """Handles logging to the file and stroudt with timestamps."""

    def __init__(
        self,
        name: str,
        level: logging.DEBUG | logging.INFO | logging.WARNING | logging.ERROR = None,
        log_dir: str = None,
    ):
        super().__init__(name)
        self.log_dir = log_dir or LOG_DIR
        self.setLevel(level or LOG_LEVEL)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.file_handler = logging.FileHandler(
            filename=self.log_file(), mode="a", encoding="utf-8"
        )
        self.fmt = LOG_FORMATTER
        self.stdout_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
        self.file_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
        self.addHandler(self.stdout_handler)
        self.addHandler(self.file_handler)

    def log_file(self):
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"{today}.txt")
        return log_file
