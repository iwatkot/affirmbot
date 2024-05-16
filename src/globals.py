import os

from dotenv import load_dotenv

from src.logger import Logger
from src.utils import EnvVars, env_to_list

logger = Logger(__name__)

local_env = os.path.join(os.getcwd(), "local.env")
if os.path.isfile(local_env):
    logger.debug(f"Loading local environment variables from {local_env}")
    load_dotenv(local_env)
TOKEN = os.getenv(EnvVars.TOKEN)
logger.info(f"Found TOKEN in environment variables (hidden): {'*' * len(TOKEN)}.")
ADMINS = env_to_list(EnvVars.ADMINS)
logger.info(f"Found ADMINS in environment variables: {ADMINS}.")

if not TOKEN:
    raise ValueError("Can't find TOKEN for bot token in environment variables")
