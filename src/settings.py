# import src.globals as g
from src.config import Config
from src.template import Template
from src.utils import Singleton


class Settings(metaclass=Singleton):
    def __init__(self, admins: list[int]):
        self._admins = admins
        self._templates = Config().templates
        for idx, template in enumerate(self._templates):
            template.idx = idx
        self._channel = None

    @property
    def admins(self) -> list[int]:
        return self._admins.copy()

    def add_admin(self, user_id: int) -> None:
        if user_id not in self._admins:
            self._admins.append(user_id)

    def remove_admin(self, user_id: int) -> None:
        if user_id in self._admins:
            self._admins.remove(user_id)

    @property
    def active_templates(self) -> list[Template]:
        return [template for template in self._templates if template.is_active]

    def get_template(self, idx: int) -> Template:
        return self._templates[idx]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self._admins

    @property
    def channel(self) -> str | None:
        return self._channel
