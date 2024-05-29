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
        entries: list[Entry] | None = None,
        complete: str | None = None,
        template: Template | None = None,
    ):
        if template:
            # If the Stepper is initialized with from a Template.
            self._entries = template.entries
            self._complete = template.complete
        else:
            self._entries = entries
            self._complete = complete

        if not self._entries:
            raise ValueError("Stepper must be initialized with at least one entry")
        # Generate a unique ID for the Stepper to match aiogram handlers.
        self._id = str(uuid.uuid4())

        self._content = content

        # While state is a FSMContext object, state_code is a string representation of the current state
        # which is used to match the current step of the Stepper and access the data
        # the actual state objects from the form.
        self._state = state
        self._state_code: str | None = None
        self._step = 0

        logger.debug(f"Stepper initialized with {len(self.entries)} entries...")

        self._form = get_form(self.steps)

        self.main_menu = MainMenu._button
        self.cancel = Cancel._button

        # Results are stored in a dictionary and are only available after the Stepper is closed.
        # Event is used to notify the results are ready.
        self._results: dict[str, str] | None = None
        self.results_ready = asyncio.Event()

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
        self.match_step()

    @property
    def entries(self) -> list[Entry]:
        return self._entries  # type: ignore[return-value]

    @property
    def entry(self) -> Entry:
        return self.entries[self.step]

    @property
    def previous_entry(self) -> Entry:
        return self.entries[self.step - 1]

    @property
    def steps(self) -> list[str]:
        return [f"{self.id}{entry.title}" for entry in self.entries]

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
    def state_code(self) -> str | None:
        return self._state_code

    @state_code.setter
    def state_code(self, value: str | None) -> None:
        self._state_code = value

    @property
    def results(self) -> dict[str, str] | None:
        return self._results

    @results.setter
    def results(self, value: dict[str, str] | None) -> None:
        self._results = value

    async def start(self) -> None:
        logger.debug(f"Starting stepper with {len(self.entries)} entries...")
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
        if not answer:
            return False

        correct = await self.previous_entry.validate_answer(answer)
        if not correct:
            await content.answer(self.previous_entry.incorrect)
            return False
        return True

    async def update(self, content: Message | CallbackQuery, state: FSMContext) -> None:
        self.state_code = await self.state.get_state()
        logger.debug(f"Current state updated to {self.state_code}...")
        self.state = state
        self.content = content

        await self.state.update_data(**self.data)  # type: ignore

    async def close(self) -> None:
        logger.debug("Closing stepper...")
        raw_data = await self.state.get_data()
        data = {key.replace(f"{self.id}", ""): value for key, value in raw_data.items()}
        self.results = data
        self.results_ready.set()
        logger.debug(f"Saved results: {self._results}...")
        await self.content.answer(
            self._complete, reply_markup=Helper.reply_keyboard([self.main_menu])  # type: ignore[arg-type]
        )
        await self.state.clear()

    async def get_results(self) -> dict[str, str] | None:
        await self.results_ready.wait()
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
    def keyword(self) -> str | None:
        state_code = self.state_code
        if state_code:
            return state_code.split(":")[1]
        return None

    @property
    def details(self) -> str | None:
        if isinstance(self.content, Message):
            return self.content.text
        elif isinstance(self.content, CallbackQuery):
            return self.content.data

    @property
    def data(self) -> dict[str | None, str | None]:
        return {self.keyword: self.details}

    def match_step(self) -> None:
        for idx, title in enumerate(self.steps):
            if self.state_code == getattr(self._form, title):
                logger.debug(f"Current step detected: {idx + 1}...")
                self.step = idx + 1

    async def register(self):
        logger.debug(f"Registering stepper with {len(self.entries)} entries...")

        @form(self.steps)
        @handle_errors
        async def steps(content: Message | CallbackQuery, state: FSMContext) -> None:
            if not await self.validate(content):
                return

            await self.update(content, state)

            if self.ended:
                await self.close()
                return

            await self.forward()
