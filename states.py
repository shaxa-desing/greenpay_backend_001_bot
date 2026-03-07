from aiogram.fsm.state import State, StatesGroup

class TreeForm(StatesGroup):
    tree_type = State()
    location = State()
    photo = State()

class PaymentForm(StatesGroup):
    details = State()

# MANA BU QISMNI QO'SHING:

class UserRegister(StatesGroup):
    name = State()
    phone = State() # SHU QATOR QOLIB KETGAN EDI

