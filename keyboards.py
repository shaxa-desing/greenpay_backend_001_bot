from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import KeyboardButton, InlineKeyboardButton

def contact_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🌳 Daraxt yuborish"))
    builder.row(KeyboardButton(text="👤 Shaxsiy kabinet"), KeyboardButton(text="📖 Qo'llanma"))
    return builder.as_markup(resize_keyboard=True)

def location_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📍 Lokatsiya yuborish", request_location=True))
    return builder.as_markup(resize_keyboard=True)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
            ]
        ]
    )

def payment_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="💳 Karta"), KeyboardButton(text="📱 Telefon raqam"))
    return builder.as_markup(resize_keyboard=True)


