import os
import traceback
from datetime import datetime
from functools import wraps

from aiogram import Router

from src.logger import LOG_DIR, Logger
from src.template import Template

logger = Logger(__name__)
TB_DIR = os.path.join(LOG_DIR, "tracebacks")
os.makedirs(TB_DIR, exist_ok=True)


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
        logger.debug(message.text, message.from_user.id, message.from_user.first_name)
        return await func(message, *args, **kwargs)

    return wrapper


def handle_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"An error occurred in {func.__module__}.{func.__name__}: {repr(e)}")
            try:
                dump_traceback(traceback.format_exc())
            except Exception:
                pass

    return wrapper


def dump_traceback(tb: traceback) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    save_path = os.path.join(TB_DIR, f"{timestamp}.txt")
    with open(save_path, "w") as f:
        f.write(tb)

    logger.error(f"Traceback saved to {save_path}")