import os
import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import UserRegister, TreePlanting
from keyboards import main_menu, contact_keyboard

router = Router()

# URL dagi ortiqcha slashlarni olib tashlash
RAW_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_URL = RAW_URL.rstrip('/')

# 1. START VA RO'YXATDAN O'TISH
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Bazada bormi tekshiramiz
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{user_id}") as resp:
            if resp.status == 200:
                await message.answer("Xush kelibsiz! Bosh menyu:", reply_markup=main_menu())
            else:
                await message.answer("Yashil tabiat loyihasiga xush kelibsiz!\nIltimos, ism va familiyangizni kiriting:")
                await state.set_state(UserRegister.name)

@router.message(UserRegister.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Rahmat! Endi telefon raqamingizni yuboring:", reply_markup=contact_keyboard())
    await state.set_state(UserRegister.phone)

@router.message(UserRegister.phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username
    
    payload = {
        "user_id": user_id,
        "user_name": data.get("full_name"),
        "username": f"@{username}" if username else None,
        "phone": message.contact.phone_number
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/users/", json=payload) as resp:
            if resp.status in [200, 201]:
                await message.answer("✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=main_menu())
                await state.clear()
            else:
                await message.answer("❌ Server bilan ulanishda xato yuz berdi. Keyinroq urinib ko'ring.")

# 2. SHAXSIY KABINET
@router.message(F.text == "👤 Shaxsiy kabinet")
async def show_profile(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
            if resp.status == 200:
                user = await resp.json()
                text = (f"👤 **Sizning profilingiz:**\n\n"
                        f"🆔 ID: `{user['user_id']}`\n"
                        f"👤 Ism: {user['full_name']}\n"
                        f"📱 Telefon: {user['phone'] or 'Kiritilmagan'}")
                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("⚠️ Ma'lumot topilmadi. Iltimos, /start ni bosing.")

# 3. DARAXT EKISH
@router.message(F.text == "🌳 Daraxt ekish")
async def ask_tree_photo(message: types.Message, state: FSMContext):
    await message.answer("Daraxtingizning rasmini yuboring (Oddiy rasm qilib):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(TreePlanting.photo)

@router.message(TreePlanting.photo, F.photo)
async def ask_tree_location(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(photo=file_id)
    
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]],
        resize_keyboard=True
    )
    await message.answer("Ajoyib rasm! Endi daraxt ekilgan joyning lokatsiyasini yuboring:", reply_markup=kb)
    await state.set_state(TreePlanting.location)

@router.message(TreePlanting.location, F.location)
async def save_tree(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lat = message.location.latitude
    lon = message.location.longitude
    user_id = message.from_user.id
    
    # Avval backenddan foydalanuvchi ma'lumotlarini (ism, telefon) olamiz
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{user_id}") as resp:
            if resp.status == 200:
                user_info = await resp.json()
                
                # Daraxtni saqlaymiz
                payload = {
                    "user_id": user_id,
                    "user_name": user_info.get("full_name", "Noma'lum"),
                    "phone": user_info.get("phone", ""),
                    "tree_type": "Mevali daraxt", # Buni o'zgartirishingiz mumkin
                    "latitude": lat,
                    "longitude": lon,
                    "photo": data['photo']
                }
                
                async with session.post(f"{BACKEND_URL}/trees/", json=payload) as tree_resp:
                    if tree_resp.status in [200, 201]:
                        await message.answer("✅ Daraxtingiz bazaga saqlandi va xaritaga tushdi!", reply_markup=main_menu())
                        await state.clear()
                    else:
                        await message.answer("❌ Daraxtni saqlashda xatolik yuz berdi.")
            else:
                await message.answer("Siz ro'yxatdan o'tmagansiz. /start ni bosing.")
