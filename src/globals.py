import os

from dotenv import load_dotenv

from src.config import Config
from src.form import Form
from src.logger import Logger
from src.utils import EnvVars, env_to_list

logger = Logger(__name__)

local_env = os.path.join(os.getcwd(), "local.env")
if os.path.isfile(local_env):
    logger.debug(f"Loading local environment variables from {local_env}")
    load_dotenv(local_env)
TOKEN = os.getenv(EnvVars.TOKEN)
if not TOKEN:
    raise ValueError("Can't find TOKEN for bot token in environment variables")
logger.info(f"Found TOKEN in environment variables (hidden): {'*' * len(TOKEN)}.")

ADMINS = env_to_list(EnvVars.ADMINS)
if not ADMINS:
    raise ValueError("Can't find ADMINS in environment variables")
logger.info(f"Found ADMINS in environment variables: {ADMINS}.")

CONFIG = os.getenv(EnvVars.CONFIG)
if CONFIG:
    # TODO: Clone repo from the address in FORM and return a path to yaml file.
    config_yaml = ""
else:
    logger.info("No CONFIG environment variable found, using default config.yml")
    config_yaml = os.path.join(os.getcwd(), "config.yml")

if not os.path.isfile(config_yaml):
    raise FileNotFoundError(f"Can't find config file at {config_yaml}")

config = Config(config_yaml)
forms = [Form(**form) for form in config.forms]
logger.info(f"Loaded {len(forms)} forms: {forms}")
