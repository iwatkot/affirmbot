from __future__ import annotations

from datetime import datetime

import src.globals as g
from src.logger import Logger
from src.utils import Modes

logger = Logger(__name__)


class Template:
    """Class to represent a template of the form.
    Contains the title, description, entries, complete message, and active status.

    Args:
        title (str): Title of the form
        description (str, optional): Description of the form. Defaults to None.
        entries (list[Entry] | list[dict[str, str | list[str]]], optional): List of entries. Defaults to None.
        complete (str, optional): Message to display when the form is completed. Defaults to None.
        active (bool, optional): Status of the form. Defaults to True.
    """

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
        """Returns the title of the form.

        Returns:
            str: Title of the form
        """
        return self._title

    @property
    def description(self) -> str:
        """Returns the description of the form.

        Returns:
            str: Description of the form
        """
        return self._description

    @property
    def entries(self) -> list[Entry] | None:
        """Returns the list of entries in the form.

        Returns:
            list[Entry]: List of entries
        """
        return self._entries.copy()

    @property
    def complete(self) -> str | None:
        """Returns the complete message of the form.

        Returns:
            str: Complete message
        """
        return self._complete

    @property
    def active(self) -> bool:
        """Returns the status of the form.

        Returns:
            bool: Status of the form
        """
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        """Sets the status of the form.

        Args:
            value (bool): Status of the form
        """
        self._active = value

    @property
    def idx(self) -> int | None:
        """Returns the index of the form.

        Returns:
            int: Index of the form
        """
        return self._idx

    @idx.setter
    def idx(self, value: int) -> None:
        """Sets the index of the form.

        Args:
            value (int): Index of the form
        """
        self._idx = value

    @property
    def disable(self) -> bool:
        """Disables the form.

        Returns:
            bool: Status of the form
        """
        self.active = False

    @property
    def enable(self) -> bool:
        """Enables the form.

        Returns:
            bool: Status of the form
        """
        self.active = True

    @property
    def is_active(self) -> bool:
        """Returns the status of the form.

        Returns:
            bool: Status of the form
        """
        return self.active

    def get_entry(self, idx: int) -> Entry:
        """Returns the entry at the given index.

        Args:
            idx (int): Index of the entry

        Returns:
            Entry: Entry at the given index
        """
        return self.entries[idx]

    def __repr__(self) -> str:
        return f"Form title='{self.title}' | description='{self.description}' | entries='{self.entries}'"


class Entry:
    """Base class to represent an entry in the form.

    Args:
        title (str): Title of the entry
        incorrect (str): Message to display when the answer is incorrect
        description (str, optional): Description of the entry. Defaults to None.
        options (list[str], optional): List of options for the entry. Defaults to None.
    """

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
        """Creates an entry from the given data. The data should contain the mode of the entry.

        Args:
            data (dict[str, str | list[str]]): Data to create the entry

        Returns:
            Entry: Entry created from the data
        """

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
        """Validates the answer to the entry. Must be implemented by the subclass.

        Args:
            content (str): Answer to the entry

        Returns:
            bool: True if the answer is valid, False otherwise
        """
        raise NotImplementedError

    def get_answer(self, results: dict[str, str]) -> str | int:
        """Returns the answer to the entry.

        Args:
            results (dict[str, str]): Results of the form

        Returns:
            str | int: Answer to the entry
        """
        return self.base_type(results[self.title])

    def replace_validator(self, validator: callable) -> None:
        """Replaces the validator of the entry with the given function.

        Args:
            validator (callable): New validator
        """
        self.validate_answer = validator


class TextEntry(Entry):
    base_type = str

    """Class to represent a text entry in the form.

    Args:
        title (str): Title of the entry
        incorrect (str): Message to display when the answer is incorrect
        description (str, optional): Description of the entry. Defaults to None.
    """

    def __init__(self, title: str, incorrect: str, description: str = None, **kwargs):
        super().__init__(title, incorrect, description, **kwargs)

    async def validate_answer(self, content: str) -> bool:
        """Checks if the answer is a string.

        Args:
            content (str): Answer to the entry

        Returns:
            bool: True if the answer is a string, False otherwise
        """
        try:
            assert isinstance(content, str)
            return True
        except AssertionError:
            return False


class NumberEntry(Entry):
    """Class to represent a number entry in the form.

    Args:
        title (str): Title of the entry
        incorrect (str): Message to display when the answer is incorrect
        description (str, optional): Description of the entry. Defaults to None.
    """

    base_type = int

    def __init__(self, title: str, incorrect: str, description: str = None, **kwargs):
        super().__init__(title, incorrect, description, **kwargs)

    async def validate_answer(self, content: str) -> bool:
        """Checks if the answer is a number.

        Args:
            content (str): Answer to the entry

        Returns:
            bool: True if the answer is a number, False otherwise
        """
        try:
            assert content.isdigit()
            return True
        except AssertionError:
            return False


class DateEntry(Entry):
    """Class to represent a date entry in the form.

    Args:
        title (str): Title of the entry
        incorrect (str): Message to display when the answer is incorrect
        description (str, optional): Description of the entry. Defaults to None.
    """

    base_type = str

    def __init__(self, title: str, incorrect: str, description: str = None, **kwargs):
        super().__init__(title, incorrect, description, **kwargs)

    async def validate_answer(self, content: str) -> bool:
        """Checks if the answer is a date.

        Args:
            content (str): Answer to the entry

        Returns:
            bool: True if the answer is a date, False otherwise
        """
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
    """Class to represent a one-of entry in the form.

    Args:
        title (str): Title of the entry
        incorrect (str): Message to display when the answer is incorrect
        description (str, optional): Description of the entry. Defaults to None.
        options (list[str], optional): List of options for the entry. Defaults to None.
    """

    base_type = str

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
        """Checks if the answer is one of the options.

        Args:
            content (str): Answer to the entry

        Returns:
            bool: True if the answer is one of the options, False otherwise
        """
        if g.is_development:
            return True
        return content in self.options
