from __future__ import annotations

from datetime import datetime

import src.globals as g
from src.logger import Logger
from src.utils import Modes

logger = Logger(__name__)


class Template:
    def __init__(
        self,
        title: str,
        description: str = None,
        entries: list[Entry] | list[dict[str, str | list[str]]] = None,
        complete: str = None,
        active: bool = True,
    ):
        self._title = title
        self._description = description
        self._entries = [Entry.from_json(entry) for entry in entries] if entries else []
        self._complete = complete
        self._active = active
        self._idx = None

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def entries(self) -> list[Entry]:
        return self._entries.copy()

    @property
    def complete(self) -> str:
        return self._complete

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self._active = value

    @property
    def disable(self) -> bool:
        self.active = False

    @property
    def enable(self) -> bool:
        self.active = True

    @property
    def is_active(self) -> bool:
        return self.active

    def get_entry(self, idx: int) -> Entry:
        return self.entries[idx]

    def __repr__(self) -> str:
        return f"Form title='{self.title}' | description='{self.description}' | entries='{self.entries}'"


class Entry:
    def __init__(
        self,
        title: str,
        incorrect: str,
        description: str = None,
        options: list[str] = None,
        **kwargs,
    ):
        self.title = title
        self.incorrect = incorrect
        self.description = description
        self.options = options

    @classmethod
    def from_json(cls, data: dict[str, str | list[str]]) -> Entry:
        mode_to_class = {
            Modes.TEXT: TextEntry,
            Modes.DATE: DateEntry,
            Modes.ONEOF: OneOfEntry,
        }
        mode = data.get(Modes.MODE)
        if mode not in mode_to_class:
            logger.warning(f"Invalid mode: {mode}, supported modes: {list(mode_to_class.keys())}")
            return
        return mode_to_class[mode](**data)

    def __repr__(self) -> str:
        return f"Entry title='{self.title}' | description='{self.description}' | options='{self.options}'"

    async def validate_answer(self, content: str) -> bool:
        raise NotImplementedError

    def get_answer(self, results: dict[str, str]) -> str | int:
        return self.base_type(results[self.title])


class TextEntry(Entry):
    def __init__(self, title: str, incorrect: str, description: str = None, **kwargs):
        super().__init__(title, incorrect, description, **kwargs)

    async def validate_answer(self, content: str) -> bool:
        try:
            assert isinstance(content, str)
            return True
        except AssertionError:
            return False


class NumberEntry(Entry):
    base_type = int

    def __init__(self, title: str, incorrect: str, description: str = None, **kwargs):
        super().__init__(title, incorrect, description, **kwargs)

    async def validate_answer(self, content: str) -> bool:
        try:
            assert content.isdigit()
            return True
        except AssertionError:
            return False


class DateEntry(Entry):

    def __init__(self, title: str, incorrect: str, description: str = None, **kwargs):
        super().__init__(title, incorrect, description, **kwargs)

    async def validate_answer(self, content: str) -> bool:
        if g.is_development:
            return True
        date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y"]
        for date_format in date_formats:
            try:
                datetime.strptime(content, date_format)
                return True
            except ValueError:
                continue
        return False


class OneOfEntry(Entry):

    def __init__(
        self,
        title: str,
        incorrect: str,
        description: str = None,
        options: list[str] = None,
        **kwargs,
    ):
        super().__init__(title, incorrect, description, options, **kwargs)

    async def validate_answer(self, content: str) -> bool:
        if g.is_development:
            return True
        return content in self.options
