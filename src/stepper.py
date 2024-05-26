from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup

from src.event import Cancel, MainMenu
from src.form import CombinedMeta, get_form
from src.logger import Logger
from src.template import Entry, Template

logger = Logger(__name__)


class Stepper:

    def __init__(
        self,
        message: Message,
        state: FSMContext,
        entries: list[Entry] = None,
        complete: str = None,
        template: Template = None,
    ):
        self._message = message
        self._state = state
        if template:
            self._entries = template.entries
            self._complete = template.complete
        else:
            self._entries = entries
            self._complete = complete

        self._form = get_form(self.entries_titles)

        self._step = 0
        self._current_state = None

        self.main_menu = MainMenu._button
        self.cancel = Cancel._button

    @property
    def message(self) -> Message:
        return self._message

    @message.setter
    def message(self, value: Message) -> None:
        self._message = value

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
        logger.debug(f"Getting entry {self.step} of {len(self._entries)}...")
        return self._entries[self.step - 1]

    @property
    def entries_titles(self) -> list[str]:
        return [entry.title for entry in self._entries]

    @property
    def form(self) -> CombinedMeta:
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
        if self._step == 0:
            return await self.forward()
        else:
            raise ValueError("Stepper is already started, use forward() method to move forward")

    async def forward(self) -> None:
        await self._send_answer()
        await self._update_state()
        self.step += 1
        logger.debug(f"Moving forward to step {self.step}...")

    async def validate(self, message: Message | CallbackQuery) -> bool:
        content = message.text if isinstance(message, Message) else message.data

        correct = self.entry.validate_answer(content)
        if not correct:
            await message.answer(self.entry.incorrect)
            return False
        return True

    async def update(self, message: Message, state: FSMContext) -> None:
        self._state = state
        self._current_state = await self._state.get_state()
        logger.debug(f"Current state updated to {self._current_state}...")
        self._message = message

        await self._state.update_data(**self.data)

    async def close(self) -> None:
        data = await self._state.get_data()  # TODO: Process data.
        logger.debug(f"Collected data: {data}.")
        await self._message.answer(
            self._complete, reply_markup=self._reply_keyboard([self.main_menu])
        )
        await self._state.clear()

    async def _update_state(self) -> None:
        await self._state.set_state(getattr(self.form, self.entry.title))

    async def _send_answer(self) -> None:
        entry = self.entry
        buttons = entry.options if entry.options else []
        buttons.append(self.cancel)
        await self._message.answer(
            self._prepare_message(), reply_markup=self._reply_keyboard(buttons)
        )

    def _reply_keyboard(self, buttons: list[str]) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text=button)] for button in buttons]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @property
    def ended(self) -> bool:
        ended = self.step == len(self.entries)
        if ended:
            logger.debug(f"Stepper is ending, step {self.step} of {len(self.entries)}")
        else:
            logger.debug(f"Stepper is not ending, step {self.step} of {len(self.entries)}")
        return ended

    def _prepare_message(self) -> str:
        entry = self.entry
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

    def _detect_step(self) -> int:
        for idx, title in enumerate(self._titles):
            if self._state == getattr(self._template.form, title):
                return idx
