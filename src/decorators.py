import traceback
from functools import wraps

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import src.globals as g
from event import Callback, CallbackGroup, Event, EventGroup
from src.logger import Logger
from src.utils import get_form

logger = Logger(__name__)
event_router = Router(name="event_router")


def form(steps: list[str]) -> callable:
    """Decorator to register multiple form steps for event handler.

    Args:
        steps (list[str]): List of form steps.

    Returns:
        callable: Decorator function.
    """
    attributes = [getattr(get_form(steps), step) for step in steps]

    def decorator(func: callable) -> callable:
        """Iterates over form steps and registers event handlers for each step.

        Args:
            func (callable): Function to decorate.

        Returns:
            callable: Decorated function.
        """
        for attr in reversed(attributes):
            func = event_router.message(attr)(func)
        return func

    return decorator


def admin_only(func: callable) -> callable:
    """Decorator to restrict access to admin-only commands.
    If user of the event is not admin, log warning and return.

    Args:
        func (callable): Function to decorate.

    Returns:
        callable: Decorated function.
    """

    @wraps(func)
    async def wrapper(event: Event, *args, **kwargs) -> None:
        """Check if user is admin and call decorated function.

        Args:
            event (Event): Event object.
        """
        if event.is_admin:
            return await func(event, *args, **kwargs)
        else:
            logger.warning(f"User {event.message.from_user.id} tried to access admin-only command.")
            return

    return wrapper


def moderator_admin_only(func: callable) -> callable:
    """Decorator to restrict access to commands which available for moderators and admins.
    If user of the event is not moderator or admin, log warning and return.

    Args:
        func (callable): Function to decorate.

    Returns:
        callable: Decorated function.
    """

    @wraps(func)
    async def wrapper(event: Event, *args, **kwargs) -> None:
        """Check if user is moderator or admin and call decorated function.

        Args:
            event (Event): Event object.
        """
        if event.is_moderator or event.is_admin:
            return await func(event, *args, **kwargs)
        else:
            logger.warning(
                f"User {event.message.from_user.id} tried to access moderator-plus-only command."
            )
            return

    return wrapper


def handle_errors(func: callable) -> callable:
    """Decorator to handle exceptions in event handlers.
    Logs error and traceback, and raises exception in development mode.

    Args:
        func (callable): Function to decorate.

    Returns:
        callable: Decorated function.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> None:
        """Call decorated function and handle exceptions."""
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


def event(event: Event) -> callable:
    """Decorator to register event handler for a single event.

    Args:
        event (Event): Event object.

    Returns:
        callable: Decorator function.
    """

    def decorator(func: callable) -> callable:
        """Register event handler for event.

        Args:
            func (callable): Function to decorate.

        Returns:
            callable: Decorated function.
        """

        @event_router.message(event.button())
        async def wrapper(message: Message, state: FSMContext) -> None:
            """Call decorated function with event object.

            Args:
                message (Message): Message object.
                state (FSMContext): FSMContext object.
            """
            return await func(message, event(message, state))

        return wrapper

    return decorator


def events(events: EventGroup) -> callable:
    """Decorator to register event handler for multiple events.

    Args:
        events (EventGroup): EventGroup object.

    Returns:
        callable: Decorator function.
    """

    def decorator(func: callable) -> callable:
        """Register event handler for multiple events.

        Args:
            func (callable): Function to decorate.

        Returns:
            callable: Decorated function.
        """

        @event_router.message(events.buttons())
        async def wrapper(message: Message, state: FSMContext) -> None:
            """Call decorated function with event object.

            Args:
                message (Message): Message object.
                state (FSMContext): FSMContext object.
            """
            return await func(events.event(message, state))

        return wrapper

    return decorator


def callback(callback: Callback) -> callable:
    """Decorator to register callback handler for a single callback.

    Args:
        callback (Callback): Callback object.

    Returns:
        callable: Decorator function.
    """

    def decorator(func: callable) -> callable:
        """Register callback handler for callback.

        Args:
            func (callable): Function to decorate.

        Returns:
            callable: Decorated function.
        """

        @event_router.callback_query(callback.callback())
        async def wrapper(query: CallbackQuery, state: FSMContext) -> None:
            """Call decorated function with callback object.

            Args:
                query (CallbackQuery): CallbackQuery object.
                state (FSMContext): FSMContext object.
            """
            return await func(callback(query, state))

        return wrapper

    return decorator


def callbacks(callbacks: CallbackGroup) -> callable:
    """Decorator to register callback handler for multiple callbacks.

    Args:
        callbacks (CallbackGroup): CallbackGroup object.

    Returns:
        callable: Decorator function.
    """

    def decorator(func: callable) -> callable:
        """Register callback handler for multiple callbacks.

        Args:
            func (callable): Function to decorate.

        Returns:
            callable: Decorated function.
        """

        @event_router.callback_query(callbacks.callbacks())
        async def wrapper(query: CallbackQuery, state: FSMContext) -> None:
            """Call decorated function with callback object.

            Args:
                query (CallbackQuery): CallbackQuery object.
                state (FSMContext): FSMContext object.
            """
            return await func(callbacks.callback(query, state))

        return wrapper

    return decorator
