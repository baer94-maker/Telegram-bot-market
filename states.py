from aiogram.fsm.state import State, StatesGroup


class ProductFlow(StatesGroup):
    waiting_for_product = State()
    waiting_for_clarify = State()
    generating = State()