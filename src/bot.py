import asyncio

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

import src.globals as g
from src.logger import Logger
from src.state import State

logger = Logger(__name__)
state = State(g.ADMINS)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {html.bold(message.from_user.id)}!")


@dp.message(Command("template"))
async def command_template_handler(message: Message) -> None:
    """
    This handler receives messages with `/template` command
    """
    template = state.get_template()
    for entry in template.entries:
        await message.answer(str(entry))


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=g.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
