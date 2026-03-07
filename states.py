from aiogram.fsm.state import State, StatesGroup

class TreeForm(StatesGroup):
    registration_phone = State()
    tree_type = State()
    location = State()
    photo = State()

class PaymentForm(StatesGroup):
    method = State()
    details = State()
