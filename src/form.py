from __future__ import annotations

from src.logger import Logger
from src.utils import Modes

logger = Logger(__name__)


class Form:
    def __init__(
        self,
        title: str,
        description: str = None,
        entries: list[Entry] | list[dict[str, str | list[str]]] = None,
    ):
        self._title = title
        self._description = description
        self._entries = [Entry.from_json(entry) for entry in entries] if entries else []

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

    @property
    def entries(self) -> list[Entry]:
        return self._entries

    def __repr__(self) -> str:
        return f"Form title='{self.title}' | description='{self.description}' | entries='{self.entries}'"


class Entry:
    def __init__(self, title: str, description: str = None, options: list[str] = None, **kwargs):
        self.title = title
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


class TextEntry(Entry):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title, description, **kwargs)


class DateEntry(Entry):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title, description, **kwargs)


class OneOfEntry(Entry):
    def __init__(self, title: str, description: str = None, options: list[str] = None, **kwargs):
        super().__init__(title, description, options, **kwargs)
