from aiogram import F
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

import src.globals as g
from src.logger import Logger

logger = Logger(__name__)


class Event:
    BUTTON_MAIN_MENU = "🏠 Main Menu"
    BUTTON_FORMS = "📝 Forms"
    """ADMIN BUTTONS"""
    BUTTON_SETTINGS = "⚙️ Settings"
    BUTTON_ADMINS = "👥 Admins"

    def __init__(self, message: Message) -> None:
        self._is_admin = g.settings.is_admin(message.from_user.id)

    @property
    def menu(self) -> ReplyKeyboardMarkup:
        buttons = self._menu + getattr(self, "_admin", [])
        keyboard = [[KeyboardButton(text=button)] for button in buttons]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    def inlines(self, data: dict[str, str]) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text=text, callback_data=data)] for text, data in data.items()
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @classmethod
    def button(cls) -> F:
        return F.text == cls._button

    @property
    def answer(self) -> str:
        return self._answer

    async def process(self, message: Message, *args, **kwargs) -> None:
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
    _answer = "In this section you can change the settings of the bot."
    _menu = [Event.BUTTON_ADMINS, Event.BUTTON_MAIN_MENU]


class Admins(Event):
    _button = Event.BUTTON_ADMINS
    _answer = (
        "Here's the list of admins, you can add or remove them, but you can't remove yourself."
    )
    _menu = []

    async def process(self, message: Message, *args, **kwargs) -> None:
        other_admins = [admin for admin in g.settings.admins if admin != message.from_user.id]
        if not other_admins:
            reply = "You are the only admin."
        else:
            reply = "List of admins:"

        data = {f"Remove admin with ID: {admin}": f"remove_admin_{admin}" for admin in other_admins}
        data.update({"Add new admin": "add_admin"})
        await message.answer(reply, reply_markup=self.inlines(data))


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


class AdminGroup(EventGroup):
    _events = [Settings, Admins]
