import src.globals as g
from src.form import Form


class State:
    def __init__(self, admins: list[int], active_template: int = 1):
        self._admins = admins
        self._active_template = active_template

    def get_template(self) -> Form:
        return g.config.get_form(form_idx=self._active_template)

    @property
    def admins(self) -> list[int]:
        return self._admins

    @property
    def active_template(self) -> int:
        return self._active_template

    @active_template.setter
    def active_template(self, value: int) -> None:
        self._active_template = value
