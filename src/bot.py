import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.decorators import admin_only, callback, event_router, events, handle_errors
from src.event import AddAdmin, AdminGroup, Callback, Event, MenuGroup
from src.globals import TOKEN, settings
from src.logger import Logger
from src.stepper import Stepper

logger = Logger(__name__)
dp = Dispatcher()
router = Router(name="main_router")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@events(MenuGroup)
async def menu_group(event: Event) -> None:
    await event.message.answer(
        event.answer,
        reply_markup=event.menu,
    )
    await event.process()


@events(AdminGroup)
@admin_only
async def admin_group(event: Event) -> None:
    await event.message.answer(
        event.answer,
        reply_markup=event.menu,
    )
    await event.process()


@router.message(Command("form"))
@handle_errors
async def process_form(message: Message, state: FSMContext) -> None:
    template = settings.get_template()
    stepper = Stepper(message, state, template=template)
    await stepper.start()


@callback(AddAdmin)
@admin_only
async def add_admin(callback: Callback):
    await bot.send_message(
        callback.user_id,
        callback.answer,
    )
    await callback.process()


@handle_errors
async def main() -> None:
    dp.include_routers(router, event_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
