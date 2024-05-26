from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import Config
from src.logger import Logger
from src.settings import Settings
from src.template import Entry, NumberEntry
from src.utils import Helper

logger = Logger(__name__)


class BaseEvent:
    def __init__(self, content: Message | CallbackQuery, state: FSMContext) -> None:
        self._content = content
        self._state = state
        self._user_id = content.from_user.id
        self._is_admin = Settings().is_admin(self._user_id)

    @property
    def content(self) -> Message | CallbackQuery:
        return self._content

    @property
    def state(self) -> FSMContext:
        return self._state

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def is_admin(self) -> bool:
        return self._is_admin

    @property
    def answer(self) -> str:
        return getattr(self, "_answer", None)

    @property
    def menu(self) -> list[str]:
        return getattr(self, "_menu", None)

    async def reply(self, *args, **kwargs):
        if not self.answer:
            return

        await Helper.force_answer(self.content, self.answer, self.menu)

    async def process(self, *args, **kwargs) -> None:
        if self.entries:
            from src.stepper import Stepper

            stepper = Stepper(
                self.content,
                self.state,
                entries=self.entries,
                complete=self.complete,
            )
            await stepper.start()
            self.results = await stepper.results()


class Event(BaseEvent):
    BUTTON_MAIN_MENU = "🏠 Main Menu"
    BUTTON_CANCEL = "❌ Cancel"
    BUTTON_FORMS = "📝 Forms"
    """ADMIN BUTTONS"""
    BUTTON_SETTINGS = "⚙️ Settings"
    BUTTON_ADMINS = "👥 Admins"

    @property
    def menu(self) -> list[str]:
        buttons = self._menu.copy()
        if self.is_admin:
            buttons += getattr(self, "_admin", [])
        return buttons

    @classmethod
    def button(cls) -> F:
        return F.text == cls._button

    @property
    def answer(self) -> str:
        return getattr(self, "_answer", None)

    async def process(self, *args, **kwargs) -> None:
        pass


class MainMenu(Event):
    _button = Event.BUTTON_MAIN_MENU
    _answer = "Now you are in the main menu, use the buttons below to navigate."
    _menu = [Event.BUTTON_FORMS]
    _admin = [Event.BUTTON_SETTINGS]


class Start(MainMenu):
    _button = "/start"
    _answer = Config().welcome


class Cancel(MainMenu):
    _button = Event.BUTTON_CANCEL
    _answer = "Operation canceled."

    async def process(self, *args, **kwargs) -> None:
        await self.state.clear()


class SettingsMenu(Event):
    _button = Event.BUTTON_SETTINGS
    _answer = "In this section you can change the settings of the bot."
    _menu = [Event.BUTTON_ADMINS, Event.BUTTON_MAIN_MENU]


class Admins(Event):
    _button = Event.BUTTON_ADMINS
    _menu = []

    async def process(self, *args, **kwargs) -> None:
        other_admins = [admin for admin in Settings().admins if admin != self.content.from_user.id]
        reply = "List of admins (current user is not displayed):"

        data = {
            f"➖ Remove admin with ID: {admin}": f"{RemoveAdmin._callback}{admin}"
            for admin in other_admins
        }
        data.update({AddAdmin._text: AddAdmin._callback})
        await self.content.answer(reply, reply_markup=Helper.inline_keyboard(data))


class Forms(Event):
    _button = Event.BUTTON_FORMS
    _menu = []

    async def process(self, *args, **kwargs) -> None:
        templates = Settings().active_templates
        reply = "Select a form to fill out:"

        data = {template.title: f"{Form._callback}{template.idx}" for template in templates}
        await self.content.answer(reply, reply_markup=Helper.inline_keyboard(data))


class Callback(BaseEvent):
    @classmethod
    def callback(cls) -> F:
        return F.data.startswith(cls._callback)

    def __init__(self, content: CallbackQuery, state: FSMContext) -> None:
        super().__init__(content, state)
        data = content.data.replace(self._callback, "")
        self._data = None if not data else self._data_type(data)

    @property
    def data(self):
        return self._data

    @property
    def entries(self) -> list[Entry]:
        return getattr(self, "_entries", [])

    @property
    def complete(self) -> str:
        return getattr(self, "_complete")

    async def process(self, *args, **kwargs) -> None:
        await super().process()

    @property
    def answers(self):
        answers = []
        for entry in self.entries:
            answers.append(entry.get_answer(self.results))
        return answers if len(answers) > 1 else answers[0]


class AddAdmin(Callback):
    _text = "➕ Add new admin"
    _callback = "admin__add_admin"
    _data_type = int
    _complete = "Admin added."

    _entries = [NumberEntry("Admin ID", "Incorrect user ID.", "Enter the user ID to add as admin.")]

    async def process(self, *args, **kwargs) -> None:
        await super().process()
        Settings().add_admin(self.answers)


class RemoveAdmin(Callback):
    _callback = "admin__remove_admin"
    _data_type = int
    _answer = "Admin removed."

    async def process(self, *args, **kwargs) -> None:
        Settings().remove_admin(self.data)


class Form(Callback):
    _callback = "user__form_"
    _data_type = int

    async def process(self, *args, **kwargs) -> None:
        template = Settings().get_template(self.data)
        self._entries = template.entries
        self._complete = template.complete
        await super().process()


class EventGroup:
    @classmethod
    def buttons(cls) -> F:
        return F.text.in_([event._button for event in cls._events])

    @classmethod
    def event(cls, message: Message, state: FSMContext) -> Event:
        for event in cls._events:
            if event._button == message.text:
                return event(message, state)
        return MainMenu(message, state)


class CallbackGroup:
    @classmethod
    def callbacks(cls) -> F:
        return F.data.startswith(cls._prefix)

    @classmethod
    def callback(cls, query: CallbackQuery, state: FSMContext) -> Callback:
        for event in cls._callbacks:
            if query.data.startswith(event._callback):
                return event(query, state)


class MenuGroup(EventGroup):
    _events = [Start, MainMenu, Cancel, Forms]


class AdminGroup(EventGroup):
    _events = [SettingsMenu, Admins]


class AdminCallbacks(CallbackGroup):
    _prefix = "admin__"
    _callbacks = [AddAdmin, RemoveAdmin]


class UserCallbacks(CallbackGroup):
    _prefix = "user__"
    _callbacks = [Form]
