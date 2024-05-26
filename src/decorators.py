import traceback
from functools import wraps

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import src.globals as g
from event import Callback, CallbackGroup, Event, EventGroup
from src.form import get_form
from src.logger import Logger

logger = Logger(__name__)
event_router = Router(name="event_router")


def form(steps: list[str]) -> callable:
    attributes = [getattr(get_form(steps), step) for step in steps]

    def decorator(func: callable) -> callable:
        for attr in reversed(attributes):
            func = event_router.message(attr)(func)
        return func

    return decorator


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
            if g.is_development:
                raise e
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
        async def wrapper(query: CallbackQuery, state: FSMContext) -> None:
            return await func(callback(query, state))

        return wrapper

    return decorator


def callbacks(callbacks: CallbackGroup):
    def decorator(func):
        @event_router.callback_query(callbacks.callbacks())
        async def wrapper(query: CallbackQuery, state: FSMContext) -> None:
            return await func(callbacks.callback(query, state))

        return wrapper

    return decorator
