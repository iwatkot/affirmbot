from aiogram import F
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

import src.globals as g


class Event:
    BUTTON_MAIN_MENU = "🏠 Main Menu"
    BUTTON_FORMS = "📝 Forms"
    BUTTON_SETTINGS = "⚙️ Settings"

    @classmethod
    def menu(cls, **kwargs) -> ReplyKeyboardMarkup:
        return cls._reply_markup(cls._menu)

    @classmethod
    def admin_menu(cls, **kwargs) -> ReplyKeyboardMarkup:
        message: Message = kwargs.get("message")
        if not message or not g.settings.is_admin(message.from_user.id):
            buttons = cls._menu
        else:
            buttons = cls._admin + cls._menu

        return cls._reply_markup(buttons)

    @classmethod
    def button(cls) -> F:
        return F.text.startswith(cls._button)

    @classmethod
    def answer(cls) -> str:
        return cls._answer

    @classmethod
    def _reply_markup(cls, buttons: list[str]) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text=button)] for button in buttons]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


class MainMenu(Event):
    _button = Event.BUTTON_MAIN_MENU
    _answer = "Now you are in the main menu, use the buttons below to navigate."
    _menu = [Event.BUTTON_FORMS]
    _admin = [Event.BUTTON_SETTINGS]

    @classmethod
    def menu(cls, **kwargs) -> ReplyKeyboardMarkup:
        return cls.admin_menu(**kwargs)


class Start(MainMenu):
    _button = "/start"
    _answer = g.config.welcome


class Settings(Event):
    _button = Event.BUTTON_SETTINGS
    _answer = "Settings"
    _menu = [Event.BUTTON_MAIN_MENU]
