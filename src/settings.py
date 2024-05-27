from __future__ import annotations

import json
import os
from functools import wraps

from src.config import Config
from src.globals import ADMINS, SETTINGS_JSON
from src.logger import Logger
from src.template import Template
from src.utils import Singleton

logger = Logger(__name__)


class Settings(metaclass=Singleton):
    def __init__(self, admins: list[int] | None = None, channel: int | None = None) -> None:
        if not admins:
            admins = ADMINS
        self._admins = admins
        self._templates = Config().templates
        for idx, template in enumerate(self._templates):
            template.idx = idx
        self._channel = channel

    def dump(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            with open(SETTINGS_JSON, "w") as f:
                json.dump(self.to_json(), f, indent=4)
            logger.info(f"Settings saved to {SETTINGS_JSON}")
            return result

        return wrapper

    @property
    def admins(self) -> list[int]:
        return self._admins.copy()

    @dump
    def add_admin(self, user_id: int) -> None:
        if user_id not in self._admins:
            self._admins.append(user_id)

    @dump
    def remove_admin(self, user_id: int) -> None:
        if user_id in self._admins:
            self._admins.remove(user_id)

    @property
    def active_templates(self) -> list[Template]:
        return [template for template in self._templates if template.is_active]

    def get_template(self, idx: int) -> Template:
        return self._templates[idx]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self._admins

    @property
    def channel(self) -> int | None:
        return self._channel

    @channel.setter
    @dump
    def channel(self, channel: int) -> None:
        self._channel = channel

    def to_json(self) -> dict[str, list[int] | int]:
        return {
            "admins": self._admins,
            "channel": self._channel,
        }

    @classmethod
    def from_json(cls, data: dict[str, list[int] | int]) -> Settings:
        try:
            return cls(data["admins"], data["channel"])
        except KeyError as e:
            raise ValueError(f"Invalid JSON data: {repr(e)}")

    @property
    def json_file(self) -> str:
        return SETTINGS_JSON


try:
    if os.path.isfile(SETTINGS_JSON):
        logger.info(f"Found settings file at {SETTINGS_JSON}, loading settings.")
        settings_json = json.load(open(SETTINGS_JSON))
        Settings.from_json(settings_json)
        logger.info(f"Successfully loaded settings from {SETTINGS_JSON}")
    else:
        logger.info(f"No settings file found at {SETTINGS_JSON}, will use default settings.")
except Exception as e:
    logger.error(f"Failed to load settings: {e}, will use default settings.")
finally:
    Settings()
