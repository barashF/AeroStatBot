from aiogram.fsm.state import State, StatesGroup


class Compare(StatesGroup):
    first = State()
    second = State()
