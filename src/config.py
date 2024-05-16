import yaml

from src.logger import Logger

logger = Logger(__name__)


class Config:
    def __init__(self, config_yaml: str):
        config_json = yaml.safe_load(open(config_yaml))
        logger.debug(f"Loaded config from {config_yaml}: {config_json}")

        self._forms = config_json.get("forms", [])

    @property
    def forms(self) -> list:
        return self._forms
