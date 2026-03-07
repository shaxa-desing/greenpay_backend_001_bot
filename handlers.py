import os
import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from states import UserRegister, TreePlanting
from keyboards import main_menu, contact_keyboard

router = Router()

# Backend URL manzilini to'g'ri oling
BACKEND_URL = os.getenv("BACKEND_URL", "https://greenpaybackend-production.up.railway.app/").rstrip('/')

# --- RO'YXATDAN O'TISH ---
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
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
    payload = {
        "user_id": message.from_user.id,
        "user_name": data.get("full_name"),
        "username": message.from_user.username,
        "phone": message.contact.phone_number
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/users/", json=payload) as resp:
            if resp.status in [200, 201]:
                await message.answer("✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=main_menu())
                await state.clear()
            else:
                await message.answer("❌ Server xatosi.")

# --- DARAXT EKISH JARAYONI ---
@router.message(F.text == "🌳 Daraxt ekish")
async def ask_tree_name(message: types.Message, state: FSMContext):
    await message.answer("Daraxtga nom bering (masalan: 'Vatan bog'i'):")
    await state.set_state(TreePlanting.name)

@router.message(TreePlanting.name)
async def ask_tree_photo(message: types.Message, state: FSMContext):
    await state.update_data(tree_name=message.text)
    await message.answer("Daraxtingizning rasmini yuboring:")
    await state.set_state(TreePlanting.photo)

@router.message(TreePlanting.photo, F.photo)
async def ask_tree_location(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    kb = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]], resize_keyboard=True)
    await message.answer("Endi lokatsiyani yuboring:", reply_markup=kb)
    await state.set_state(TreePlanting.location)

@router.message(TreePlanting.location, F.location)
async def save_tree(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    
    async with aiohttp.ClientSession() as session:
        # Foydalanuvchini bazadan topamiz
        async with session.get(f"{BACKEND_URL}/user/{user_id}") as resp:
            if resp.status == 200:
                user_info = await resp.json()
                # Daraxtni saqlaymiz
                payload = {
                    "user_id": user_id,
                    "user_name": user_info.get("full_name"),
                    "phone": user_info.get("phone"),
                    "tree_type": data.get("tree_name"), # Daraxt nomi
                    "latitude": message.location.latitude,
                    "longitude": message.location.longitude,
                    "photo": data.get("photo")
                }
                async with session.post(f"{BACKEND_URL}/trees/", json=payload) as tree_resp:
                    if tree_resp.status in [200, 201]:
                        await message.answer("✅ Daraxtingiz saqlandi!", reply_markup=main_menu())
                        await state.clear()
                    else:
                        await message.answer("❌ Saqlashda xatolik.")
            

# handlers.py ga qo'shing:
ADMIN_ID = "5833828220" # O'zingizning IDingizni yozing

@router.callback_query(F.data.startswith("approve_"))
async def approve_tree(callback: types.CallbackQuery):
    tree_id = callback.data.split("_")[1]
    # Backendga statusni 'approved' deb yuborish kerak
    await callback.message.edit_caption(caption="✅ Daraxt tasdiqlandi va xaritaga qo'shildi!")
    await callback.answer("Daraxt tasdiqlandi")



# Callback uchun handler
@router.callback_query(F.data.startswith("approve_"))
async def approve_tree(callback: types.CallbackQuery):
    # Bu yerda backendga statusni 'approved' deb yuboramiz
    await callback.message.edit_caption(caption="✅ Daraxt tasdiqlandi!")

@router.message(Command("help"))
async def help_cmd(message: types.Message):
    text = """
    📘 **Qo'llanma:**
    1. **/start** - Ro'yxatdan o'tish.
    2. **🌳 Daraxt ekish** - Daraxt nomi, rasm va lokatsiyani yuboring.
    3. **👤 Shaxsiy kabinet** - Ma'lumotlaringizni ko'rish.
    
    *Daraxtingiz admin tomonidan tasdiqlangach, xaritada ko'rinadi!*
    """
    await message.answer(text, parse_mode="Markdown")







