import logging
import os
import shutil
import sys
import traceback
from datetime import datetime

from src.utils import make_dirs

LOG_LEVEL = os.getenv("LOG_LEVEL", logging.DEBUG)
LOG_FORMATTER = "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
LOG_DIR = os.path.join(os.getcwd(), "logs")
TB_DIR = os.path.join(LOG_DIR, "tracebacks")
ARCHIVES_DIR = os.path.join(LOG_DIR, "archives")
make_dirs([LOG_DIR, TB_DIR, ARCHIVES_DIR])


class Logger(logging.getLoggerClass()):
    """Handles logging to the file and stroudt with timestamps."""

    def __init__(
        self,
        name: str,
        level: str = None,
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

    def dump_traceback(self, tb: traceback) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = os.path.join(TB_DIR, f"{timestamp}.txt")
        with open(save_path, "w") as f:
            f.write(tb)

        self.info(f"Traceback saved to {save_path}")

    def archive_logs(self) -> str:
        save_path = os.path.join(ARCHIVES_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.zip")
        shutil.make_archive(save_path, "zip", self.log_dir)
        return save_path
