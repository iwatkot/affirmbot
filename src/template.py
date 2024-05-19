from __future__ import annotations

from datetime import datetime

from aiogram.fsm.state import StatesGroup

from src.logger import Logger
from src.utils import CombinedMeta, Modes

# from typing import Generator


logger = Logger(__name__)


class Template:
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

    # @property
    # def entries(self) -> Generator[Entry, None, None]:
    #     for entry in self._entries:
    #         yield entry

    @property
    def entries(self) -> list[Entry]:
        return self._entries

    def __repr__(self) -> str:
        return f"Form title='{self.title}' | description='{self.description}' | entries='{self.entries}'"

    @property
    def form(self) -> CombinedMeta:
        titles = [entry.title for entry in self.entries]

        class Form(StatesGroup, metaclass=CombinedMeta, titles=titles):
            pass

        return Form


class Entry:
    def __init__(self, title: str, description: str = None, options: list[str] = None, **kwargs):
        self.title = title
        self.description = description
        self.options = options
        self._answer = None

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

    def save_answer(self, answer: str) -> bool:
        if self._validate_answer(answer):
            self._answer = answer
            logger.debug(f"Saved answer for {self.title}: {answer}")
            return True
        else:
            logger.error(f"Failed to save answer for {self.title}: {answer}")
            return False

    def _validate_answer(self, answer: str) -> bool:
        raise NotImplementedError

    @property
    def answer(self) -> str:
        return self._answer


class TextEntry(Entry):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title, description, **kwargs)

    def _validate_answer(self, answer: str) -> bool:
        try:
            assert isinstance(answer, str)
            return True
        except AssertionError:
            return False


class DateEntry(Entry):
    def __init__(self, title: str, description: str = None, **kwargs):
        super().__init__(title, description, **kwargs)

    def _validate_answer(self, answer: str) -> bool:
        date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y"]
        for date_format in date_formats:
            try:
                datetime.strptime(answer, date_format)
                return True
            except ValueError:
                continue
        return False


class OneOfEntry(Entry):
    def __init__(self, title: str, description: str = None, options: list[str] = None, **kwargs):
        super().__init__(title, description, options, **kwargs)
