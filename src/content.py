from aiogram import F
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

import src.globals as g


class AnswersEN:
    MAIN_MENU = "Welcome to the main menu."
    CANCEL = "Operation canceled."
    """"""
    SETTINGS = "Here you can set up the bot."
    """"""
    CHANNEL = "The bot is currently sending posts to the channel with ID: {channel_id}."
    EDIT_CHANNEL = "Enter the channel ID for the bot to send posts to."


class AnswersRU:
    MAIN_MENU = "Добро пожаловать в главное меню."
    CANCEL = "Операция отменена."
    """"""
    SETTINGS = "Здесь вы можете настроить бота."
    """"""
    CHANNEL = "Бот в данный момент отправляет посты в канал с ID: {channel_id}."
    EDIT_CHANNEL = "Введите ID канала, в который бот будет отправлять посты."


class ButtonsEN:
    BUTTON_MAIN_MENU = "🏠 Main menu"
    BUTTON_CANCEL = "❌ Cancel"
    """"""
    BUTTON_SETTINGS = "⚙️ Settings"
    BUTTON_FORMS = "📝 Forms"
    """"""
    MENU_MAIN = [BUTTON_FORMS]
    MENU_MAIN_ADMIN = [BUTTON_FORMS, BUTTON_SETTINGS]
    """"""
    BUTTON_ADMINS = "👮‍♀️ Manage admins"
    BUTTON_CHANNEL = "📡 Manage channel"
    BUTTON_EDIT_CHANNEL = "📡 Edit channel"
    """"""
    MENU_SETTINGS = [BUTTON_ADMINS, BUTTON_CHANNEL, BUTTON_MAIN_MENU]
    MENU_CHANNEL = [BUTTON_EDIT_CHANNEL, BUTTON_MAIN_MENU]


class ButtonsRU:
    BUTTON_MAIN_MENU = "🏠 Главное меню"
    BUTTON_CANCEL = "❌ Отмена"
    """"""
    BUTTON_SETTINGS = "⚙️ Настройки"
    BUTTON_FORMS = "📝 Формы"
    """"""
    MENU_MAIN = [BUTTON_FORMS]
    MENU_MAIN_ADMIN = [BUTTON_FORMS, BUTTON_SETTINGS]
    """"""
    BUTTON_ADMINS = "👮‍♀️ Управление админами"
    BUTTON_CHANNEL = "📡 Управление каналом"
    BUTTON_EDIT_CHANNEL = "📡 Изменить канал"
    """"""
    MENU_SETTINGS = [BUTTON_ADMINS, BUTTON_CHANNEL, BUTTON_MAIN_MENU]
    MENU_CHANNEL = [BUTTON_EDIT_CHANNEL, BUTTON_MAIN_MENU]


class BaseMarkup:
    locales = {
        "en": ButtonsEN,
        "ru": ButtonsRU,
    }

    @classmethod
    def locale(cls, message: Message) -> str:
        return (
            message.from_user.language_code
            if message.from_user.language_code in cls.locales
            else "en"
        )

    @classmethod
    def reply_markup(cls, buttons: list[str]) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text=button)] for button in buttons]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
        )


class Buttons(BaseMarkup):
    @property
    def settings(self) -> F:
        return self.button_in("BUTTON_SETTINGS")

    @property
    def main_menu(self) -> F:
        return self.button_in("BUTTON_MAIN_MENU")

    @property
    def cancel(self) -> F:
        return self.button_in("BUTTON_CANCEL")

    @property
    def edit_channel(self) -> F:
        return self.button_in("BUTTON_EDIT_CHANNEL")

    @property
    def channel(self) -> F:
        return self.button_in("BUTTON_CHANNEL")

    def button_in(self, attribute: str) -> F:
        buttons = [getattr(locale, attribute) for locale in self.locales.values()]
        return F.text.in_(buttons)


class Menus(BaseMarkup):
    def main(self, message: Message) -> ReplyKeyboardMarkup:
        locale = self.locales[self.locale(message)]
        buttons = (
            locale.MENU_MAIN_ADMIN
            if g.settings.is_admin(message.from_user.id)
            else locale.MENU_MAIN
        )
        return self.reply_markup(buttons)

    def settings(cls, message: Message) -> ReplyKeyboardMarkup:
        locale = cls.locales[cls.locale(message)]
        return cls.reply_markup(locale.MENU_SETTINGS)

    def channel(cls, message: Message) -> ReplyKeyboardMarkup:
        locale = cls.locales[cls.locale(message)]
        return cls.reply_markup(locale.MENU_CHANNEL)

    def edit_channel(cls, message: Message) -> ReplyKeyboardMarkup:
        locale = cls.locales[cls.locale(message)]
        return cls.reply_markup([locale.BUTTON_CANCEL])


class Answers(BaseMarkup):
    locales = {
        "en": AnswersEN,
        "ru": AnswersRU,
    }

    def main_menu(self, message: Message) -> str:
        return self.locales[self.locale(message)].MAIN_MENU

    def settings(self, message: Message) -> str:
        return self.locales[self.locale(message)].SETTINGS

    def channel(self, message: Message) -> str:
        current_channel = g.settings.channel or "None"
        return self.locales[self.locale(message)].CHANNEL.format(channel_id=current_channel)

    def edit_channel(self, message: Message) -> str:
        return self.locales[self.locale(message)].EDIT_CHANNEL

    def cancel(self, message: Message) -> str:
        return self.locales[self.locale(message)].CANCEL


Button = Buttons()
Menu = Menus()
Answer = Answers()
