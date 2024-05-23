import traceback
from functools import wraps

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from event import Callback, Event, EventGroup
from src.logger import Logger
from src.template import Template

logger = Logger(__name__)
event_router = Router(name="event_router")


def form(template: Template) -> callable:
    attributes = [getattr(template.form, entry.title) for entry in template.entries]

    def decorator(func: callable) -> callable:
        for attr in reversed(attributes):
            func = event_router.message(attr)(func)
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
    async def wrapper(event: Event, *args, **kwargs):
        if event.is_admin:
            return await func(event, *args, **kwargs)
        else:
            logger.warning(f"User {event.message.from_user.id} tried to access admin-only command.")
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
        async def wrapper(message: Message, state: FSMContext) -> None:
            return await func(message, event(message, state))

        return wrapper

    return decorator


def events(events: EventGroup):
    def decorator(func):
        @event_router.message(events.buttons())
        async def wrapper(message: Message, state: FSMContext) -> None:
            return await func(events.event(message, state))

        return wrapper

    return decorator


def callback(callback: Callback):
    def decorator(func):
        @event_router.callback_query(callback.callback())
        async def wrapper(query: CallbackQuery) -> None:
            return await func(callback(query))

        return wrapper

    return decorator
