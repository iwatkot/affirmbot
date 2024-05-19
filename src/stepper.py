from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.logger import Logger
from src.template import Template

logger = Logger(__name__)


class Stepper:
    def __init__(self, template: Template, state: FSMContext, message: Message = None):
        self._template = template
        self._titles = [entry.title for entry in self._template.entries]
        self._steps = len(self._template.entries)
        self._state = state
        self._message = message
        self._step = 0
        self._current_state = None

    @property
    def message(self) -> Message:
        return self._message

    @message.setter
    def message(self, value: Message) -> None:
        self._message = value

    @property
    def step(self) -> int:
        return self._step

    @step.setter
    def step(self, value: int) -> None:
        self._step = value

    @property
    def state(self) -> FSMContext:
        return self._state

    @state.setter
    def state(self, value: FSMContext) -> None:
        self._state = value
        self._step = self._detect_step()

    @property
    def current_state(self) -> str:
        return self._current_state

    @current_state.setter
    def current_state(self, value: str) -> None:
        self._current_state = value

    async def start(self) -> None:
        if self._step == 0:
            logger.debug(f"Starting stepper for {self._template.title} form...")
            return await self.forward()
        else:
            raise ValueError("Stepper is already started, use forward() method to move forward")

    async def forward(self) -> None:
        await self._send_answer()
        await self._update_state()
        self.step += 1
        logger.debug(f"Moving forward to step {self.step}...")

    async def update(self, state: FSMContext, message: Message) -> None:
        self._state = state
        self._current_state = await self._state.get_state()
        logger.debug(f"Current state updated to {self._current_state}...")
        self._message = message

        await self._state.update_data(**self.data)

    async def close(self) -> None:
        data = await self._state.get_data()
        await self._message.answer(f"Data: {data}")
        await self._state.clear()

    async def _update_state(self) -> None:
        await self._state.set_state(getattr(self._template.form, self._get_entry_title()))

    async def _send_answer(self) -> None:
        await self._message.answer(self._prepare_message())

    @property
    def ended(self) -> bool:
        return self.step == self._steps

    def _prepare_message(self) -> str:
        entry = self._template.get_entry(self.step)
        message = f"<b>{entry.title}</b>\n\n"
        if entry.description:
            message += f"{entry.description}\n"
        return message

    @property
    def keyword(self) -> str:
        return self._current_state.split(":")[1]

    @property
    def data(self) -> dict[str, str]:
        return {self.keyword: self._message.text}

    def _get_entry_title(self) -> str:
        return self._titles[self.step]

    def _detect_step(self) -> int:
        for idx, title in enumerate(self._titles):
            if self._state == getattr(self._template.form, title):
                return idx
