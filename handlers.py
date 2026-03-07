import os
import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import UserRegister, TreePlanting
from keyboards import main_menu, contact_keyboard

router = Router()
BACKEND_URL = os.getenv("BACKEND_URL", "https://greenpaybackend-production.up.railway.app/").rstrip('/')

# --- START & RO'YXATDAN O'TISH ---
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
            if resp.status == 200:
                await message.answer("Siz ro'yxatdan o'tgansiz!", reply_markup=main_menu())
            else:
                await message.answer("Ism-familiyangizni kiriting:")
                await state.set_state(UserRegister.name)

@router.message(UserRegister.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=contact_keyboard())
    await state.set_state(UserRegister.phone)

@router.message(UserRegister.phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payload = {
        "user_id": message.from_user.id,
        "user_name": data['name'],
        "phone": message.contact.phone_number
    }
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BACKEND_URL}/users/", json=payload)
    await message.answer("✅ Ro'yxatdan o'tdingiz!", reply_markup=main_menu())
    await state.clear()

# --- SHAXSIY KABINET ---
@router.message(F.text == "👤 Shaxsiy kabinet")
async def profile(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
            if resp.status == 200:
                user = await resp.json()
                await message.answer(f"👤 Ism: {user['full_name']}\n📱 Tel: {user['phone']}")
            else:
                await message.answer("❌ Profil topilmadi. /start ni bosing.")

# --- DARAXT EKISH VA ADMIN TASDIQLASH ---
@router.message(F.text == "🌳 Daraxt ekish")
async def start_tree(message: types.Message, state: FSMContext):
    await message.answer("Daraxtga nom bering:")
    await state.set_state(TreePlanting.name)

@router.message(TreePlanting.name)
async def get_tree_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Rasm yuboring:")
    await state.set_state(TreePlanting.photo)

@router.message(TreePlanting.photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    kb = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="📍 Joylashuv", request_location=True)]], resize_keyboard=True)
    await message.answer("Lokatsiyani yuboring:", reply_markup=kb)
    await state.set_state(TreePlanting.location)

@router.message(TreePlanting.location, F.location)
async def save_tree(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payload = {
        "user_id": message.from_user.id,
        "user_name": "Foydalanuvchi", # Bu qismni yanada yaxshilash mumkin
        "tree_type": data['name'],
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
        "photo": data['photo']
    }
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BACKEND_URL}/trees/", json=payload)
    await message.answer("✅ Daraxt yuborildi. Admin tasdiqlashini kuting!")
    await state.clear()
