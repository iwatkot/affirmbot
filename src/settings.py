from __future__ import annotations

import json
import os
from functools import wraps

from src.config import Config
from src.globals import ADMINS, SETTINGS_JSON
from src.logger import Logger
from src.template import Template
from src.utils import SettingsFields, Singleton

logger = Logger(__name__)


class Settings(metaclass=Singleton):
    """Singleton class to manage bot settings, such as admins, channel, templates, etc.
    Saves settings to the JSON file on every change and loads them on bot start.

    Args:
        admins (list[int]): List of admin user IDs.
        channel (int): Channel ID.
    """

    def __init__(self, admins: list[int] | None = None, channel: int | None = None) -> None:
        if not admins:
            admins = ADMINS
        self._admins = admins
        self._templates = Config().templates

        # Setting index for each template to access them by index later.
        for idx, template in enumerate(self._templates):
            template.idx = idx
        self._channel = channel

        self._min_approval = 1
        self._min_rejection = 1

    def dump(func: callable) -> callable:
        """Decorator to save settings to JSON after the function call.

        Args:
            func (callable): Function to decorate.

        Returns:
            callable: Decorated function.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs) -> None:
            """Call decorated function and save settings to JSON file.

            Args:
                self (Settings): Settings object.
            """
            result = func(self, *args, **kwargs)
            with open(SETTINGS_JSON, "w") as f:
                json.dump(self.to_json(), f, indent=4)
            logger.info(f"Settings saved to {SETTINGS_JSON}")
            return result

        return wrapper

    @property
    def admins(self) -> list[int]:
        """Return list of admin user IDs.

        Returns:
            list[int]: List of admin user IDs.
        """
        return self._admins.copy()

    @dump
    def add_admin(self, user_id: int) -> None:
        """Add user to the list of admins.

        Args:
            user_id (int): User ID.
        """
        if user_id not in self._admins:
            self._admins.append(user_id)

    @dump
    def remove_admin(self, user_id: int) -> None:
        """Remove user from the list of admins.

        Args:
            user_id (int): User ID.
        """
        if user_id in self._admins:
            self._admins.remove(user_id)

    @property
    def active_templates(self) -> list[Template]:
        """Return list of active templates.

        Returns:
            list[Template]: List of active templates.
        """
        return [template for template in self._templates if template.is_active]

    @property
    def inactive_templates(self) -> list[Template]:
        """Return list of inactive templates.

        Returns:
            list[Template]: List of inactive templates.
        """
        return [template for template in self._templates if not template.is_active]

    @dump
    def deactivate_template(self, idx: int) -> None:
        """Deactivate template by index.

        Args:
            idx (int): Index of template.
        """
        self.get_template(idx).disable

    @dump
    def activate_template(self, idx: int) -> None:
        """Activate template by index.

        Args:
            idx (int): Index of template.
        """
        self.get_template(idx).enable

    @property
    def templates(self) -> list[Template]:
        """Return list of all templates.

        Returns:
            list[Template]: List of all templates.
        """
        return self._templates.copy()

    def get_template(self, idx: int) -> Template:
        """Get template by index.

        Args:
            idx (int): Index of template.

        Returns:
            Template: Template object.
        """
        return self._templates[idx]

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin.

        Args:
            user_id (int): User ID.

        Returns:
            bool: True if user is admin, False otherwise.
        """
        return user_id in self._admins

    @property
    def channel(self) -> int | None:
        """Return channel ID.

        Returns:
            int | None: Channel ID.
        """
        return self._channel

    @channel.setter
    @dump
    def channel(self, channel: int) -> None:
        """Set channel ID.

        Args:
            channel (int): Channel ID.
        """
        self._channel = channel

    @property
    def min_approval(self) -> int:
        """Return minimum number of approvals required for a template.

        Returns:
            int: Minimum number of approvals.
        """
        return self._min_approval

    @min_approval.setter
    @dump
    def min_approval(self, value: int) -> None:
        """Set minimum number of approvals required for a template.

        Args:
            value (int): Minimum number of approvals.
        """
        self._min_approval = value

    @property
    def min_rejection(self) -> int:
        """Return minimum number of rejections required for a template.

        Returns:
            int: Minimum number of rejections.
        """
        return self._min_rejection

    @min_rejection.setter
    @dump
    def min_rejection(self, value: int) -> None:
        """Set minimum number of rejections required for a template.

        Args:
            value (int): Minimum number of rejections.
        """
        self._min_rejection = value

    def to_json(self) -> dict[str, list[int] | int]:
        """Convert settings to JSON format.

        Returns:
            dict[str, list[int] | int]: JSON data.
        """
        return {
            # "admins": self._admins,
            SettingsFields.ADMINS: self._admins,
            SettingsFields.CHANNEL: self._channel,
            SettingsFields.ACTIVE_TEMPLATES: [template.idx for template in self.active_templates],
            SettingsFields.INACTIVE_TEMPLATES: [
                template.idx for template in self.inactive_templates
            ],
            SettingsFields.MIN_APPROVAL: self._min_approval,
            SettingsFields.MIN_REJECTION: self._min_rejection,
        }

    @classmethod
    def from_json(cls, data: dict[str, list[int] | int]) -> Settings:
        """Create settings object from JSON data.

        Args:
            data (dict[str, list[int] | int]): JSON data.

        Returns:
            Settings: Settings object.

        Raises:
            ValueError: If JSON data is invalid.
        """
        try:
            settings = cls(data[SettingsFields.ADMINS], data[SettingsFields.CHANNEL])
            for idx in data.get(SettingsFields.ACTIVE_TEMPLATES, []):
                settings.activate_template(idx)
            for idx in data.get(SettingsFields.INACTIVE_TEMPLATES, []):
                settings.deactivate_template(idx)
            settings.min_approval = data.get(SettingsFields.MIN_APPROVAL, 1)
            settings.min_rejection = data.get(SettingsFields.MIN_REJECTION, 1)
            return settings
        except KeyError as e:
            raise ValueError(f"Invalid JSON data: {repr(e)}")

    @property
    def json_file(self) -> str:
        """Return path to JSON file.

        Returns:
            str: Path to JSON file.
        """
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
