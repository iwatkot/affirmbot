from functools import partial
from time import time

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import Config
from src.logger import Logger
from src.settings import Settings
from src.template import Entry, NumberEntry
from src.utils import Helper, compile_form

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
    BUTTON_CHANNEL = "📡 Channel"
    BUTTON_TEMPLATES = "📄 Templates"

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
    _menu = [
        Event.BUTTON_ADMINS,
        Event.BUTTON_CHANNEL,
        Event.BUTTON_TEMPLATES,
        Event.BUTTON_MAIN_MENU,
    ]


class Admins(Event):
    _button = Event.BUTTON_ADMINS
    _menu = []

    async def process(self, *args, **kwargs) -> None:
        other_admins = [admin for admin in Settings().admins if admin != self.content.from_user.id]
        reply = "List of admins (current user is not displayed):"

        data = {
            f"{RemoveAdmin._text} with ID: {admin}": f"{RemoveAdmin._callback}{admin}"
            for admin in other_admins
        }
        data.update({AddAdmin._text: AddAdmin._callback})
        await self.content.answer(reply, reply_markup=Helper.inline_keyboard(data))


class Channel(Event):
    _button = Event.BUTTON_CHANNEL
    _menu = []

    async def process(self, *args, **kwargs) -> None:
        channel = Settings().channel
        reply = "Currently connected channel:"
        if not channel:
            data = {ConnectChannel._text: ConnectChannel._callback}
        else:
            data = {
                f"{DisconnectChannel._text} with ID: {channel}": f"{DisconnectChannel._callback}{channel}"
            }

        await self.content.answer(reply, reply_markup=Helper.inline_keyboard(data))


class Templates(Event):
    _button = Event.BUTTON_TEMPLATES
    _menu = []

    async def process(self, *args, **kwargs) -> None:
        reply = "List of templates:"
        data = {}
        for template in Settings().templates:
            callback = DeactivateTemplate if template.is_active else ActivateTemplate
            data[f"{callback._text}: {template.title}"] = f"{callback._callback}{template.idx}"

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


class ConnectChannel(Callback):
    _text = "➕ Connect channel"
    _callback = "admin__connect_channel_"
    _data_type = int
    _complete = "Channel connected."

    _connect_entry = NumberEntry(
        "Channel ID",
        "Incorrect channel ID or bot is not added to the channel.",
        "Enter the channel ID to connect.",
    )

    async def validate_connection(self, content: str):

        from src.bot import bot

        channel_id = int(content)
        try:
            message = await bot.send_message(
                channel_id, "AffirmBot is connected to the channel.", disable_notification=True
            )
            await message.delete()
            return True
        except Exception as e:
            logger.error(f"Error connecting to the channel: {e}")
            return False

    _connect_entry.validate_answer = partial(validate_connection, _connect_entry)

    _entries = [_connect_entry]

    async def process(self, *args, **kwargs) -> None:
        await super().process()
        Settings().channel = self.answers


class DisconnectChannel(Callback):
    _text = "➖ Disconnect channel"
    _callback = "admin__disconnect_channel_"
    _data_type = int
    _answer = "Channel disconnected."

    async def process(self, *args, **kwargs) -> None:
        Settings().channel = None


class RemoveAdmin(Callback):
    _text = "➖ Remove admin"
    _callback = "admin__remove_admin_"
    _data_type = int
    _answer = "Admin removed."

    async def process(self, *args, **kwargs) -> None:
        Settings().remove_admin(self.data)


class DeactivateTemplate(Callback):
    _text = "➖ Deactivate template"
    _callback = "admin__deactivate_template_"
    _data_type = int
    _answer = "Template deactivated."

    async def process(self, *args, **kwargs) -> None:
        Settings().deactivate_template(self.data)


class ActivateTemplate(Callback):
    _text = "➕ Activate template"
    _callback = "admin__activate_template_"
    _data_type = int
    _answer = "Template activated."

    async def process(self, *args, **kwargs) -> None:
        Settings().activate_template(self.data)


class Form(Callback):
    _callback = "user__form_"
    _data_type = int

    async def process(self, *args, **kwargs) -> None:
        template = Settings().get_template(self.data)
        self._entries = template.entries
        self._complete = template.complete
        await super().process()

        from src.bot import bot

        form = f"{template.title}\n\n"
        form += compile_form(self.results)
        username = self.content.from_user.username
        if True:
            form += f"\nAuthor: @{username}"
        else:
            form += f"\nAuthor: {self.content.from_user.full_name}"

        epoch = int(time())
        for admin in Settings().admins:
            data = {
                ConfirmForm._text: f"{ConfirmForm._callback}{epoch}_{self.user_id}_{admin}",
                RejectForm._text: f"{RejectForm._callback}{epoch}_{self.user_id}_{admin}",
            }
            try:
                await bot.send_message(admin, form, reply_markup=Helper.inline_keyboard(data))
            except Exception as e:
                logger.error(f"Error sending form to admin {admin}: {e}")


class ConfirmForm(Callback):
    _text = "✅ Confirm"
    _callback = "admin__confirm_form_"
    _data_type = str
    _answer = "Form confirmed."

    async def process(self, *args, **kwargs) -> None:
        epoch, user_id, admin = self.data.split("_")
        logger.debug(f"Form confirmed. Epoch: {epoch}, User: {user_id}, Admin: {admin}")


class RejectForm(Callback):
    _text = "❌ Reject"
    _callback = "admin__reject_form_"
    _data_type = str
    _answer = "Form rejected."

    async def process(self, *args, **kwargs) -> None:
        epoch, user_id, admin = self.data.split("_")
        logger.debug(f"Form rejected. Epoch: {epoch}, User: {user_id}, Admin: {admin}")


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
    _events = [SettingsMenu, Admins, Channel, Templates]


class AdminCallbacks(CallbackGroup):
    _prefix = "admin__"
    _callbacks = [
        AddAdmin,
        RemoveAdmin,
        ConnectChannel,
        DisconnectChannel,
        ActivateTemplate,
        DeactivateTemplate,
        ConfirmForm,
        RejectForm,
    ]


class UserCallbacks(CallbackGroup):
    _prefix = "user__"
    _callbacks = [Form]
