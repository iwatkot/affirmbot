import copy

import yaml

from src.form import Form
from src.logger import Logger

logger = Logger(__name__)


class Config:
    def __init__(self, config_yaml: str):
        config_json = yaml.safe_load(open(config_yaml))
        logger.debug(f"Loaded config from {config_yaml}: {config_json}")

        templates_json = config_json.get("templates", [])
        if not templates_json:
            logger.error("No templates found in config")
            raise ValueError("No templates found in config")
        self._templates = [Form(**template) for template in templates_json]

    @property
    def templates(self) -> list[Form]:
        return self._templates

    def get_form(self, form_title: str = None, form_idx: int = None) -> Form | None:
        if form_title:
            for form in self.templates:
                if form.title == form_title:
                    return copy.deepcopy(form)
        if form_idx:
            form_idx = form_idx - 1
            if form_idx >= len(self.templates):
                logger.error(
                    f"Invalid form index: {form_idx}, available indexes from 1 to {len(self.templates)}"
                )
                return
            return copy.deepcopy(self.templates[form_idx])
