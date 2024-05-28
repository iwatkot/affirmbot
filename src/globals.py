import os

from dotenv import load_dotenv

from src.logger import Logger
from src.utils import EnvVars, env_to_list

logger = Logger(__name__)

# region constants
CWD = os.getcwd()
LOCAL_ENV = os.path.join(CWD, "local.env")
DEFAULT_CONFIG = os.path.join(CWD, "config.yml")
SETTINGS_JSON = os.path.join(CWD, "settings.json")
STORAGE_JSON = os.path.join(CWD, "storage.json")
# endregion

if os.path.isfile(LOCAL_ENV):
    logger.debug(f"Loading local environment variables from {LOCAL_ENV}")
    load_dotenv(LOCAL_ENV)

# region envvars
TOKEN = os.getenv(EnvVars.TOKEN)
ADMINS = env_to_list(EnvVars.ADMINS)
CONFIG = os.getenv(EnvVars.CONFIG)
ENV = os.getenv(EnvVars.ENV)
# endregion

if ENV == "DEV":
    is_development = True
    logger.info("Running in development mode.")
else:
    is_development = False
    logger.info("Running in production mode.")

if not TOKEN:
    raise ValueError("Can't find TOKEN for bot token in environment variables")
logger.info(f"Found TOKEN in environment variables (hidden): {'*' * len(TOKEN)}.")

if not ADMINS:
    raise ValueError("Can't find ADMINS in environment variables")
logger.info(f"Found ADMINS in environment variables: {ADMINS}.")

if CONFIG:
    # TODO: Clone repo from the address in FORM and return a path to yaml file.
    config_yaml = ""
else:
    logger.info("No CONFIG environment variable found, using default config.yml")
    config_yaml = DEFAULT_CONFIG

if not os.path.isfile(config_yaml):
    raise FileNotFoundError(f"Can't find config file at {config_yaml}")
