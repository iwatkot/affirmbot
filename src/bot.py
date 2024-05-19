import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import src.globals as g
from src.decorators import handle_errors, routers
from src.logger import Logger
from src.settings import Settings
from src.stepper import Stepper

logger = Logger(__name__)
settings = Settings(g.ADMINS)
dp = Dispatcher()


form_router = Router()


@form_router.message(CommandStart())
@handle_errors
async def command_start(message: Message, state: FSMContext) -> None:
    template = settings.get_template()
    stepper = Stepper(template, state, message)
    await stepper.start()

    @routers(form_router, template)
    @handle_errors
    async def process_name(message: Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        stepper.current_state = current_state
        stepper.message = message

        await state.update_data(**stepper.data)

        if stepper.step == len(template.entries):
            data = await state.get_data()
            await message.answer(f"Data: {data}")
            return

        await stepper.forward()


@handle_errors
async def main() -> None:
    bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(form_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
