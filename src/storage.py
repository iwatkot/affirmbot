from __future__ import annotations

import json
import os
import uuid
from functools import wraps

from aiogram.types import CallbackQuery, Message

from src.globals import STORAGE_JSON
from src.logger import Logger
from src.settings import Settings
from src.utils import Singleton, StorageFields

logger = Logger(__name__)


class Storage(metaclass=Singleton):
    """Singleton class to manage posts storage.
    On each change, saves storage to the JSON file and loads it on bot start.
    Removes post from storage after it's approved or rejected.

    Args:
        posts (list[Post]): List of posts.
    """

    def __init__(self, posts: list[Post] = None):
        self._posts = posts or []

    @property
    def posts(self) -> list[Post]:
        """List of posts in storage.

        Returns:
            list[Post]: List of posts.
        """
        return self._posts.copy()

    def to_json(self) -> dict[str, list[dict[str, str | list[str] | int]]]:
        """Convert storage to JSON including all posts.

        Returns:
            dict[str, list[dict[str, str | list[str] | int]]]: JSON representation of storage.
        """
        return {StorageFields.POSTS: [post.to_json() for post in self._posts]}

    @classmethod
    def from_json(cls, data: dict[str, list[dict[str, str | list[str] | int]]]) -> Storage:
        """Create storage from JSON data.

        Args:
            data (dict[str, list[dict[str, str | list[str] | int]]): JSON data.

        Returns:
            Storage: Storage object.
        """
        posts = [Post.from_json(post) for post in data[StorageFields.POSTS]]
        return cls(posts)

    def dump(func: callable) -> callable:
        """Decorator to save storage to JSON after the function call.

        Args:
            func (callable): Function to decorate.

        Returns:
            callable: Decorated function.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs) -> None:
            """Call decorated function and save storage to JSON file.

            Args:
                self (Storage): Storage object.
            """
            result = func(self, *args, **kwargs)
            with open(STORAGE_JSON, "w") as f:
                json.dump(self.to_json(), f, indent=4)
            logger.info(f"Storage saved to {STORAGE_JSON}")
            return result

        return wrapper

    @dump
    def add_post(self, post: Post) -> None:
        """Add post to the storage.

        Args:
            post (Post): Post to add.
        """
        self._posts.append(post)

    def get_post(self, post_id: str) -> Post | None:
        """Get post by ID.

        Args:
            post_id (str): Post ID.

        Returns:
            Post | None: Post object or None if not found.
        """
        for post in self._posts:
            if post.id == post_id:
                return post

    @dump
    def remove_post(self, post: Post) -> None:
        """Remove post from the storage.

        Args:
            post (Post): Post to remove.
        """
        try:
            self._posts.remove(post)
        except ValueError:
            logger.warning(f"Post {post.id} not found in storage.")


class Post:
    """Class to represent a post with title, data, and author information.

    Args:
        title (str): Post title.
        data (dict[str, str | list[str]]): Post data.
        id (str): Post ID.
    """

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
        """Create post object from message or callback content.

        Args:
            title (str): Post title.
            data (dict[str, str | list[str]]): Post data.
            content (Message | CallbackQuery): Message or callback content.

        Returns:
            Post: Post object.
        """
        post = cls(title, data)
        post._user_id = content.from_user.id
        post._username = content.from_user.username
        post._full_name = content.from_user.full_name
        return post

    @property
    def title(self) -> str:
        """Post title.

        Returns:
            str: Post title.
        """
        return self._title

    @property
    def data(self) -> dict[str, str | list[str]]:
        """Post data.

        Returns:
            dict[str, str | list[str]]: Post data.
        """
        return self._data

    @property
    def id(self) -> str:
        """Post ID.

        Returns:
            str: Post ID.
        """
        return self._id

    @id.setter
    def id(self, id: str) -> None:
        """Set post ID.

        Args:
            id (str): Post ID.
        """
        self._id = id

    @property
    def user_id(self) -> int:
        """Author user ID.

        Returns:
            int: Author user ID.
        """
        return self._user_id

    @property
    def username(self) -> str | None:
        """Author username.

        Returns:
            str | None: Author username.
        """
        return self._username

    @property
    def full_name(self) -> str:
        """Author full name.

        Returns:
            str: Author full name.
        """
        return self._full_name

    async def approve_by(self, admin: int) -> None:
        """Approve post by admin.
        If enough approvals, send post to the channel, notify author, and remove post from storage.

        Args:
            admin (int): Admin user ID.
        """
        from src.bot import bot

        if admin not in self.accepted_by:
            logger.info(f"Post {self.id} approved by {admin}.")
            self._accepted_by.append(admin)
            logger.info(f"Post {self.id} has {len(self.accepted_by)} approvals.")
            if self.is_approved:
                logger.info(f"Post {self.id} has enough approvals and will be posted.")
                await bot.send_message(self.user_id, "Your post has been approved.")
                try:
                    await bot.send_message(Settings().channel, self.message)
                except Exception as e:
                    if not Settings().channel:
                        logger.error("Channel ID is not in settings.")
                    else:
                        logger.error(f"Failed to send message to the channel: {e}")

                Storage().remove_post(self)

    async def reject_by(self, admin: int) -> None:
        """Reject post by admin.
        If enough rejections, send message to the author and remove post from storage.

        Args:
            admin (int): Admin user ID.
        """
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
        """List of admin user IDs who approved the post.

        Returns:
            list[int]: List of admin user IDs.
        """
        return self._accepted_by.copy()

    @property
    def rejected_by(self) -> list[int]:
        """List of admin user IDs who rejected the post.

        Returns:
            list[int]: List of admin user IDs.
        """
        return self._rejected_by.copy()

    @property
    def is_approved(self) -> bool:
        """Check if post has enough approvals.

        Returns:
            bool: True if post has enough approvals, False otherwise.
        """
        return len(self._accepted_by) >= Settings().min_approval

    @property
    def is_rejected(self) -> bool:
        """Check if post has enough rejections.

        Returns:
            bool: True if post has enough rejections, False otherwise.
        """
        return len(self._rejected_by) >= Settings().min_rejection

    def to_json(self) -> dict[str, str | list[str] | int]:
        """Convert post to JSON.

        Returns:
            dict[str, str | list[str] | int]: JSON representation of post.
        """
        return {
            StorageFields.TITLE: self._title,
            StorageFields.DATA: self._data,
            StorageFields.ID: self._id,
            StorageFields.USER_ID: self._user_id,
            StorageFields.USERNAME: self._username,
            StorageFields.FULL_NAME: self._full_name,
            StorageFields.ACCEPTED_BY: self._accepted_by,
            StorageFields.REJECTED_BY: self._rejected_by,
        }

    @classmethod
    def from_json(cls, data: dict[str, str | list[str] | int]) -> Post:
        """Create post from JSON data.

        Args:
            data (dict[str, str | list[str] | int]): JSON data.

        Returns:
            Post: Post object.
        """
        post = cls(
            data[StorageFields.TITLE],
            data[StorageFields.DATA],
            id=data[StorageFields.ID],
        )
        post._user_id = data[StorageFields.USER_ID]
        post._username = data[StorageFields.USERNAME]
        post._full_name = data[StorageFields.FULL_NAME]
        post._accepted_by = data[StorageFields.ACCEPTED_BY]
        post._rejected_by = data[StorageFields.REJECTED_BY]
        return post

    @property
    def text(self) -> str:
        """Post text representation.

        Returns:
            str: Post text.
        """
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
        """Post message for the channel.

        Returns:
            str: Post message.
        """
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
