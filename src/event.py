import os
from functools import partial

from aiogram import F, MagicFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from src.config import Config
from src.logger import Logger
from src.settings import Settings
from src.storage import Post, Storage
from src.template import Entry, FileEntry, NumberEntry, OneOfEntry
from src.utils import Helper

logger = Logger(__name__)


class BaseEvent:
    """Base class for all events.
    Each event will have a content and state properties and the process method may be
    reimplemented in the child class to handle some specific logic.

    Args:
        content (Message | CallbackQuery): The content of the event.
        state (FSMContext): The state of the event.
    """

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
        """Return the content of the event, which can be a message or a callback query.
        The content has no setter, so it can't be changed after initialization.

        Returns:
            Message | CallbackQuery: The content of the event.
        """
        return self._content

    @property
    def state(self) -> FSMContext:
        """Return the state of the event, which is a FSMContext object.
        The state has no setter, so it can't be changed after initialization.

        Returns:
            FSMContext: The state of the event.
        """
        return self._state

    @property
    def user_id(self) -> int:
        """Return the user ID of the event content.

        Returns:
            int: The user ID of the event content.
        """
        return self._user_id

    @property
    def is_admin(self) -> bool:
        """Return True if the user is an admin, otherwise False.

        Returns:
            bool: True if the user is an admin, otherwise False.
        """
        return self._is_admin

    @property
    def answer(self) -> str | None:
        """Return the answer of the event, which is a string to be sent as a reply to the user.
        The instance of the class may don't have this property, so it returns None.

        Returns:
            str | None: The answer of the event or None if it doesn't exist.
        """
        return getattr(self, "_answer", None)

    @property
    def menu(self) -> list[str]:
        """Return the menu of the event, which is a list of strings to be used as buttons in the reply.

        Returns:
            list[str]: The menu of the event.
        """
        return getattr(self, "_menu", [])

    @property
    def entries(self) -> list[Entry]:
        """Return the entries of the event, which is a list of Entry objects to be used in the form.

        Returns:
            list[Entry]: The entries of the event.
        """
        return getattr(self, "_entries", [])

    @property
    def complete(self) -> str:
        """Return the complete message of the event, which is a string to be sent when the form is completed.

        Returns:
            str: The complete message of the event.
        """
        return getattr(self, "_complete")

    async def reply(self) -> None:
        """Reply to the user with the answer of the event, using
        force_answer method to always send the message, even for the callback queries."""
        if not self.answer:
            return
        await Helper.force_answer(self.content, self.answer, self.menu)

    async def process(self) -> None:
        """Process the event, which may be reimplemented in the child class to handle some specific logic."""
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
    """Base class for all events with buttons.
    Each event will have a button and an answer properties, for the menus it will have a menu property,
    and in some cases admin property with the admin buttons.
    """

    BUTTON_MAIN_MENU = "🏠 Main Menu"
    BUTTON_CANCEL = "❌ Cancel"
    BUTTON_SKIP = "➡️ Skip"
    BUTTON_FORMS = "📝 Forms"
    """ADMIN BUTTONS"""
    BUTTON_ADMINISTRATION = "🔑 Administration"
    BUTTON_ADMINS = "👥 Admins"
    BUTTON_CHANNEL = "📡 Channel"
    BUTTON_TEMPLATES = "📄 Templates"
    BUTTON_GET_LOGS = "📂 Get logs"
    """CONFIG BUTTONS"""
    BUTTON_CONFIG = "🔧 Config"
    BUTTON_UPDATE_CONFIG = "🔄 Update config"
    """SETTINGS BUTTONS"""
    BUTTON_SETTINGS = "⚙️ Settings"
    BUTTON_MINIMUM_APPROVALS = "⏫ Minimum approvals"
    BUTTON_MINIMUM_REJECTIONS = "⏬ Minimum rejections"
    BUTTON_BACKUP_SETTINGS = "📦 Backup settings"
    BUTTON_RESTORE_SETTINGS = "📤 Restore settings"

    @property
    def menu(self) -> list[str]:
        """Return the menu of the event, which is a list of strings to be used as buttons in the reply.
        If the user is an admin and the event has admin buttons, the menu will be extended with the admin buttons.

        Returns:
            list[str]: The menu of the event.
        """
        buttons = self._menu.copy()
        if self.is_admin:
            buttons += getattr(self, "_admin", [])
        return buttons

    @classmethod
    def button(cls) -> MagicFilter:
        """Returns the filter to catch the event by the button text.

        Returns:
            MagicFilter: The filter to catch the event by the button text.
        """
        return F.text == cls._button


