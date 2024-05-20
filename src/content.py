from aiogram import F
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

import src.globals as g


class ButtonsEN:
    BACK = "🔙 Back"
    """"""
    SETTINGS = "⚙️ Settings"
    FORMS = "📝 Forms"
    """"""
    MENU_MAIN = [FORMS]
    MENU_MAIN_ADMIN = [FORMS, SETTINGS]
    """"""
    ADMINS_BUTTON = "👮‍♀️ Manage admins"
    CHANNEL_BUTTON = "📡 Manage channel"
    """"""
    MENU_SETTINGS = [ADMINS_BUTTON, CHANNEL_BUTTON, BACK]


class ButtonsRU:
    BACK = "🔙 Назад"
    """"""
    SETTINGS = "⚙️ Настройки"
    FORMS = "📝 Формы"
    """"""
    MENU_BUTTONS = [FORMS]
    MENU_ADMIN_BUTTONS = [FORMS, SETTINGS]


class Buttons:
    locales = {
        "en": ButtonsEN,
        "ru": ButtonsRU,
    }

    @classmethod
    def settings_button(cls) -> list[str]:
        res = [cls.locales[locale].SETTINGS for locale in cls.locales]
        return cls.button_in(res)

    @classmethod
    def back_button(cls) -> list[str]:
        res = [cls.locales[locale].BACK for locale in cls.locales]
        return cls.button_in(res)

    @classmethod
    def locale(cls, message: Message) -> str:
        return (
            message.from_user.language_code
            if message.from_user.language_code in cls.locales
            else "en"
        )

    @classmethod
    def main_menu(cls, message: Message) -> list[str]:
        locale = cls.locales[cls.locale(message)]
        buttons = (
            locale.MENU_MAIN_ADMIN
            if g.settings.is_admin(message.from_user.id)
            else locale.MENU_MAIN
        )
        return cls.reply_markup(buttons)

    @classmethod
    def settings_menu(cls, message: Message) -> list[str]:
        locale = cls.locales[cls.locale(message)]
        return Buttons.reply_markup(locale.MENU_SETTINGS)

    @classmethod
    def reply_markup(cls, buttons: list[str]) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text=button)] for button in buttons]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
        )

    @classmethod
    def button_in(cls, buttons: list[str]) -> F:
        return F.text.in_(buttons)
