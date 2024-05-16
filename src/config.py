import yaml

from src.logger import Logger

logger = Logger(__name__)


class Config:
    def __init__(self, config_yaml: str):
        config_json = yaml.safe_load(open(config_yaml))
        logger.debug(f"Loaded config from {config_yaml}: {config_json}")

        forms = config_json.get("forms", [])
        if not forms:
            logger.error("No forms found in config")
            raise ValueError("No forms found in config")

        self._forms = config_json.get("forms", [])

    @property
    def forms(self) -> list:
        return self._forms
