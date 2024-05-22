from aiogram import F
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

import src.globals as g
from src.logger import Logger

logger = Logger(__name__)


class Event:
    BUTTON_MAIN_MENU = "🏠 Main Menu"
    BUTTON_FORMS = "📝 Forms"
    BUTTON_SETTINGS = "⚙️ Settings"

    def __init__(self, message: Message) -> None:
        self._is_admin = g.settings.is_admin(message.from_user.id)

    @property
    def menu(self) -> ReplyKeyboardMarkup:
        buttons = self._menu + getattr(self, "_admin", [])
        keyboard = [[KeyboardButton(text=button)] for button in buttons]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @classmethod
    def button(cls) -> F:
        return F.text == cls._button

    @property
    def answer(self) -> str:
        return self._answer

    def process(self) -> None:
        pass


class MainMenu(Event):
    _button = Event.BUTTON_MAIN_MENU
    _answer = "Now you are in the main menu, use the buttons below to navigate."
    _menu = [Event.BUTTON_FORMS]
    _admin = [Event.BUTTON_SETTINGS]


class Start(MainMenu):
    _button = "/start"
    _answer = g.config.welcome


class Settings(Event):
    _button = Event.BUTTON_SETTINGS
    _answer = "Settings"
    _menu = [Event.BUTTON_MAIN_MENU]


class EventGroup:
    @classmethod
    def buttons(cls) -> F:
        return F.text.in_([event._button for event in cls._events])

    @classmethod
    def event(cls, message: Message) -> Event:
        for event in cls._events:
            if event._button == message.text:
                return event(message)
        return MainMenu(message)


class MenuGroup(EventGroup):
    _events = [Start, MainMenu]
