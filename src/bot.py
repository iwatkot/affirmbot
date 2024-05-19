import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import src.globals as g
from src.logger import Logger
from src.settings import Settings
from src.template import Entry, Template

logger = Logger(__name__)
settings = Settings(g.ADMINS)
dp = Dispatcher()


form_router = Router()


def routers(template: Template) -> callable:
    attributes = [getattr(template.form, entry.title) for entry in template.entries]

    def decorator(func: callable) -> callable:
        for attr in reversed(attributes):
            func = form_router.message(attr)(func)
        return func

    return decorator


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    template = settings.get_template()
    await process_step(template, state, message)

    @routers(template)
    async def process_name(message: Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        step = get_step(current_state, template)

        await state.update_data(**{get_title(current_state): message.text})
        if step == len(template.entries) - 1:
            data = await state.get_data()
            await message.answer(f"Data: {data}")
            return

        next_step = step + 1
        await process_step(template, state, message, next_step)


async def process_step(
    template: Template, state: FSMContext, message: Message, step: int = 0
) -> None:
    await _update_state(template, state, step)
    await _send_answer(template, message, step)


async def _update_state(template: Template, state: FSMContext, step: int = 0) -> None:
    titles = [entry.title for entry in template.entries]
    await state.set_state(getattr(template.form, titles[step]))


async def _send_answer(template: Template, message: Message, step: int = 0) -> None:
    await message.answer(prepare_message(template.entries[step]))


def prepare_message(entry: Entry) -> str:
    message = f"<b>{entry.title}</b>\n\n"
    if entry.description:
        message += f"{entry.description}\n"
    return message


def get_title(current_state: str) -> str:
    return current_state.split(":")[1]


def get_step(current_state: str, template: Template) -> int:
    titles = [entry.title for entry in template.entries]
    for idx, title in enumerate(titles):
        if current_state == getattr(template.form, title):
            return idx


async def main() -> None:
    bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(form_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
