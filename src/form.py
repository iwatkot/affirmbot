from aiogram.fsm.state import State, StatesGroup


class FormMeta(type):
    def __new__(cls, name: str, bases: tuple, attrs: dict, steps: list[str] = None):
        if steps is None:
            steps = []
        for attr in steps:
            attrs[attr] = State()
        return super().__new__(cls, name, bases, attrs)


class CombinedMeta(FormMeta, type(StatesGroup)):
    pass


def get_form(steps: list[str]) -> CombinedMeta:

    class Form(StatesGroup, metaclass=CombinedMeta, steps=steps):
        pass

    return Form
