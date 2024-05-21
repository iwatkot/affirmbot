import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import src.content as content
import src.globals as g
from src.content import Event
from src.decorators import admin_only, handle_errors, log_message, routers
from src.logger import Logger
from src.stepper import Stepper

logger = Logger(__name__)
dp = Dispatcher()
router = Router()
bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def event(event: Event):
    def decorator(func):
        @dp.message(event.button())
        async def wrapper(message) -> None:
            return await func(message, event)

        return wrapper

    return decorator


@event(content.Start)
async def start(message: Message, event: Event) -> None:
    await message.answer(
        event.answer(),
        reply_markup=event.menu(message=message),
    )


@event(content.MainMenu)
async def main_menu(message: Message, event: Event) -> None:
    await message.answer(
        event.answer(),
        reply_markup=event.menu(message=message),
    )


@event(content.Settings)
@admin_only
async def settings(message: Message, event: Event) -> None:
    await message.answer(
        event.answer(),
        reply_markup=event.menu(message=message),
    )


@router.message(Command("form"))
@log_message
@handle_errors
async def command_start(message: Message, state: FSMContext) -> None:
    template = g.settings.get_template()
    stepper = Stepper(message, state, template)
    await stepper.start()

    @routers(router, template)
    @handle_errors
    async def steps(message: Message, state: FSMContext) -> None:
        if not await stepper.validate(message):
            return

        await stepper.update(message, state)

        if stepper.ended:
            await stepper.close()
            return

        await stepper.forward()


@handle_errors
async def main() -> None:
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
