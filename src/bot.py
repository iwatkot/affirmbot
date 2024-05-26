import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.decorators import admin_only, callback, event_router, events, handle_errors
from src.event import AddAdmin, AdminGroup, Callback, Event, Form, MenuGroup
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


@router.message(Command("form"))
@handle_errors
async def process_form(message: Message, state: FSMContext) -> None:
    template = settings.active_templates[0]
    stepper = Stepper(message, state, template=template)
    await stepper.start()


@callback(AddAdmin)
@handle_errors
@admin_only
async def add_admin(callback: Callback):
    await callback.reply()
    await callback.process()


@callback(Form)
@handle_errors
async def form(callback: Callback):
    await callback.reply()
    await callback.process()


@handle_errors
async def main() -> None:
    dp.include_routers(router, event_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
