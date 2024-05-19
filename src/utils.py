import os

from aiogram.fsm.state import State, StatesGroup


class Modes:
    """Simple class to store modes."""

    MODE = "mode"
    TEXT = "text"
    DATE = "date"
    ONEOF = "oneof"


class EnvVars:
    """Simple class to store environment variables names."""

    TOKEN = "TOKEN"
    ADMINS = "ADMINS"
    CONFIG = "CONFIG"
    ENV = "ENV"


def env_to_list(env_name: str, separator: str = ",", cast: type = int) -> list:
    """Read environment variable and return a list of values of specified type

    Args:
        env_name (str): Environment variable name
        separator (str, optional): Separator for splitting values. Defaults to ",".
        cast (type, optional): Type of values. Defaults to int.
    Returns:
        list: List of values
    """
    return [cast(env.strip()) for env in os.getenv(env_name, "").split(separator) if env.strip()]


class FormMeta(type):
    def __new__(cls, name, bases, attrs, titles=None):
        if titles is None:
            titles = []
        for attr in titles:
            attrs[attr] = State()
        return super().__new__(cls, name, bases, attrs)


class CombinedMeta(FormMeta, type(StatesGroup)):
    pass
