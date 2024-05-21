from aiogram import F
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

import src.globals as g


class AnswersEN:
    MAIN_MENU = "Welcome to the main menu."
    """"""
    SETTINGS = "Here you can set up the bot."


class AnswersRU:
    MAIN_MENU = "Добро пожаловать в главное меню."
    """"""
    SETTINGS = "Здесь вы можете настроить бота."


class ButtonsEN:
    BUTTON_MAIN_MENU = "🏠 Main menu"
    """"""
    BUTTON_SETTINGS = "⚙️ Settings"
    BUTTON_FORMS = "📝 Forms"
    """"""
    MENU_MAIN = [BUTTON_FORMS]
    MENU_MAIN_ADMIN = [BUTTON_FORMS, BUTTON_SETTINGS]
    """"""
    BUTTON_ADMINS = "👮‍♀️ Manage admins"
    BUTTON_CHANNELS = "📡 Manage channel"
    """"""
    MENU_SETTINGS = [BUTTON_ADMINS, BUTTON_CHANNELS, BUTTON_MAIN_MENU]


class ButtonsRU:
    BUTTON_MAIN_MENU = "🏠 Главное меню"
    """"""
    BUTTON_SETTINGS = "⚙️ Настройки"
    BUTTON_FORMS = "📝 Формы"
    """"""
    MENU_MAIN = [BUTTON_FORMS]
    MENU_MAIN_ADMIN = [BUTTON_FORMS, BUTTON_SETTINGS]
    """"""
    BUTTON_ADMINS = "👮‍♀️ Управление админами"
    BUTTON_CHANNELS = "📡 Управление каналом"
    """"""
    MENU_SETTINGS = [BUTTON_ADMINS, BUTTON_CHANNELS, BUTTON_MAIN_MENU]


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
    def settings(self) -> list[str]:
        return self.button_in("BUTTON_SETTINGS")

    @property
    def main_menu(self) -> list[str]:
        return self.button_in("BUTTON_MAIN_MENU")

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


class Answers(BaseMarkup):
    locales = {
        "en": AnswersEN,
        "ru": AnswersRU,
    }

    def main_menu(self, message: Message) -> str:
        return self.locales[self.locale(message)].MAIN_MENU

    def settings(self, message: Message) -> str:
        return self.locales[self.locale(message)].SETTINGS


Button = Buttons()
Menu = Menus()
Answer = Answers()
