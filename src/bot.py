import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import src.globals as g
from src.decorators import (
    admin_only,
    callback,
    event_router,
    events,
    form,
    handle_errors,
)
from src.event import AddAdmin, AdminGroup, Callback, Event, MenuGroup
from src.logger import Logger
from src.stepper import Stepper

logger = Logger(__name__)
dp = Dispatcher()
router = Router(name="main_router")
bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@events(MenuGroup)
async def menu_group(event: Event) -> None:
    await event.message.answer(
        event.answer,
        reply_markup=event.menu,
    )
    await event.process()


@events(AdminGroup)
@admin_only
async def settings(event: Event) -> None:
    await event.message.answer(
        event.answer,
        reply_markup=event.menu,
    )
    await event.process()


@router.message(Command("form"))
@handle_errors
async def command_start(message: Message, state: FSMContext) -> None:
    template = g.settings.get_template()
    stepper = Stepper(message, state, template)
    await stepper.start()

    @form(template)
    @handle_errors
    async def steps(message: Message | CallbackQuery, state: FSMContext) -> None:
        if not await stepper.validate(message):
            return

        await stepper.update(message, state)

        if stepper.ended:
            await stepper.close()
            return

        await stepper.forward()


@callback(AddAdmin)
@admin_only
async def add_admin(callback: Callback):
    await bot.send_message(
        callback.user_id,
        callback.answer,
    )


@handle_errors
async def main() -> None:
    dp.include_routers(router, event_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