class MainMenu(Event):
    """Event for pressing the main menu button."""

    _button = Event.BUTTON_MAIN_MENU
    _answer = "Now you are in the main menu, use the buttons below to navigate."
    _menu = [Event.BUTTON_FORMS]
    _admin = [Event.BUTTON_ADMINISTRATION]


class Start(MainMenu):
    """Event for starting the bot with the /start command. Almost the same as the main menu event,
    but with the welcome message as an answer."""

    _button = "/start"
    _answer = Config().welcome


class Cancel(MainMenu):
    """Event for pressing the cancel button. Clears the state in reimplementation of the process
    method to exit from the form filling process."""

    _button = Event.BUTTON_CANCEL
    _answer = "Operation canceled."

    async def process(self) -> None:
        """Clear the state to exit from the form filling process."""
        await self.state.clear()


class AdministrationMenu(Event):
    """Event for pressing the settings button. Shows the settings menu with the admin buttons."""

    _button = Event.BUTTON_ADMINISTRATION
    _answer = "In this section you can change the settings of the bot."
    _menu = [
        Event.BUTTON_ADMINS,
        Event.BUTTON_CHANNEL,
        Event.BUTTON_TEMPLATES,
        Event.BUTTON_CONFIG,
        Event.BUTTON_SETTINGS,
        Event.BUTTON_GET_LOGS,
        Event.BUTTON_MAIN_MENU,
    ]


class ConfigMenu(Event):
    """Event for pressing the config button. Shows the config values with the edit buttons."""

    _button = Event.BUTTON_CONFIG
    _answer = "In this section you can change the config of templates."
    _menu = [
        Event.BUTTON_UPDATE_CONFIG,
        Event.BUTTON_MAIN_MENU,
    ]


class SettingsMenu(Event):
    """Event for pressing the settings button. Shows the settings values with the edit buttons."""

    _button = Event.BUTTON_SETTINGS
    _answer = "In this section you can change the settings of the bot."
    _menu = [
        Event.BUTTON_MINIMUM_APPROVALS,
        Event.BUTTON_MINIMUM_REJECTIONS,
        Event.BUTTON_BACKUP_SETTINGS,
        Event.BUTTON_RESTORE_SETTINGS,
        Event.BUTTON_MAIN_MENU,
    ]


class Admins(Event):
    """Event for pressing the admins button. Shows the list of admins with the add and remove buttons."""

    _button = Event.BUTTON_ADMINS
    _menu = []

    async def process(self) -> None:
        """Process the event by showing the list of admins with the add and remove buttons."""
        other_admins = [admin for admin in Settings().admins if admin != self.user_id]
        reply = "List of admins (current user is not displayed):"

        data = {
            f"{RemoveAdmin._text} with ID: {admin}": f"{RemoveAdmin._callback}{admin}"
            for admin in other_admins
        }
        data.update({AddAdmin._text: AddAdmin._callback})
        await self.content.answer(reply, reply_markup=Helper.inline_keyboard(data))


class Channel(Event):
    """Event for pressing the channel button. Shows the channel connection status with the connect
    and disconnect buttons."""

    _button = Event.BUTTON_CHANNEL
    _menu = []

    async def process(self) -> None:
        """Process the event by showing the channel connection status with the connect and disconnect buttons."""
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
    """Event for pressing the templates button. Shows the list of templates with the activate and deactivate buttons."""

    _button = Event.BUTTON_TEMPLATES
    _menu = []

    async def process(self) -> None:
        """Process the event by showing the list of templates with the activate and deactivate buttons."""
        reply = "List of templates:"
        data = {}
        for template in Settings().templates:
            callback = DeactivateTemplate if template.is_active else ActivateTemplate
            data[f"{callback._text}: {template.title}"] = f"{callback._callback}{template.idx}"

        await self.content.answer(reply, reply_markup=Helper.inline_keyboard(data))


