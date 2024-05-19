import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import src.globals as g
from src.decorators import handle_errors, log_message, routers
from src.logger import Logger
from src.settings import Settings
from src.stepper import Stepper

logger = Logger(__name__)
settings = Settings(g.ADMINS)
dp = Dispatcher()
router = Router()


@router.message(CommandStart())
@log_message
@handle_errors
async def command_start(message: Message, state: FSMContext) -> None:
    template = settings.get_template()
    stepper = Stepper(template, state, message)
    await stepper.start()

    @routers(router, template)
    @handle_errors
    async def process_name(message: Message, state: FSMContext) -> None:
        # TODO: Implement answer validation.
        await stepper.update(state, message)

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
