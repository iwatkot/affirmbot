from aiogram import F
from aiogram.types import (
    CallbackQuery,
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
        self._message = message
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

    @property
    def message(self) -> Message:
        return self._message

    async def process(self, *args, **kwargs) -> None:
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

    async def process(self, *args, **kwargs) -> None:
        other_admins = [admin for admin in g.settings.admins if admin != self.message.from_user.id]
        if not other_admins:
            reply = "You are the only admin."
        else:
            reply = "List of admins:"

        data = {
            f"➖ Remove admin with ID: {admin}": f"remove_admin_{admin}" for admin in other_admins
        }
        data.update({AddAdmin._text: AddAdmin._callback})
        await self.message.answer(reply, reply_markup=self.inlines(data))


class Callback:
    @classmethod
    def callback(cls) -> F:
        return F.data.startswith(cls._callback)

    def __init__(self, query: CallbackQuery):
        data = query.data.replace(self._callback, "")
        self._data = None if not data else self._data_type(data)

    @property
    def data(self):
        return self._data

    @property
    def answer(self) -> str:
        return self._answer


class AddAdmin(Callback):
    _text = "➕ Add new admin"
    _callback = "add_admin"
    _data_type = int
    _answer = "Enter the ID of the user you want to add as an admin."


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
