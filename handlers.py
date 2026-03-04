from aiogram import types
from aiogram.dispatcher import FSMContext


import requests
import os
from config import ADMIN_ID
from keyboards import *
from states import TreeForm, PaymentForm



user_payment = {}

async def start(message: types.Message):

    await message.answer(
        "Assalomu alaykum 🌳",
        reply_markup=start_keyboard()
    )


async def start_tree(message: types.Message):

    await message.answer("Daraxt turini kiriting")

    await TreeForm.tree_type.set()


async def tree_type(message: types.Message, state: FSMContext):

    await state.update_data(tree_type=message.text)

    await message.answer(
        "📍 Lokatsiyani yuboring",
        reply_markup=location_keyboard()
    )

    await TreeForm.location.set()


async def location(message: types.Message, state: FSMContext):

    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude
    )

    await message.answer(
        "📱 Telefon raqamingizni yuboring",
        reply_markup=phone_keyboard()
    )

    await TreeForm.phone.set()


async def phone(message: types.Message, state: FSMContext):

    await state.update_data(phone=message.contact.phone_number)

    await message.answer(
        "📷 Endi daraxt rasmini yuboring (oddiy rasm yuboring)",
        reply_markup=photo_keyboard()
    )

    await TreeForm.photo.set()


async def receive_photo(message: types.Message, state: FSMContext):

    data = await state.get_data()

    lat = data["latitude"]
    lon = data["longitude"]
    phone = data["phone"]
    tree = data["tree_type"]

    photo = message.photo[-1]

    api_url = "https://greenpaybackend-production.up.railway.app/trees/"

    payload = {
        "user_id": message.from_user.id,
        "user_name": message.from_user.full_name,
        "phone": phone,
        "tree_type": tree,
        "latitude": lat,
        "longitude": lon,
        "photo": photo.file_id
    }

    try:
        r = requests.post(api_url, json=payload)
        print("Backend javobi:", r.text)
    except Exception as e:
        print("Backend xato:", e)

    map_link = f"https://maps.google.com/?q={lat},{lon}"

    text = f"""
🌳 Yangi daraxt

User: {message.from_user.full_name}
Telefon: {phone}
Daraxt: {tree}

📍 {map_link}
"""

    await message.bot.send_photo(
        ADMIN_ID,
        photo.file_id,
        caption=text,
        reply_markup=admin_keyboard(message.from_user.id)
    )

    await message.answer("✅ Rasm yuborildi. Admin tekshiradi.")

    await state.finish()

   
async def admin_buttons(call: types.CallbackQuery):

    user_id = int(call.data.split("_")[1])

    if "reject" in call.data:

        await call.bot.send_message(
            user_id,
            "❌ Siz yuborgan daraxt qabul qilinmadi"
        )

    if "accept" in call.data:

        user_payment[user_id] = "choose"

        await call.bot.send_message(
            user_id,
            "✅ Daraxtingiz qabul qilindi\n\nTo‘lov usulini tanlang",
            reply_markup=payment_keyboard()
        )

    await call.answer()



async def payment_method(message: types.Message):

    user_id = message.from_user.id

    if user_payment.get(user_id) != "choose":
        return

    if message.text == "💳 Karta":

        user_payment[user_id] = "card"

        await message.answer("💳 Karta raqamingizni kiriting")

    elif message.text == "📱 Telefon raqam":

        user_payment[user_id] = "phone"

        await message.answer("📱 Telefon raqamingizni kiriting")



async def payment_card(message: types.Message):

    user_id = message.from_user.id

    if user_payment.get(user_id) == "card":

        await message.bot.send_message(
            ADMIN_ID,
            f"""
💳 Karta ma'lumot

User: {message.from_user.full_name}
ID: {user_id}

Karta:
{message.text}
"""
        )

        await message.answer("✅ Ma'lumot qabul qilindi")

        user_payment.pop(user_id)



async def payment_phone(message: types.Message):

    user_id = message.from_user.id

    if user_payment.get(user_id) != "phone":
        return

    await message.bot.send_message(
        ADMIN_ID,
        f"""
📱 Telefon orqali to'lov

User: {message.from_user.full_name}
ID: {user_id}

Telefon:
{message.text}
"""
    )

    await message.answer("✅ Rahmat, ma'lumot yuborildi")

    user_payment.pop(user_id)