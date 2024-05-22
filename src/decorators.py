import traceback
from functools import wraps

from aiogram import Router
from aiogram.types import CallbackQuery, Message

import src.globals as g
from event import Callback, Event, EventGroup
from src.logger import Logger
from src.template import Template

logger = Logger(__name__)
event_router = Router(name="event_router")


def routers(router: Router, template: Template) -> callable:
    attributes = [getattr(template.form, entry.title) for entry in template.entries]

    def decorator(func: callable) -> callable:
        for attr in reversed(attributes):
            func = router.message(attr)(func)
        return func

    return decorator


def log_message(func):
    @wraps(func)
    async def wrapper(message, *args, **kwargs):
        logger.debug(
            f"ID: {message.from_user.id} | "
            f"Name: {message.from_user.first_name} {message.from_user.last_name} | "
            f"Message: {message.text}"
        )
        return await func(message, *args, **kwargs)

    return wrapper


def admin_only(func):
    @wraps(func)
    async def wrapper(message: Message | CallbackQuery, *args, **kwargs):
        if g.settings.is_admin(message.from_user.id):
            return await func(message, *args, **kwargs)
        else:
            logger.warning(f"User {message.from_user.id} tried to access admin-only command.")
            return

    return wrapper


def handle_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"An error occurred in {func.__module__}.{func.__name__}: {repr(e)}")
            try:
                logger.dump_traceback(traceback.format_exc())
            except Exception:
                pass

    return wrapper


def event(event: Event):
    def decorator(func):
        @event_router.message(event.button())
        async def wrapper(message: Message) -> None:
            return await func(message, event(message))

        return wrapper

    return decorator


def events(events: EventGroup):
    def decorator(func):
        @event_router.message(events.buttons())
        async def wrapper(message: Message) -> None:
            return await func(message, events.event(message))

        return wrapper

    return decorator


def callback(callback: Callback):
    def decorator(func):
        @event_router.callback_query(callback.callback())
        async def wrapper(query: CallbackQuery) -> None:
            return await func(query, callback(query))

        return wrapper

    return decorator
