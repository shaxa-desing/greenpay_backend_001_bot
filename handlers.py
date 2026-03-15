import os
import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from states import UserRegister, TreePlanting, CardUpdate
from keyboards import main_menu, contact_keyboard, tree_category_kb, fruit_trees_kb

router = Router()

# Mahalliy test qilish uchun localhost, serverga qo'yganda o'zgaradi
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip('/')
ADMIN_ID = 5833828220 

# Narxlar ro'yxati (Baza = 5000 so'm, mevalar narxi qadam-baqadam oshadi)
FRUIT_PRICES = {
    "Olma": 10000, "Gilos": 11000, "Tut": 12000,
    "Nok": 13000, "O'rik": 14000, "Olxori": 15000
}

# --- START & RO'YXATDAN O'TISH ---
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/users/check/{message.from_user.id}") as resp:
            data = await resp.json()
            if data.get("exists"):
                await message.answer("Assalomu alaykum! Qanday xizmat xohlaysiz?", reply_markup=main_menu())
            else:
                await message.answer("Assalomu alaykum, iltimos ismingiz va familiyangizni yozib qoldiring:", reply_markup=ReplyKeyboardRemove())
                await state.set_state(UserRegister.name)

@router.message(UserRegister.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Endi telefon raqamingizni (kontaktni) yuboring:", reply_markup=contact_keyboard())
    await state.set_state(UserRegister.phone)

@router.message(UserRegister.phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payload = {
        "user_id": message.from_user.id,
        "full_name": data.get("full_name"),
        "phone": message.contact.phone_number
    }
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BACKEND_URL}/users/", json=payload)
    
    await message.answer("Muvaffaqiyatli ro'yxatdan o'tdingiz! Qanday xizmat xohlaysiz?", reply_markup=main_menu())
    await state.clear()

# --- QO'LLANMA ---
@router.message(F.text == "📖 Qo'llanma")
async def show_instruction(message: types.Message):
    text = ("🌲 **Qanday ishlashi haqida:**\n\n"
            "Daraxt ekib daromad topish tizimi. Siz daraxt ekasiz, rasmini va lokatsiyasini yuborasiz. Admin tasdiqlagach, pul hisobingizga tushadi.")
    await message.answer(text, parse_mode="Markdown")
    # Agar video bo'lsa:
    # await message.answer_video(video="Sizning_video_file_id_shu_yerda")

# --- SHAXSIY KABINET ---
@router.message(F.text == "👤 Shaxsiy kabinet")
async def show_cabinet(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
            if resp.status == 200:
                user = await resp.json()
                text = (f"👤 **Ism:** {user['full_name']}\n"
                        f"📱 **Telefon:** {user['phone']}\n"
                        f"💳 **Karta raqami:** {user.get('card') or 'Biriktirilmagan'}\n"
                        f"💰 **Hisobingiz (Balans):** {user['balance']} so'm")
                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("Ma'lumot topilmadi.")

# --- KARTA MA'LUMOTLARI ---
@router.message(F.text == "💳 Karta ma'lumotlari")
async def show_card_menu(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
            user = await resp.json()
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✏️ O'zgartirish", callback_data="edit_card")]])
            text = f"Sizning karta raqamingiz: {user.get('card') or 'Yoq'}\nTelefon: {user['phone']}"
            await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "edit_card")
async def edit_card_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Yangi karta raqamingizni kiriting (masalan: 8600...):")
    await state.set_state(CardUpdate.card_number)

@router.message(CardUpdate.card_number)
async def get_card(message: types.Message, state: FSMContext):
    await state.update_data(card=message.text)
    await message.answer("Kartaga biriktirilgan telefon raqamni kiriting:")
    await state.set_state(CardUpdate.phone_number)

@router.message(CardUpdate.phone_number)
async def save_card(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payload = {"card": data.get("card"), "phone": message.text}
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BACKEND_URL}/update-card/{message.from_user.id}", json=payload)
    await message.answer("✅ Karta ma'lumotlaringiz saqlandi!", reply_markup=main_menu())
    await state.clear()

# --- DARAXT EKISH LOGIKASI ---
@router.message(F.text == "🌳 Daraxt ekish")
async def start_tree(message: types.Message, state: FSMContext):
    await message.answer("Qanday daraxt ekmoqchisiz?", reply_markup=tree_category_kb())
    await state.set_state(TreePlanting.category)

@router.message(TreePlanting.category)
async def get_tree_category(message: types.Message, state: FSMContext):
    cat = message.text
    await state.update_data(category=cat)
    if cat == "🍎 Mevali":
        await message.answer("Daraxt turini tanlang:", reply_markup=fruit_trees_kb())
    else:
        await message.answer("Manzarali daraxt nomini kiriting (masalan: Archa):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TreePlanting.name)

@router.message(TreePlanting.name)
async def get_tree_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📸 Daraxtning rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TreePlanting.photo)

@router.message(TreePlanting.photo, F.photo)
async def get_tree_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)
    loc_kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("✅ Rasm qabul qilindi. Endi joylashuvni yuboring:", reply_markup=loc_kb)
    await state.set_state(TreePlanting.location)

@router.message(TreePlanting.location, F.location)
async def save_tree_and_send_admin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    # Narx hisoblash: Mevali uchun 5000 + daraxt narxi. Manzarali uchun statik 5000.
    category = data.get("category")
    tree_type = data.get("name")
    
    if category == "🍎 Mevali":
        price = 5000 + FRUIT_PRICES.get(tree_type, 0)
    else:
        price = 5000 # Manzarali daraxt qat'iy narxi
        
    payload = {
        "user_id": message.from_user.id,
        "user_name": message.from_user.full_name,
        "category": category,
        "tree_type": tree_type,
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
        "photo": data.get("photo"),
        "price": price
    }

    async with aiohttp.ClientSession() as session:
        # Backendga yozish
        async with session.post(f"{BACKEND_URL}/trees/", json=payload) as resp:
            if resp.status == 200:
                result = await resp.json()
                tree_id = result["tree_id"]
                
                # Adminga yuborish
                kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"approve_{tree_id}_{message.from_user.id}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{tree_id}_{message.from_user.id}")
                ]])
                
                await message.bot.send_photo(
                    ADMIN_ID, photo=data.get("photo"), 
                    caption=f"🌳 Yangi {category} daraxt!\nIsm: {message.from_user.full_name}\nTuri: {tree_type}\nKutilayotgan to'lov: {price} so'm",
                    reply_markup=kb
                )
                await message.answer("Sizning ma'lumotlaringiz adminga yuborildi!", reply_markup=main_menu())
            else:
                await message.answer("❌ Xatolik yuz berdi.", reply_markup=main_menu())
    await state.clear()

# --- ADMIN TASDIQLASHI ---
@router.callback_query(F.data.startswith("approve_"))
async def admin_approve(call: types.CallbackQuery):
    _, tree_id, user_id = call.data.split("_")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/trees/approve/{tree_id}") as resp:
            if resp.status == 200:
                await call.message.edit_caption(caption=call.message.caption + "\n\n✅ Qabul qilindi!")
                await call.bot.send_message(user_id, "Sizning daraxtingiz qabul qilindi va to'lov hisobingizga tushdi. Buni tekshirish uchun shaxsiy kabinetga kiring.")
            else:
                await call.answer("Xatolik!")

@router.callback_query(F.data.startswith("reject_"))
async def admin_reject(call: types.CallbackQuery):
    _, tree_id, user_id = call.data.split("_")
    
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BACKEND_URL}/trees/reject/{tree_id}")
    await call.message.edit_caption(caption=call.message.caption + "\n\n❌ Rad etildi!")
    await call.bot.send_message(user_id, "Siz yuborgan daraxt rad etildi.")
