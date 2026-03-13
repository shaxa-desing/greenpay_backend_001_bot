import os
import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import UserRegister, TreePlanting, CardUpdate
from keyboards import main_menu, contact_keyboard

router = Router()

BACKEND_URL = os.getenv("BACKEND_URL", "https://greenpaybackend-production.up.railway.app").rstrip('/')
ADMIN_ID = "5833828220" # Sizning admin ID raqamingiz

# --- START & MENU ---
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer("Assalomu alaykum! Green Pay botiga xush kelibsiz.", reply_markup=main_menu())

# --- YO'RIQNOMA VA SUPPORT ---
@router.message(F.text == "📖 Yo'riqnoma")
async def show_instruction(message: types.Message):
    text = ("🌲 **GreenPay botidan foydalanish:**\n\n"
            "1. '🌳 Daraxt ekish' tugmasini bosing.\n"
            "2. Daraxtga nom bering.\n"
            "3. Daraxt rasmini yuboring.\n"
            "4. '📍 Joylashuvni yuborish' tugmasini bosing.\n"
            "5. Admin tasdiqlashini kuting.")
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "📞 Support")
async def show_support(message: types.Message):
    # Admin bilan bog'lanish tugmasi
    support_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Admin bilan chat", url="https://t.me/SizningUsername")]
    ])
    await message.answer("Muammo bo'lsa admin bilan bog'laning:", reply_markup=support_kb)

# --- DARAXT EKISH (AI O'CHIRILDI) ---
@router.message(F.text == "🌳 Daraxt ekish")
async def start_tree(message: types.Message, state: FSMContext):
    await message.answer("Daraxtga nom bering (masalan: Archa):")
    await state.set_state(TreePlanting.name)

@router.message(TreePlanting.name)
async def get_tree_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📸 Daraxtning rasmini yuboring:")
    await state.set_state(TreePlanting.photo)

@router.message(TreePlanting.photo, F.photo)
async def get_tree_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo=photo.file_id)
    
    loc_kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]], 
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("✅ Rasm qabul qilindi. Endi joylashuvni yuboring:", reply_markup=loc_kb)
    await state.set_state(TreePlanting.location)

@router.message(TreePlanting.location, F.location)
async def save_tree(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payload = {
        "user_id": message.from_user.id,
        "tree_type": data.get("name"),
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
        "photo_id": data.get("photo")
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/trees/", json=payload) as resp:
            if resp.status in [200, 201]:
                # Adminga yuborish
                kb = InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tree_approve_{message.from_user.id}"),
                    types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"tree_reject_{message.from_user.id}")
                ]])
                await message.bot.send_photo(
                    ADMIN_ID, photo=data.get("photo"), 
                    caption=f"🌳 Yangi daraxt!\nFoydalanuvchi: {message.from_user.full_name}\nNomi: {data.get('name')}",
                    reply_markup=kb
                )
                await message.answer("✅ Ma'lumotlar adminga yuborildi!", reply_markup=main_menu())
                await state.clear()
            else:
                await message.answer("❌ Xatolik yuz berdi.")
