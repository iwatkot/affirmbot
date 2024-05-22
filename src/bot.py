import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import src.globals as g
from src.decorators import (
    admin_only,
    event_router,
    events,
    handle_errors,
    log_message,
    routers,
)
from src.event import AdminGroup, Event, MenuGroup
from src.logger import Logger
from src.stepper import Stepper

logger = Logger(__name__)
dp = Dispatcher()
router = Router(name="main_router")
bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@events(MenuGroup)
async def menu_group(message: Message, event: Event) -> None:
    await message.answer(
        event.answer,
        reply_markup=event.menu,
    )
    await event.process(message)


@events(AdminGroup)
@admin_only
async def settings(message: Message, event: Event) -> None:
    await message.answer(
        event.answer,
        reply_markup=event.menu,
    )
    await event.process(message)


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
    dp.include_routers(router, event_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
