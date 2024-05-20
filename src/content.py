from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

import src.globals as g


class ButtonsEN:
    SETTINGS = "⚙️ Settings"
    FORMS = "📝 Forms"

    MENU_BUTTONS = [FORMS]
    MENU_ADMIN_BUTTONS = [FORMS, SETTINGS]


class ButtonsRU:
    SETTINGS = "⚙️ Настройки"
    FORMS = "📝 Формы"

    MENU_BUTTONS = [FORMS]
    MENU_ADMIN_BUTTONS = [FORMS, SETTINGS]


class Buttons:
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
    def main_menu(cls, message: Message) -> list[str]:
        locale = cls.locales[cls.locale(message)]
        buttons = (
            locale.MENU_ADMIN_BUTTONS
            if g.settings.is_admin(message.from_user.id)
            else locale.MENU_BUTTONS
        )
        return Buttons.reply_markup(buttons)

    @classmethod
    def reply_markup(cls, buttons: list[str]) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text=button)] for button in buttons]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
        )
