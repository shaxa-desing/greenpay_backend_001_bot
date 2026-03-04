from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("🌳 Daraxt yuborish"))

    return kb


def location_keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("📍 Lokatsiya yuborish", request_location=True))

    return kb


def phone_keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("📱 Telefon yuborish", request_contact=True))

    return kb


def photo_keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add(KeyboardButton("📷 Rasm yuborish"))

    return kb


def admin_keyboard(user_id):

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("✔ Qabul qilish", callback_data=f"accept_{user_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}")
    )

    return kb


def payment_keyboard():

    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.add("💳 Karta", "📱 Telefon raqam")

    return kb