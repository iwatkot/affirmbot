import os

from dotenv import load_dotenv

from src.config import Config
from src.logger import Logger
from src.utils import EnvVars, env_to_list, make_dirs

logger = Logger(__name__)

# region constants
CWD = os.getcwd()
LOCAL_ENV = os.path.join(CWD, "local.env")
DEFAULT_CONFIG = os.path.join(CWD, "config.yml")
CUSTOM_CONFIG = os.path.join(CWD, "custom.yml")
SETTINGS_JSON = os.path.join(CWD, "settings.json")
STORAGE_JSON = os.path.join(CWD, "storage.json")
TMP_DIR = os.path.join(CWD, "tmp")
REPO_DIR = os.path.join(TMP_DIR, "repo")
# endregion
make_dirs([REPO_DIR])

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

try:
    if CONFIG:
        logger.info(f"Found CONFIG in environment variables: {CONFIG}.")
        Config.from_git(CONFIG, REPO_DIR, CUSTOM_CONFIG)
    else:
        raise ValueError("No CONFIG environment variable found, using default config.yml")
except Exception as e:
    logger.warning(f"Failed to load custom config: {e}")
    Config.from_yaml(DEFAULT_CONFIG)
