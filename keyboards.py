from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import KeyboardButton, InlineKeyboardButton

def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🌳 Daraxt yuborish"))
    builder.row(KeyboardButton(text="👤 Shaxsiy kabinet"), KeyboardButton(text="📖 Qo'llanma"))
    return builder.as_markup(resize_keyboard=True)

def location_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📍 Lokatsiya yuborish", request_location=True))
    return builder.as_markup(resize_keyboard=True)

def admin_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_{user_id}"))
    return builder.as_markup()

def payment_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="💳 Karta"), KeyboardButton(text="📱 Telefon raqam"))
    return builder.as_markup(resize_keyboard=True)
