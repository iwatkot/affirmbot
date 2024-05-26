import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.decorators import admin_only, callbacks, event_router, events, handle_errors
from src.event import (
    AdminCallbacks,
    AdminGroup,
    Callback,
    Event,
    MenuGroup,
    UserCallbacks,
)
from src.globals import TOKEN, settings
from src.logger import Logger
from src.stepper import Stepper

logger = Logger(__name__)
dp = Dispatcher()
router = Router(name="main_router")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@events(MenuGroup)
@handle_errors
async def menu_group(event: Event) -> None:
    await event.reply()
    await event.process()


@events(AdminGroup)
@handle_errors
@admin_only
async def admin_group(event: Event) -> None:
    await event.reply()
    await event.process()


@callbacks(AdminCallbacks)
@handle_errors
@admin_only
async def admin_callbacks(callback: Callback) -> None:
    await callback.reply()
    await callback.process()


@callbacks(UserCallbacks)
@handle_errors
async def user_callbacks(callback: Callback) -> None:
    await callback.reply()
    await callback.process()


@handle_errors
async def main() -> None:
    dp.include_routers(router, event_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
