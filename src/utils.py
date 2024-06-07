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
    NUMBER = "number"
    DATE = "date"
    ONEOF = "oneof"
    URL = "url"
    FILE = "file"


class EnvVars:
    """Simple class to store environment variables names."""

    TOKEN = "TOKEN"
    ADMINS = "ADMINS"
    CONFIG = "CONFIG"
    ENV = "ENV"
    CHANNEL = "CHANNEL"


class SettingsFields:
    """Simple class to store settings fields names."""

    ADMINS = "admins"
    MODERATORS = "moderators"
    CHANNEL = "channel"
    ACTIVE_TEMPLATES = "active_templates"
    INACTIVE_TEMPLATES = "inactive_templates"
    MIN_APPROVAL = "min_approval"
    MIN_REJECTION = "min_rejection"


class StorageFields:
    """Simple class to store storage fields names."""

    POSTS = "posts"
    TITLE = "title"
    DATA = "data"
    TOEND = "toend"
    ID = "id"
    USER_ID = "user_id"
    USERNAME = "username"
    FULL_NAME = "full_name"
    ACCEPTED_BY = "accepted_by"
    REJECTED_BY = "rejected_by"


class Singleton(type):
    """Metaclass to create a singleton class."""

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
    """Simple class to simplify some aiogram functions."""

    @staticmethod
    async def force_answer(
        content: Message | CallbackQuery,
        text: str,
        buttons: list[str] = [],
    ) -> None:
        """By default the CallbackQuery.answer() method looks very bad in the telegram chat.
        For this reason, we will send a classic message with the same text and buttons.

        Args:
            content (Message | CallbackQuery): Content to reply to
            text (str): Text of the message
            buttons (list[str], optional): Buttons to display. Defaults to [].
        """
        from src.bot import bot

        if isinstance(content, CallbackQuery):
            await bot.send_message(
                content.from_user.id,
                text,
                reply_markup=Helper.reply_keyboard(buttons),
            )
        else:
            await content.answer(text, reply_markup=Helper.reply_keyboard(buttons))

    @staticmethod
    def reply_keyboard(buttons: list[str] = None) -> ReplyKeyboardMarkup | None:
        """Create a reply keyboard with buttons from the given list.

        Args:
            buttons (list[str], optional): List of buttons. Defaults to None.

        Returns:
            ReplyKeyboardMarkup | None: Reply keyboard with buttons
        """
        if not buttons:
            return
        per_row = Helper.per_row(len(buttons))
        keyboard = [buttons[i : i + per_row] for i in range(0, len(buttons), per_row)]
        keyboard = [[KeyboardButton(text=button) for button in row] for row in keyboard]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @staticmethod
    def per_row(buttons: int) -> int:
        """Calculate how many buttons should be in a row.

        Args:
            buttons (int): Number of buttons

        Returns:
            int: Number of buttons in a row
        """
        if buttons % 3 == 0 or buttons % 2 == 0:
            return buttons // 2 if buttons > 2 else buttons
        else:
            return buttons // 2 + buttons % 2

    @staticmethod
    def inline_keyboard(data: dict[str, str]) -> InlineKeyboardMarkup:
        """Create an inline keyboard with buttons from the given dictionary,
        where the key is the text of the button and the value is the callback data, from which
        the callback query will be created.

        Args:
            data (dict[str, str]): Dictionary with buttons data

        Returns:
            InlineKeyboardMarkup: Inline keyboard with buttons
        """
        keyboard = [
            [InlineKeyboardButton(text=text, callback_data=data)] for text, data in data.items()
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


class FormMeta(type):
    """Simple class to set attributes as State objects without creating the instance of the class."""

    def __new__(cls, name: str, bases: tuple, attrs: dict, steps: list[str] | None = None):
        if steps is None:
            steps = []
        for attr in steps:
            attrs[attr] = State()
        return super().__new__(cls, name, bases, attrs)


class CombinedMeta(FormMeta, type(StatesGroup)):
    """Since the StatesGroup already has it's metaclass, we need to combine it with our metaclass."""

    pass


def get_form(steps: list[str]) -> StatesGroup:
    """Returns a new class, with attributes as State objects.

    Args:
        steps (list[str]): List of steps

    Returns:
        StatesGroup: New class with steps as State objects
    """

    class Form(StatesGroup, metaclass=CombinedMeta, steps=steps):
        pass

    return Form


def find_file(directory: str, file_name: str) -> str | None:
    """Try to find the file in the given directory and all subdirectories.

    Args:
        directory (str): Path to the directory
        file_name (str): Name of the file

    Returns:
        str | None: Path to the file or None if not found
    """
    for root, _, files in os.walk(directory):
        if file_name in files:
            return os.path.join(root, file_name)
    return None


def to_github_url(repo: str) -> str:
    """Converts the repository name to the GitHub URL.
    If the repository name already contains the URL, it will return the same string.

    Args:
        repo (str): Repository name

    Returns:
        str: GitHub URL
    """
    if not repo.startswith("https://github.com/"):
        return "https://github.com/" + repo
    return repo
