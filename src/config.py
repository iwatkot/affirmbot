from __future__ import annotations

import copy
import shutil

import yaml
from git import Repo

from src.logger import Logger
from src.template import Template
from src.utils import Singleton, find_file

logger = Logger(__name__)


class Config(metaclass=Singleton):
    """Singleton class to load and store config from yaml file.
    Configuration is used to load custom forms and welcome message.
    Do not confuse with bot settings, which is stored in src/settings.py.

    Args:
        templates (list[Template]): List of templates.
        welcome (str): Welcome message.
    """

    file_name = "config.yml"

    def __init__(self, templates: list[Template], welcome: str):
        self._templates = templates
        self._welcome = welcome

    @classmethod
    def from_yaml(cls, config_yaml: str) -> Config:
        """Create Config object from yaml file.

        Args:
            config_yaml (str): Path to yaml file.

        Returns:
            Config: Config object.

        Raises:
            ValueError: If no templates found in config.
            ValueError: If failed to load templates.
            ValueError: If no welcome message found in config.
        """
        logger.info(f"Loading config from {config_yaml}")
        config_json = yaml.safe_load(open(config_yaml))
        templates_json = config_json.get("templates", [])
        if not templates_json:
            logger.error("No templates found in config")
            raise ValueError("No templates found in config")
        try:
            templates = [Template(**template) for template in templates_json]
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            raise ValueError("Failed to load templates")

        welcome = config_json.get("welcome")
        if not welcome:
            logger.error("No welcome message found in config")
            raise ValueError("No welcome message found in config")

        logger.info(f"Succesfully loaded config with {len(templates)} templates")
        return cls(templates, welcome)

    @classmethod
    def from_git(cls, repo_url: str, repo_directory: str, save_path: str) -> Config:
        Repo.clone_from(repo_url, repo_directory)
        logger.info(f"Cloned repository from {repo_url} to {repo_directory}")
        config_file = find_file(repo_directory, cls.file_name)
        if not config_file:
            return

        shutil.copy(config_file, save_path)
        logger.info(f"Found config.yml, copied to {save_path}")
        shutil.rmtree(repo_directory)
        logger.debug(f"Removed repository directory {repo_directory}")

        return cls.from_yaml(save_path)

    @property
    def templates(self) -> list[Template]:
        """List of templates loaded from config.

        Returns:
            list[Template]: List of templates.
        """
        return self._templates

    @templates.setter
    def templates(self, templates: list[Template]) -> None:
        """Set templates.

        Args:
            templates (list[Template]): List of templates.
        """
        self._templates = templates

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
