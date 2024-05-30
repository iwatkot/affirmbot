import os

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)


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


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


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


def make_dirs(dirs: list[str]) -> None:
    """Create multiple directories

    Args:
        dirs (list[str]): List of directories
    """
    for dir in dirs:
        os.makedirs(dir, exist_ok=True)


class Helper:
    @staticmethod
    async def force_answer(
        content: Message | CallbackQuery,
        text: str,
        butttons: list[str] = [],
    ) -> None:
        from src.bot import bot

        if isinstance(content, CallbackQuery):
            await bot.send_message(
                content.from_user.id,
                text,
                reply_markup=Helper.reply_keyboard(butttons),
            )
        else:
            await content.answer(text, reply_markup=Helper.reply_keyboard(butttons))

    @staticmethod
    def reply_keyboard(buttons: list[str] = None) -> ReplyKeyboardMarkup | None:
        if not buttons:
            return
        keyboard = [[KeyboardButton(text=button)] for button in buttons]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def inline_keyboard(data: dict[str, str]) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text=text, callback_data=data)] for text, data in data.items()
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


class FormMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict, steps: list[str] | None = None):
        if steps is None:
            steps = []
        for attr in steps:
            attrs[attr] = State()
        return super().__new__(cls, name, bases, attrs)


class CombinedMeta(FormMeta, type(StatesGroup)):
    pass


def get_form(steps: list[str]) -> StatesGroup:

    class Form(StatesGroup, metaclass=CombinedMeta, steps=steps):
        pass

    return Form
