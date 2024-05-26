import copy

import yaml

from src.logger import Logger
from src.template import Template
from src.utils import Singleton

logger = Logger(__name__)


class Config(metaclass=Singleton):
    def __init__(self, config_yaml: str):
        config_json = yaml.safe_load(open(config_yaml))
        logger.debug(f"Loaded config from {config_yaml}: {config_json}")

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
        return self._templates

    def get_template(self, template_title: str = None, template_idx: int = None) -> Template | None:
        if template_title:
            for form in self.templates:
                if form.title == template_title:
                    return copy.deepcopy(form)
        if template_idx:
            template_idx = template_idx - 1
            if template_idx >= len(self.templates):
                logger.error(
                    f"Invalid form index: {template_idx}, available indexes from 1 to {len(self.templates)}"
                )
                return
            return copy.deepcopy(self.templates[template_idx])

    @property
    def welcome(self) -> str:
        return self._welcome
