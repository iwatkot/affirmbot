from __future__ import annotations

import json
import os
import uuid
from functools import wraps

from aiogram.types import CallbackQuery, Message

from src.globals import STORAGE_JSON
from src.logger import Logger
from src.settings import Settings
from src.utils import Singleton

logger = Logger(__name__)


class Storage(metaclass=Singleton):
    def __init__(self, posts: list[Post] = None):
        self._posts = posts or []

    @property
    def posts(self) -> list[Post]:
        return self._posts.copy()

    def to_json(self) -> dict[str, list[dict[str, str | list[str] | int]]]:
        return {"posts": [post.to_json() for post in self._posts]}

    @classmethod
    def from_json(cls, data: dict[str, list[dict[str, str | list[str] | int]]]) -> Storage:
        posts = [Post.from_json(post) for post in data["posts"]]
        return cls(posts)

    def dump(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            with open(STORAGE_JSON, "w") as f:
                json.dump(self.to_json(), f, indent=4)
            logger.info(f"Storage saved to {STORAGE_JSON}")
            return result

        return wrapper

    @dump
    def add_post(self, post: Post) -> None:
        self._posts.append(post)

    def get_post(self, post_id: str) -> Post:
        for post in self._posts:
            if post.id == post_id:
                return post

    @dump
    def remove_post(self, post: Post) -> None:
        try:
            self._posts.remove(post)
        except ValueError:
            logger.warning(f"Post {post.id} not found in storage.")


class Post:
    def __init__(self, title: str, data: dict[str, str | list[str]], id: str = None):
        self._title = title
        self._data = data
        self._id = id or str(uuid.uuid4())

        self._accepted_by = []
        self._rejected_by = []

    def __repr__(self) -> str:
        return f"Post(title={self.title}, id={self.id})"

    @classmethod
    def from_content(
        cls, title: str, data: dict[str, str | list[str]], content: Message | CallbackQuery
    ) -> Post:
        post = cls(title, data)
        post._user_id = content.from_user.id
        post._username = content.from_user.username
        post._full_name = content.from_user.full_name
        return post

    @property
    def title(self) -> str:
        return self._title

    @property
    def data(self) -> dict[str, str | list[str]]:
        return self._data

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, id: str) -> None:
        self._id = id

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def full_name(self) -> str:
        return self._full_name

    async def approve_by(self, admin: int) -> None:
        from src.bot import bot

        if admin not in self.accepted_by:
            logger.info(f"Post {self.id} approved by {admin}.")
            self._accepted_by.append(admin)
            logger.info(f"Post {self.id} has {len(self.accepted_by)} approvals.")
            if self.is_approved:
                logger.info(f"Post {self.id} has enough approvals and will be posted.")
                await bot.send_message(self.user_id, "Your post has been approved.")
                await bot.send_message(Settings().channel, self.message)

                Storage().remove_post(self)

    async def reject_by(self, admin: int) -> None:
        from src.bot import bot

        if admin not in self.rejected_by:
            logger.info(f"Post {self.id} rejected by {admin}.")
            self._rejected_by.append(admin)
            logger.info(f"Post {self.id} has {len(self.rejected_by)} rejections.")
            if self.is_rejected:
                logger.info(f"Post {self.id} has enough rejections and will be removed.")
                await bot.send_message(self.user_id, "Your post has been rejected.")

                Storage().remove_post(self)

    @property
    def accepted_by(self) -> list[int]:
        return self._accepted_by.copy()

    @property
    def rejected_by(self) -> list[int]:
        return self._rejected_by.copy()

    @property
    def is_approved(self) -> bool:
        return len(self._accepted_by) >= Settings().min_approval

    @property
    def is_rejected(self) -> bool:
        return len(self._rejected_by) >= Settings().min_rejection

    def to_json(self) -> dict[str, str | list[str] | int]:
        return {
            "title": self._title,
            "data": self._data,
            "id": self._id,
            "user_id": self._user_id,
            "username": self._username,
            "full_name": self._full_name,
            "accepted_by": self._accepted_by,
            "rejected_by": self._rejected_by,
        }

    @classmethod
    def from_json(cls, data: dict[str, str | list[str] | int]) -> Post:
        post = cls(data["title"], data["data"], id=data["id"])
        post._user_id = data["user_id"]
        post._username = data["username"]
        post._full_name = data["full_name"]
        post._accepted_by = data["accepted_by"]
        post._rejected_by = data["rejected_by"]
        return post

    @property
    def text(self) -> str:
        text = ""
        for key, value in self.data.items():
            if isinstance(value, list):
                text += f"{key}:\n"
                for item in value:
                    text += f"  - {item}\n"
            else:
                text += f"{key}: {value}\n"
        return text

    @property
    def message(self) -> str:
        text = f"{self.title}\n\n{self.text}"
        if self.username:
            text += f"\n\nAuthor: @{self.username}"
        else:
            text += f"\n\nAuthor: {self.full_name}"
        return text


try:
    if os.path.isfile(STORAGE_JSON):
        logger.info(f"Found storage file at {STORAGE_JSON}, loading storage.")
        storage_json = json.load(open(STORAGE_JSON))
        Storage.from_json(storage_json)
        logger.info(f"Successfully loaded storage from {STORAGE_JSON}")
    else:
        logger.info(f"No storage file found at {STORAGE_JSON}, it will be created.")
except Exception as e:
    logger.error(f"Failed to load storage: {e}, it will be created.")
finally:
    Storage()
    logger.info(f"Storage created with {len(Storage().posts)} posts.")