class UpdateConfig(Event):
    """Event for pressing the update config button. Launches the config update process."""

    _button = Event.BUTTON_UPDATE_CONFIG
    _menu = []

    async def process(self) -> None:
        """Process the event by launching the config update process."""
        result = Config().update(force=False)
        if result:
            await self.content.answer("Config successfully updated.")
        else:
            await self.content.answer("Config was not updated, please check the logs.")


class GetLogs(Event):
    """Event for pressing the get logs button. Sends the logs to the user."""

    _button = Event.BUTTON_GET_LOGS
    _menu = []

    async def process(self) -> None:
        """Process the event by sending the logs to the user."""

        from src.bot import bot

        archive_path = logger.archive_logs()
        logs = FSInputFile(archive_path)
        await bot.send_document(self.user_id, logs)


class MinimumApprovals(Event):
    """Event for pressing the minimum approvals button. Sets the minimum approvals in settings."""

    _button = Event.BUTTON_MINIMUM_APPROVALS
    _menu = []
    _complete = "Minimum approvals set successfully."

    _minimum_approval_entry = OneOfEntry(
        "Minimum approvals",
        "Incorrect minimum approvals value, it can't be more than the number of admins.",
        "Enter the minimum approvals value. When the form is approved by this number of admins, it will be sent to the channel.",
        options=[str(i) for i in range(1, len(Settings().admins) + 1)],
    )

    _entries = [_minimum_approval_entry]
    _attribute = "min_approval"

    async def process(self) -> None:
        """Process the event by setting the minimum approvals in settings."""
        await super().process()
        new_value = int(next(iter(self.results.values())))
        setattr(Settings(), self._attribute, new_value)


class MinimumRejections(MinimumApprovals):
    """Event for pressing the minimum rejections button. Sets the minimum rejections in settings."""

    _button = Event.BUTTON_MINIMUM_REJECTIONS
    _complete = "Minimum rejections set successfully."
    _attribute = "min_rejection"

    _minimum_rejection_entry = OneOfEntry(
        "Minimum rejections",
        "Incorrect minimum rejections value, it can't be more than the number of admins.",
        "Enter the minimum rejections value. When the form is rejected by this number of admins, it will be removed from the storage.",
        options=[str(i) for i in range(1, len(Settings().admins) + 1)],
    )


class BackupSettings(Event):
    """Event for pressing the backup settings button. Sends the user the JSON file with the settings."""

    _button = Event.BUTTON_BACKUP_SETTINGS
    _menu = []

    async def process(self) -> None:
        """Process the event by saving the settings to the backup file."""
        from src.bot import bot

        settings_path = Settings().json_file
        if not os.path.exists(settings_path):
            await self.content.answer("Settings file not found.")
            return
        settings = FSInputFile(settings_path)
        await bot.send_document(self.user_id, settings)


class RestoreSettings(Event):
    """Event for pressing the restore settings button. Uploads the JSON file with the settings."""

    _button = Event.BUTTON_RESTORE_SETTINGS
    _menu = []
    _complete = "Settings file uploaded received."

    _settings_upload_entry = FileEntry(
        "Settings file",
        "Incorrect settings file, it should be a JSON file.",
        "Upload the settings file to restore.",
    )

    _entries = [_settings_upload_entry]

    async def process(self) -> None:
        """Process the event by restoring the settings from the uploaded file."""
        from src.bot import bot

        await super().process()
        file_id = next(iter(self.results.values()))
        settings_file = await bot.get_file(file_id)
        await bot.download_file(settings_file.file_path, Settings().restored_json_file)
        logger.info(f"Settings file saved to {Settings().restored_json_file}, restoring..")

        try:
            Settings().restore()
            logger.info("Settings restored successfully.")
            await self.content.answer("Settings restored successfully.")
        except Exception as e:
            logger.error(f"Error restoring settings: {e}")
            await self.content.answer("Error restoring settings, ensure the file is correct.")


class Forms(Event):
    """Event for pressing the forms button. Shows the list of forms to fill out with the form buttons."""

    _button = Event.BUTTON_FORMS

    async def process(self) -> None:
        """Process the event by showing the list of forms to fill out with the form buttons."""
        templates = Settings().active_templates
        reply = "Select a form to fill out:"

        data = {template.title: f"{Form._callback}{template.idx}" for template in templates}
        await self.content.answer(reply, reply_markup=Helper.inline_keyboard(data))


