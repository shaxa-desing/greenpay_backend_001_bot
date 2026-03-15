from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌳 Daraxt ekish"), KeyboardButton(text="👤 Shaxsiy kabinet")],
            [KeyboardButton(text="💳 Karta ma'lumotlari"), KeyboardButton(text="📖 Qo'llanma")]
        ], resize_keyboard=True
    )

def contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def tree_category_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🍎 Mevali"), KeyboardButton(text="🌲 Manzarali")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def fruit_trees_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Olma"), KeyboardButton(text="Gilos"), KeyboardButton(text="Tut")],
            [KeyboardButton(text="Nok"), KeyboardButton(text="O'rik"), KeyboardButton(text="Olxori")]
        ], resize_keyboard=True, one_time_keyboard=True
    )
