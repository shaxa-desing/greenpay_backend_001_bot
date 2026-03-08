from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌳 Daraxt ekish")],
            [KeyboardButton(text="👤 Shaxsiy kabinet")]
        ],
        resize_keyboard=True
    )


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌳 Daraxt ekish")],
            [KeyboardButton(text="👤 Shaxsiy kabinet"), KeyboardButton(text="💳 Karta ma'lumotlari")]
        ],
        resize_keyboard=True
    )

def contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

