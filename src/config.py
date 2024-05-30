import copy

import yaml

from src.globals import DEFAULT_CONFIG, config_yaml
from src.logger import Logger
from src.template import Template
from src.utils import Singleton

logger = Logger(__name__)


class Config(metaclass=Singleton):
    """Singleton class to load and store config from yaml file.
    Configuration is used to load custom forms and welcome message.
    Do not confuse with bot settings, which is stored in src/settings.py.

    Args:
        config_yaml (str | None): Path to yaml config file.
    """

    def __init__(self, config_yaml: str):
        config_json = yaml.safe_load(open(config_yaml))
        logger.info(f"Trying to load config from {config_yaml}")

        templates_json = config_json.get("templates", [])
        if not templates_json:
            logger.error("No templates found in config")
            raise ValueError("No templates found in config")
        self._templates = [Template(**template) for template in templates_json]

        welcome = config_json.get("welcome")
        if not welcome:
            logger.error("No welcome message found in config")
            raise ValueError("No welcome message found in config")
        self._welcome = welcome

    @property
    def templates(self) -> list[Template]:
        """List of templates loaded from config.

        Returns:
            list[Template]: List of templates.
        """
        return self._templates

    def get_template(self, idx: int) -> Template | None:
        """Get template by index.

        Args:
            idx (int): Index of template.

        Returns:
            Template | None: Template object or None if index is invalid.
        """
        template_idx = idx - 1
        if template_idx >= len(self.templates):
            logger.error(
                f"Invalid form index: {template_idx}, available indexes from 1 to {len(self.templates)}"
            )
            return
        return copy.deepcopy(self.templates[template_idx])

    @property
    def welcome(self) -> str:
        """Welcome message loaded from config.

        Returns:
            str: Welcome message.
        """
        return self._welcome


try:
    Config(config_yaml)
    logger.info(f"Succesfully loaded config from {config_yaml}")
except ValueError as e:
    logger.error(f"Failed to load config: {e}, will use default config.")
    Config(DEFAULT_CONFIG)
