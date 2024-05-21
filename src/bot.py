import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import src.globals as g
from src.content import Answer, Button, Menu
from src.decorators import admin_only, handle_errors, log_message, routers
from src.logger import Logger
from src.stepper import Stepper

logger = Logger(__name__)
dp = Dispatcher()
router = Router()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        g.config.welcome,
        reply_markup=Menu.main(message),
    )


@dp.message(Button.main_menu)
async def back(message: Message) -> None:
    await message.answer(
        Answer.main_menu(message),
        reply_markup=Menu.main(message),
    )


@dp.message(Button.settings)
@admin_only
async def settings(message: Message) -> None:
    await message.answer(
        Answer.settings(message),
        reply_markup=Menu.settings(message),
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
    bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
