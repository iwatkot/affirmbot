import asyncio
from typing import cast

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.decorators import (
    admin_only,
    callbacks,
    event_router,
    events,
    handle_errors,
    moderator_admin_only,
)
from src.event import (
    AdminCallbacks,
    AdminGroup,
    Callback,
    Event,
    MenuGroup,
    ModeratorAdminCallbacks,
    UserCallbacks,
)
from src.globals import TOKEN
from src.logger import Logger

logger = Logger(__name__)
dp = Dispatcher()
router = Router(name="main_router")
bot = Bot(token=cast(str, TOKEN), default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@events(MenuGroup)
@handle_errors
async def menu_group(event: Event) -> None:
    """Menu group event handler.

    Args:
        event (Event): Event object.
    """
    await event.reply()
    await event.process()


@events(AdminGroup)
@handle_errors
@admin_only
async def admin_group(event: Event) -> None:
    """Admin group event handler.

    Args:
        event (Event): Event object.
    """
    await event.reply()
    await event.process()


@callbacks(AdminCallbacks)
@handle_errors
@admin_only
async def admin_callbacks(callback: Callback) -> None:
    """Admin callbacks handler.

    Args:
        callback (Callback): Callback object.
    """
    await callback.reply()
    await callback.process()


@callbacks(ModeratorAdminCallbacks)
@handle_errors
@moderator_admin_only
async def moderator_admin_callbacks(callback: Callback) -> None:
    """Moderator and admin callbacks handler.

    Args:
        callback (Callback): Callback object.
    """
    await callback.reply()
    await callback.process()


@callbacks(UserCallbacks)
@handle_errors
async def user_callbacks(callback: Callback) -> None:
    """User callbacks handler.

    Args:
        callback (Callback): Callback object.
    """
    await callback.reply()
    await callback.process()


@handle_errors
async def main() -> None:
    """Main function to start the bot."""
    dp.include_routers(router, event_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Bot is starting...")
    asyncio.run(main())
