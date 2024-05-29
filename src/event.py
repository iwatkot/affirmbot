from functools import partial
from typing import Type

from aiogram import F, MagicFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.config import Config
from src.logger import Logger
from src.settings import Settings
from src.storage import Post, Storage
from src.template import Entry, NumberEntry
from src.utils import Helper

logger = Logger(__name__)


class BaseEvent:
    _entries: list[Entry] = []
    _complete: str = ""

    def __init__(self, content: Message | CallbackQuery, state: FSMContext) -> None:
        self._content = content
        self._state = state
        user = content.from_user
        if not user:
            raise ValueError("No user found in the content.")
        self._user_id = user.id
        self._is_admin = Settings().is_admin(self._user_id)
        logger.debug(
            f"Event {self.__class__.__name__} initialized for user {self.user_id} (admin: {self.is_admin})"
        )

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
    def answer(self) -> str | None:
        if hasattr(self, "_answer"):
            return self._answer
        return None

    @property
    def menu(self) -> list[str] | None:
        if hasattr(self, "_menu"):
            return self._menu
        return None

    @property
    def entries(self) -> list[Entry]:
        return getattr(self, "_entries", [])

    @property
    def complete(self) -> str:
        return getattr(self, "_complete")

    async def reply(self, *args, **kwargs):
        if not self.answer:
            return

        await Helper.force_answer(self.content, self.answer, self.menu)

    async def process(self, *args, **kwargs) -> None:
        if self.entries:
            logger.debug(f"Processing form with {len(self.entries)} entries...")
            from src.stepper import Stepper

            stepper = Stepper(
                self.content,
                self.state,
                entries=self.entries,
                complete=self.complete,
            )
            await stepper.start()
            self.results = await stepper.get_results()
            logger.debug(f"Form processed with results: {self.results}")


class Event(BaseEvent):
    BUTTON_MAIN_MENU = "🏠 Main Menu"
    BUTTON_CANCEL = "❌ Cancel"
    BUTTON_FORMS = "📝 Forms"
    """ADMIN BUTTONS"""
    BUTTON_SETTINGS = "⚙️ Settings"
    BUTTON_ADMINS = "👥 Admins"
    BUTTON_CHANNEL = "📡 Channel"
    BUTTON_TEMPLATES = "📄 Templates"

    _button = ""
    _menu: list[str] = []

    @property
    def menu(self) -> list[str]:
        buttons = self._menu.copy()
        if self.is_admin:
            buttons += getattr(self, "_admin", [])
        return buttons

    @classmethod
    def button(cls) -> MagicFilter:
        return F.text == cls._button

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
        other_admins = [admin for admin in Settings().admins if admin != self.user_id]
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

    async def process(self, *args, **kwargs) -> None:
        templates = Settings().active_templates
        reply = "Select a form to fill out:"

        data = {template.title: f"{Form._callback}{template.idx}" for template in templates}
        await self.content.answer(reply, reply_markup=Helper.inline_keyboard(data))


class Callback(BaseEvent):
    _callback = ""
    _text = ""
    # ! "Callback" has no attribute "_data_type"  [attr-defined]

    @classmethod
    def callback(cls) -> MagicFilter:
        return F.data.startswith(cls._callback)

    def __init__(self, content: CallbackQuery, state: FSMContext) -> None:
        super().__init__(content, state)
        if not content.data:
            raise ValueError("Callback data is empty.")
        data = content.data.replace(self._callback, "")
        self._data = None if not data else self._data_type(data)  # type: ignore[attr-defined]

    @property
    def data(self):
        return self._data

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

    async def validate_connection(self, content: str) -> bool:

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

    _connect_entry.replace_validator(partial(validate_connection, _connect_entry))

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
        logger.debug(f"Processing form with template ID: {self.data}")
        template = Settings().get_template(self.data)
        logger.debug(f"Get template: {template.title}")
        if not template.entries:
            raise ValueError("Template has no entries.")
        self._entries = template.entries
        self._complete = template.complete or "Form completed."
        await super().process()

        logger.debug(f"Form results: {self.results}")

        post = Post.from_content(template.title, self.results, self.content)  # type: ignore[arg-type]
        # ! Argument 2 to "from_content" of "Post" has incompatible type "dict[str, str] | None"; expected "dict[str, str | list[str]]"  [arg-type]
        Storage().add_post(post)

        from src.bot import bot

        for admin in Settings().admins:
            data = {
                ConfirmForm._text: f"{ConfirmForm._callback}{post.id}",
                RejectForm._text: f"{RejectForm._callback}{post.id}",
            }
            try:
                await bot.send_message(
                    admin, post.message, reply_markup=Helper.inline_keyboard(data)
                )
            except Exception as e:
                logger.error(f"Error sending form to admin {admin}: {e}")


class ConfirmForm(Callback):
    _text = "✅ Confirm"
    _callback = "admin__confirm_form_"
    _data_type = str
    _answer = "Form confirmed."
    _storage_method = "approve_by"

    async def process(self, *args, **kwargs) -> None:
        post = Storage().get_post(self.data)
        if not post:
            await Helper.force_answer(
                self.content, "Form not found, it may have been approved or rejected already."
            )
            return
        await getattr(post, self._storage_method)(self.user_id)


class RejectForm(ConfirmForm):
    _text = "❌ Reject"
    _callback = "admin__reject_form_"
    _data_type = str
    _answer = "Form rejected."
    _storage_method = "reject_by"


class EventGroup:
    _events: list[Type[Event]] = []

    @classmethod
    def buttons(cls) -> MagicFilter:
        return F.text.in_([event._button for event in cls._events])

    @classmethod
    def event(cls, message: Message, state: FSMContext) -> Event:
        for event in cls._events:
            if event._button == message.text:
                return event(message, state)
        return MainMenu(message, state)


class CallbackGroup:
    _callbacks: list[Type[Callback]] = []
    _prefix = ""

    @classmethod
    def callbacks(cls) -> MagicFilter:
        return F.data.startswith(cls._prefix)

    @classmethod
    def callback(cls, query: CallbackQuery, state: FSMContext) -> Callback | None:
        for event in cls._callbacks:
            if query.data and query.data.startswith(event._callback):
                return event(query, state)
        return None


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
