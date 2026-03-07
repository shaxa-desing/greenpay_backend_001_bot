from aiogram.fsm.state import State, StatesGroup

class TreeForm(StatesGroup):
    tree_type = State()
    location = State()
    phone = State()
    photo = State()


class PaymentForm(StatesGroup):
    method = State()
    card = State()

    phone = State()
