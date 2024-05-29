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
        self._admins = admins or []
        self._templates = Config().templates
        for idx, template in enumerate(self._templates):
            template.idx = idx
        self._channel = channel

        self._min_approval = 1
        self._min_rejection = 1

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

    @property
    def inactive_templates(self) -> list[Template]:
        return [template for template in self._templates if not template.is_active]

    @dump
    def deactivate_template(self, idx: int) -> None:
        self.get_template(idx).disable

    @dump
    def activate_template(self, idx: int) -> None:
        self.get_template(idx).enable

    @property
    def templates(self) -> list[Template]:
        return self._templates.copy()

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

    @property
    def min_approval(self) -> int:
        return self._min_approval

    @min_approval.setter
    @dump
    def min_approval(self, value: int) -> None:
        self._min_approval = value

    @property
    def min_rejection(self) -> int:
        return self._min_rejection

    @min_rejection.setter
    @dump
    def min_rejection(self, value: int) -> None:
        self._min_rejection = value

    def to_json(self) -> dict[str, list[int] | int]:
        return {
            "admins": self._admins,
            "channel": self._channel,
            "active_templates": [template.idx for template in self.active_templates],
            "inactive_templates": [template.idx for template in self.inactive_templates],
            "min_approval": self._min_approval,
            "min_rejection": self._min_rejection,
        }

    @classmethod
    def from_json(cls, data: dict[str, list[int] | int]) -> Settings:
        try:
            settings = cls(data["admins"], data["channel"])
            for idx in data.get("active_templates", []):
                settings.activate_template(idx)
            for idx in data.get("inactive_templates", []):
                settings.deactivate_template(idx)
            settings.min_approval = data.get("min_approval", 1)
            settings.min_rejection = data.get("min_rejection", 1)
            return settings
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