class Callback(BaseEvent):
    """Base class for all callback events.
    Each callback event will callback and data_type properties. The first one is the callback prefix
    to catch the event, and the second one is the type of the data to be extracted from the callback.
    """

    @classmethod
    def callback(cls) -> MagicFilter:
        """Returns the filter to catch the callback event.

        Returns:
            MagicFilter: The filter to catch the callback event.
        """
        return F.data.startswith(cls._callback)

    def __init__(self, content: CallbackQuery, state: FSMContext) -> None:
        super().__init__(content, state)
        if not content.data:
            raise ValueError("Callback data is empty.")
        data = content.data.replace(self._callback, "")
        self._data = None if not data else self._data_type(data)

    @property
    def data(self):
        """Return the data extracted from the callback event.
        The data is a split of the callback data with the callback prefix removed."""
        return self._data

    @property
    def answers(self) -> list[str | int] | str | int:
        """If the event has entries, return the answers of the entries.
        If the event has only one entry, return the answer as a single value.

        Returns:
            list[str | int] | str | int: The answers of the entries or the answer as a single value.
        """
        answers = []
        for entry in self.entries:
            answers.append(entry.get_answer(self.results))
        return answers if len(answers) > 1 else answers[0]


class AddAdmin(Callback):
    """Event for adding a new admin. Shows the form with the user ID entry to add as an admin."""

    _text = "➕ Add new admin"
    _callback = "admin__add_admin"
    _data_type = int
    _complete = "Admin added."

    _entries = [NumberEntry("Admin ID", "Incorrect user ID.", "Enter the user ID to add as admin.")]

    async def process(self) -> None:
        """Process the event by adding the new admin."""
        await super().process()
        Settings().add_admin(self.answers)


class RemoveAdmin(Callback):
    """Event for removing an admin."""

    _text = "➖ Remove admin"
    _callback = "admin__remove_admin_"
    _data_type = int
    _answer = "Admin removed."

    async def process(self) -> None:
        """Process the event by removing the admin."""
        Settings().remove_admin(self.data)


class ConnectChannel(Callback):
    """Event for connecting the channel. Tries to connect to the channel with the channel ID entry."""

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
        """Tries to send a message to the channel to check if the bot is connected to the channel.

        Args:
            content (str): The channel ID to connect.

        Returns:
            bool: True if the bot is connected to the channel, otherwise False.
        """

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

    # Replace the validator of the entry with the partial function to pass the entry as an argument.
    _connect_entry.replace_validator(partial(validate_connection, _connect_entry))

    _entries = [_connect_entry]

    async def process(self) -> None:
        """Process the event by connecting the channel."""
        await super().process()
        Settings().channel = self.answers


class DisconnectChannel(Callback):
    """Event for disconnecting the channel."""

    _text = "➖ Disconnect channel"
    _callback = "admin__disconnect_channel_"
    _data_type = int
    _answer = "Channel disconnected."

    async def process(self) -> None:
        """Process the event by disconnecting the channel."""
        Settings().channel = None


class ActivateTemplate(Callback):
    """Event for activating a template."""

    _text = "➕ Activate template"
    _callback = "admin__activate_template_"
    _data_type = int
    _answer = "Template activated."

    async def process(self) -> None:
        """Process the event by activating the template."""
        Settings().activate_template(self.data)


class DeactivateTemplate(Callback):
    """Event for deactivating a template."""

    _text = "➖ Deactivate template"
    _callback = "admin__deactivate_template_"
    _data_type = int
    _answer = "Template deactivated."

    async def process(self) -> None:
        """Process the event by deactivating the template."""
        Settings().deactivate_template(self.data)


