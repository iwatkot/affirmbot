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
from src.template import Entry
from src.utils import CombinedMeta

logger = Logger(__name__)
settings = Settings(g.ADMINS)
dp = Dispatcher()


form_router = Router()


def routers(form: StatesGroup, titles: list[str]) -> callable:
    attributes = [getattr(form, attr) for attr in titles]

    def decorator(func: callable) -> callable:
        for attr in reversed(attributes):
            func = form_router.message(attr)(func)
        return func

    return decorator


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    template = settings.get_template()
    entries = template.get_entries()
    titles = [entry.title for entry in template.get_entries()]

    class Form(StatesGroup, metaclass=CombinedMeta, titles=titles):
        pass

    first_entry = entries[0]

    await state.set_state(getattr(Form, first_entry.title))
    await message.answer(prepare_message(first_entry))

    @routers(Form, titles)
    async def process_name(message: Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        step = get_step(Form, current_state, titles)

        await state.update_data(**{get_title(current_state): message.text})
        if step == len(entries) - 1:
            data = await state.get_data()
            await message.answer(f"Data: {data}")
            return

        next_step = step + 1
        await state.set_state(getattr(Form, titles[next_step]))
        await message.answer(prepare_message(entries[next_step]))


def prepare_message(entry: Entry) -> str:
    message = f"<b>{entry.title}</b>\n\n"
    if entry.description:
        message += f"{entry.description}\n"
    return message


def get_title(current_state: str) -> str:
    return current_state.split(":")[1]


def get_step(form: StatesGroup, current_state: str, titles: list[str]) -> int:
    for idx, title in enumerate(titles):
        if current_state == getattr(form, title):
            return idx


async def main() -> None:
    bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(form_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
