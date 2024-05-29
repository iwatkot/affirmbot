from typing import Type

from aiogram.fsm.state import State, StatesGroup


class FormMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict, steps: list[str] | None = None):
        if steps is None:
            steps = []
        for attr in steps:
            attrs[attr] = State()
        return super().__new__(cls, name, bases, attrs)


class CombinedMeta(FormMeta, type(StatesGroup)):  # type: ignore[misc]
    pass


def get_form(steps: list[str]) -> Type[StatesGroup]:

    class Form(StatesGroup, metaclass=CombinedMeta, steps=steps):  # type: ignore[call-arg, misc]
        pass

    return Form
