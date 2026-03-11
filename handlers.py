import os
import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import UserRegister, TreePlanting, CardUpdate
from keyboards import main_menu, contact_keyboard

router = Router()
BACKEND_URL = os.getenv("BACKEND_URL", "https://greenpaybackend-production.up.railway.app/").rstrip('/')
HF_TOKEN = "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" # Shu yerga tokenni qo'ying
API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"

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
                card_info = user.get('card') if user.get('card') else "Ulanmagan"
                text = (f"👤 **Ism:** {user.get('full_name', 'Noma`lum')}\n"
                        f"📱 **Tel:** {user.get('phone', 'Noma`lum')}\n"
                        f"💳 **Karta:** `{card_info}`")
                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("Ma'lumot topilmadi.")

# --- DARAXT EKISH VA AI TEKSHIRUV ---
@router.message(F.text == "🌳 Daraxt ekish")
async def start_tree(message: types.Message, state: FSMContext):
    await message.answer("Daraxtga nom bering (masalan: Archa):")
    await state.set_state(TreePlanting.name)

@router.message(TreePlanting.name)
async def get_tree_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Daraxt rasmini yuboring (AI tekshiradi):")
    await state.set_state(TreePlanting.photo)

@router.message(TreePlanting.photo, F.photo)
async def check_tree_ai(message: types.Message, state: FSMContext):
    msg = await message.answer("🔍 Rasm tekshirilmoqda...")
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    photo_bytes = await message.bot.download_file(file.file_path)

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, headers=headers, data=photo_bytes) as resp:
                result = await resp.json()
                full_text = str(result).lower()
                keywords = ['tree', 'plant', 'forest', 'nature', 'leaf', 'wood']
                
                if any(word in full_text for word in keywords):
                    await state.update_data(photo=photo.file_id)
                    kb = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="📍 Joylashuv", request_location=True)]], resize_keyboard=True)
                    await msg.edit_text("✅ Daraxt aniqlandi! Endi lokatsiyani yuboring.", reply_markup=kb)
                    await state.set_state(TreePlanting.location)
                else:
                    await msg.edit_text("❌ Bu rasmda daraxt aniqlanmadi. Iltimos, boshqa rasm yuboring.")
        except:
            await state.update_data(photo=photo.file_id)
            await msg.edit_text("⚠️ AI vaqtinchalik ishlamayapti, lekin rasmni qabul qildim. Lokatsiyani yuboring.")
            await state.set_state(TreePlanting.location)

@router.message(TreePlanting.location, F.location)
async def save_tree(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    admin_id = "5833828220"

    payload = {
        "user_id": user_id,
        "tree_type": data.get("name"),
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
        "photo": data.get("photo")
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/trees/", json=payload) as resp:
            if resp.status in [200, 201]:
                await message.answer("✅ Ma'lumotlar adminga yuborildi. Tasdiqlashni kuting.", reply_markup=main_menu())
                
                # Adminga xabar yuborish
                kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tree_approve_{user_id}"),
                        types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"tree_reject_{user_id}")
                    ]
                ])
                await message.bot.send_photo(admin_id, photo=data.get("photo"), 
                                           caption=f"🌳 Yangi daraxt!\nKimdan: {message.from_user.full_name}\nNomi: {data.get('name')}", 
                                           reply_markup=kb)
                await state.clear()

# --- ADMIN TASDIQLASH LOGIKASI ---
@router.callback_query(F.data.startswith("tree_"))
async def handle_tree_action(callback: types.CallbackQuery):
    action, target_user_id = callback.data.split("_")[1], callback.data.split("_")[2]
    
    if action == "approve":
        try:
            await callback.bot.send_message(target_user_id, "🌟 Tabriklaymiz! Daraxtingiz admin tomonidan tasdiqlandi.")
            await callback.message.edit_caption(caption="✅ Tasdiqlandi va foydalanuvchiga xabar yuborildi.")
        except:
            await callback.answer("Foydalanuvchiga xabar yetmadi.")
    elif action == "reject":
        await callback.bot.send_message(target_user_id, "❌ Afsuski, yuborgan rasmingiz rad etildi.")
        await callback.message.edit_caption(caption="❌ Rad etildi.")
    await callback.answer()

# --- KARTA MA'LUMOTLARI ---
@router.message(F.text == "💳 Karta ma'lumotlari")
async def show_card_info(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{user_id}") as resp:
            if resp.status == 200:
                user_data = await resp.json()
                if user_data.get("card"):
                    text = f"Sizning ulangan kartangiz: `{user_data['card']}`\n\nYangilashni xohlaysizmi?"
                    kb = types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="update_card_start")]
                    ])
                    await message.answer(text, reply_markup=kb, parse_mode="Markdown")
                else:
                    await message.answer("Sizda karta ulanmagan. Karta raqamingizni kiriting (16 xonali):")
                    await state.set_state(CardUpdate.card_number)
            else:
                await message.answer("Avval /start orqali ro'yxatdan o'ting.")

# Inline tugma bosilganda yangilashni boshlash
@router.callback_query(F.data == "update_card_start")
async def update_card_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Yangi karta raqamingizni kiriting:")
    await state.set_state(CardUpdate.card_number)
    await callback.answer()


@router.callback_query(F.data == "update_card_start")
async def start_update_card(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Yangi karta raqamingizni kiriting:")
    await state.set_state(CardUpdate.card_number)
    await callback.answer()

@router.message(CardUpdate.card_number)
async def process_card_number(message: types.Message, state: FSMContext):
    card = message.text.replace(" ", "")
    if len(card) == 16 and card.isdigit():
        await state.update_data(card_number=card)
        await message.answer("Kartaga ulangan telefon raqamingizni yuboring:", reply_markup=contact_keyboard())
        await state.set_state(CardUpdate.phone_number)
    else:
        await message.answer("⚠️ Xato! 16 ta raqam kiriting:")

@router.message(CardUpdate.phone_number, F.contact)
async def save_card_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    payload = {"card": data.get("card_number"), "phone": message.contact.phone_number}

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/update-card/{user_id}", json=payload) as resp:
            if resp.status == 200:
                # Adminga bildirishnoma
                await message.bot.send_message("5833828220", f"💳 Karta yangilandi!\nKim: {message.from_user.full_name}\nKarta: {data.get('card_number')}")
                await message.answer("✅ Karta muvaffaqiyatli saqlandi!", reply_markup=main_menu())
                await state.clear()
            else:
                await message.answer("❌ Xatolik yuz berdi.")