class Form(Callback):
    """Event for filling out the form. Shows the form with the entries to fill out and sends the form to the admins."""

    _callback = "user__form_"
    _data_type = int

    async def process(self) -> None:
        """Process the event by filling out the form and sending it to the admins."""
        logger.debug(f"Processing form with template ID: {self.data}")

        # Get the template by the ID extracted from the callback data.
        template = Settings().get_template(self.data)
        logger.debug(f"Get template: {template.title}")

        # Setting the entries and complete message from the template.
        self._entries = template.entries
        self._complete = template.complete or "Form completed."
        await super().process()

        logger.debug(f"Form results: {self.results}")

        # Create a post from the template and save it to the storage.
        post = Post.from_content(template.title, self.results, template.toend, self.content)
        Storage().add_post(post)

        from src.bot import bot

        # Iterate over the admins and send the form to each of them.
        for admin in Settings().admins:
            data = {
                ConfirmForm._text: f"{ConfirmForm._callback}{post.id}",
                RejectForm._text: f"{RejectForm._callback}{post.id}",
            }
            try:
                # In case if the admin was added, but blocked the bot, the message won't be sent.
                await bot.send_message(
                    admin, post.message, reply_markup=Helper.inline_keyboard(data)
                )
            except Exception as e:
                logger.error(f"Error sending form to admin {admin}: {e}")


class ConfirmForm(Callback):
    """Event for confirming the form. Approves the form by the admin."""

    _text = "✅ Confirm"
    _callback = "admin__confirm_form_"
    _data_type = str
    _answer = "Form confirmed."

    # Using this property to implement only one process method for ConfirmForm and RejectForm.
    _storage_method = "approve_by"

    async def process(self) -> None:
        """Process the event by approving the form."""
        post = Storage().get_post(self.data)
        if not post:
            # If the form is not found, it has been removed from the storage.
            # Usually, it happens when the form is approved or rejected already.
            await Helper.force_answer(
                self.content, "Form not found, it may have been approved or rejected already."
            )
            return
        await getattr(post, self._storage_method)(self.user_id)


class RejectForm(ConfirmForm):
    """Event for rejecting the form. Rejects the form by the admin."""

    _text = "❌ Reject"
    _callback = "admin__reject_form_"
    _data_type = str
    _answer = "Form rejected."
    _storage_method = "reject_by"


class EventGroup:
    """Base class for button-based events."""

    @classmethod
    def buttons(cls) -> MagicFilter:
        """Returns the filter to catch multiple events by the button text.

        Returns:
            MagicFilter: The filter to catch multiple events by the button text.
        """
        return F.text.in_([event._button for event in cls._events])

    @classmethod
    def event(cls, message: Message, state: FSMContext) -> Event:
        """Returns the event by the button text. If the event is not found, returns the main menu event.

        Args:
            message (Message): The message to catch the event.
            state (FSMContext): The state of the event.

        Returns:
            Event: The event by the button text or the main menu event if the event is not found.
        """
        for event in cls._events:
            if event._button == message.text:
                return event(message, state)
        return MainMenu(message, state)


class CallbackGroup:
    """Base class for callback events."""

    @classmethod
    def callbacks(cls) -> MagicFilter:
        """Returns the filter to catch multiple events by the callback prefix.

        Returns:
            MagicFilter: The filter to catch multiple events by the callback prefix.
        """
        return F.data.startswith(cls._prefix)

    @classmethod
    def callback(cls, query: CallbackQuery, state: FSMContext) -> Callback | None:
        """Returns the event by the callback prefix. If the event is not found, returns None.

        Args:
            query (CallbackQuery): The callback query to catch the event.
            state (FSMContext): The state of the event.

        Returns:
            Callback | None: The event by the callback prefix or None if the event is not found.
        """
        for event in cls._callbacks:
            if query.data and query.data.startswith(event._callback):
                return event(query, state)


class MenuGroup(EventGroup):
    """Group of events for the main menu."""

    _events = [Start, MainMenu, Cancel, Forms]


class AdminGroup(EventGroup):
    """Group of events for the admin menu."""

    _events = [
        AdministrationMenu,
        ConfigMenu,
        SettingsMenu,
        Admins,
        Channel,
        Templates,
        UpdateConfig,
        GetLogs,
        MinimumApprovals,
        MinimumRejections,
        BackupSettings,
        RestoreSettings,
    ]


class AdminCallbacks(CallbackGroup):
    """Group of callback events for the admin users."""

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
    """Group of callback events for the regular users."""

    _prefix = "user__"
    _callbacks = [Form]
