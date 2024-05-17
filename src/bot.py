import asyncio

from aiogram import Bot, Dispatcher, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

import src.globals as g
from src.logger import Logger
from src.settings import Settings
from src.utils import CombinedMeta

logger = Logger(__name__)
settings = Settings(g.ADMINS)
dp = Dispatcher()


form_router = Router()


# class Form(StatesGroup):
#     name = State()
#     like_bots = State()
#     language = State()


def apply_form_decorators(attributes):
    def decorator(func):
        for attr in reversed(attributes):
            func = form_router.message(attr)(func)
        return func

    return decorator


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    template = settings.get_template()
    entries = [entry.title for entry in template.get_entries()]

    class Form(StatesGroup, metaclass=CombinedMeta, entries=entries):
        pass

    await state.set_state(getattr(Form, entries[0]))
    await message.answer(
        "Hi there! What's your name?",
    )

    @apply_form_decorators([getattr(Form, attr) for attr in entries])
    async def process_name(message: Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        if current_state == getattr(Form, entries[0]):
            await state.update_data(name=message.text)
            await state.set_state(getattr(Form, entries[1]))
            await message.answer("STEP 1")
        elif current_state == getattr(Form, entries[1]):
            await state.update_data(like_bots=message.text)
            await state.set_state(getattr(Form, entries[2]))
            await message.answer("STEP 2")
        elif current_state == getattr(Form, entries[2]):
            await state.update_data(language=message.text)
            data = await state.get_data()
            await message.answer(f"Data: {data}")


# @dp.message(Command("template"))
# async def command_template_handler(message: Message, state: FSMContext) -> None:
#     class Form(StatesGroup):
#         name = State()
#         like_bots = State()
#         language = State()

#     attributes = [Form.name, Form.like_bots, Form.language]
#     await state.set_state(Form.name)

#     # template = settings.get_template()
#     # for entry in template.entries:
#     #     await message.answer(str(entry))
#     @apply_form_decorators(attributes)
#     def your_function(message: Message, state: FSMContext):
#         print(message.text)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(form_router)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
