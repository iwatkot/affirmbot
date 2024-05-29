import asyncio
import uuid

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.types import CallbackQuery, Message

from src.decorators import form, handle_errors
from src.event import Cancel, MainMenu
from src.logger import Logger
from src.template import Entry, Template
from src.utils import Helper, get_form

logger = Logger(__name__)


class Stepper:

    def __init__(
        self,
        content: Message | CallbackQuery,
        state: FSMContext,
        entries: list[Entry] = None,
        complete: str = None,
        template: Template = None,
    ):
        self._id = str(uuid.uuid4())
        self._content = content
        self._state = state
        if template:
            self._entries = template.entries
            self._complete = template.complete
        else:
            self._entries = entries
            self._complete = complete

        logger.debug(f"Stepper initialized with {len(self.entries)} entries...")

        self._form = get_form(self.entries_titles)

        self._step = 0
        self._current_state = None

        self.main_menu = MainMenu._button
        self.cancel = Cancel._button

        self._results = None
        self._results_ready = asyncio.Event()

    @property
    def id(self) -> str:
        return self._id

    @property
    def content(self) -> Message | CallbackQuery:
        return self._content

    @content.setter
    def content(self, value: Message | CallbackQuery) -> None:
        self._content = value

    @property
    def state(self) -> FSMContext:
        return self._state

    @state.setter
    def state(self, value: FSMContext) -> None:
        self._state = value
        self._step = self._detect_step()

    @property
    def entries(self) -> list[Entry]:
        return self._entries

    @property
    def entry(self) -> Entry:
        return self._entries[self.step]

    @property
    def previous_entry(self) -> Entry:
        return self._entries[self.step - 1]

    # @property
    # def entries_titles(self) -> list[str]:
    #     return [entry.title for entry in self._entries]

    @property
    def entries_titles(self) -> list[str]:
        return [f"{self.id}{entry.title}" for entry in self._entries]

    @property
    def form(self) -> StatesGroup:
        return self._form

    @property
    def step(self) -> int:
        return self._step

    @step.setter
    def step(self, value: int) -> None:
        self._step = value

    @property
    def current_state(self) -> str:
        return self._current_state

    @current_state.setter
    def current_state(self, value: str) -> None:
        self._current_state = value

    async def start(self) -> None:
        logger.debug("Starting stepper...")
        if self._step == 0:
            await self.forward()
            return await self.register()
        else:
            raise ValueError("Stepper is already started, use forward() method to move forward")

    async def forward(self) -> None:
        logger.debug(f"Current step: {self.step}, moving forward...")
        await self._send_answer()
        await self._update_state()
        self.step += 1
        logger.debug(f"Moved forward to step {self.step}...")

    async def validate(self, content: Message | CallbackQuery) -> bool:
        logger.debug(f"Validating answer for step {self.step} of {len(self.entries)}...")
        answer = content.text if isinstance(content, Message) else content.data

        correct = await self.previous_entry.validate_answer(answer)
        if not correct:
            await content.answer(self.previous_entry.incorrect)
            return False
        return True

    async def update(self, content: Message | CallbackQuery, state: FSMContext) -> None:
        self._current_state = await self._state.get_state()
        logger.debug(f"Current state updated to {self._current_state}...")
        self.state = state
        self.content = content

        await self._state.update_data(**self.data)

    async def close(self) -> None:
        logger.debug("Closing stepper...")
        raw_data = await self._state.get_data()
        data = {key.replace(f"{self.id}", ""): value for key, value in raw_data.items()}
        self._results = data
        self._results_ready.set()
        logger.debug(f"Saved results: {self._results}...")
        await self.content.answer(
            self._complete, reply_markup=Helper.reply_keyboard([self.main_menu])
        )
        await self._state.clear()

    async def results(self) -> dict[str, str]:
        await self._results_ready.wait()
        return self._results

    async def _update_state(self) -> None:
        await self._state.set_state(getattr(self.form, f"{self.id}{self.entry.title}"))

    async def _send_answer(self) -> None:
        entry = self.entry
        buttons = entry.options if entry.options else []
        buttons.append(self.cancel)
        text = self._prepare_text()
        await Helper.force_answer(self.content, text, buttons)

    @property
    def ended(self) -> bool:
        ended = self.step == len(self.entries)
        if ended:
            logger.debug(f"Stepper is ending, step {self.step} of {len(self.entries)}")
        else:
            logger.debug(f"Stepper is not ending, step {self.step} of {len(self.entries)}")
        return ended

    def _prepare_text(self) -> str:
        entry = self.entry
        text = f"<b>{entry.title}</b>\n\n"
        if entry.description:
            text += f"{entry.description}\n"
        return text

    @property
    def keyword(self) -> str:
        return self._current_state.split(":")[1]

    @property
    def data(self) -> dict[str, str]:
        return {self.keyword: self.content.text}

    def _detect_step(self) -> int:
        for idx, title in enumerate(self.entries_titles):
            if self._current_state == getattr(self._form, title):
                logger.debug(f"Current step detected: {idx + 1}...")
                return idx + 1

    async def register(self):
        @form(self.entries_titles)
        @handle_errors
        async def steps(content: Message | CallbackQuery, state: FSMContext) -> None:
            if not await self.validate(content):
                return

            await self.update(content, state)

            if self.ended:
                await self.close()
                return

            await self.forward()
