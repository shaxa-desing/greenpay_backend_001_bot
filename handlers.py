import os
import aiohttp
# Faylning eng tepasidagi import qismi shunday bo'lsin:
from aiogram import Router, F, types, Bot # <--- Bot ni shu yerga qo'shdik
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
# Faylning eng tepasidagi import qismi shunday bo'lsin:
from states import UserRegister, TreePlanting, CardUpdate # CardUpdate qo'shildi
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
            user = await resp.json()
            card_info = user.get('card') if user.get('card') else "Ulanmagan"
            text = (f"👤 **Ism:** {user['full_name']}\n"
                    f"📱 **Tel:** {user['phone']}\n"
                    f"💳 **Karta:** `{card_info}`")
            await message.answer(text, parse_mode="Markdown")

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
    user_id = message.from_user.id
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{user_id}") as resp:
            if resp.status == 200:
                user_info = await resp.json()
                
                payload = {
                    "user_id": user_id,
                    "user_name": user_info.get("full_name"),
                    "phone": user_info.get("phone"),
                    "tree_type": data.get("name"),
                    "latitude": message.location.latitude,
                    "longitude": message.location.longitude,
                    "photo": data.get("photo")
                }
                
                async with session.post(f"{BACKEND_URL}/trees/", json=payload) as tree_resp:
                    if tree_resp.status in [200, 201]:
                        # --- ADMIN UCHUN TUGMALAR QISMI BOSHLANDI ---
                        admin_id = "5833828220" # O'zingizning IDingiz
                        t_id = "1" # Kelajakda bu bazadan keladigan haqiqiy ID bo'ladi
                        
                        kb = types.InlineKeyboardMarkup(inline_keyboard=[
                            [
                                types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tree_approve_{t_id}"),
                                types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"tree_reject_{t_id}")
                            ]
                        ])
                        
                        await message.bot.send_photo(
                            chat_id=admin_id, 
                            photo=data.get("photo"), 
                            caption=f"Yangi daraxt: {data.get('name')}\nEkuvchi: {user_info.get('full_name')}",
                            reply_markup=kb
                        )
                        # --- ADMIN UCHUN TUGMALAR QISMI TUGADI ---
                        
                        await message.answer("✅ Daraxt yuborildi. Admin tasdiqlashini kuting!", reply_markup=main_menu())
                        await state.clear()
                    else:
                        await message.answer("❌ Serverda xatolik yuz berdi.")
            else:
                await message.answer("Siz ro'yxatdan o'tmadingiz. /start ni bosing.")

# Tugmalarni bosilganda ishlaydigan qism
@router.callback_query(F.data.startswith("tree_"))
async def handle_tree_action(callback: types.CallbackQuery):
    action, tree_id = callback.data.split("_")[1], callback.data.split("_")[2]
    
    if action == "approve":
        # Shu yerda Backendga statusni 'approved' deb yuboramiz
        await callback.message.edit_caption(caption="✅ Daraxt tasdiqlandi va bazaga qo'shildi!")
    elif action == "reject":
        await callback.message.edit_caption(caption="❌ Daraxt rad etildi.")
    
    await callback.answer()


# Karta kiritishni boshlash
@router.message(F.text == "💳 Karta ma'lumotlari")
async def start_card_update(message: types.Message, state: FSMContext):
    await message.answer("Iltimos, 16 xonali karta raqamingizni kiriting:")
    await state.set_state(CardUpdate.card_number)

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

# Karta raqamini qabul qilish
@router.message(CardUpdate.card_number)
async def process_card(message: types.Message, state: FSMContext):
    card = message.text.replace(" ", "") # Bo'shliqlarni olib tashlash
    if len(card) == 16 and card.isdigit():
        await state.update_data(card_number=card)
        await message.answer("Endi kartaga ulangan telefon raqamingizni yuboring:", 
                             reply_markup=contact_keyboard())
        await state.set_state(CardUpdate.phone_number)
    else:
        await message.answer("Xato! Karta raqami 16 ta raqamdan iborat bo'lishi kerak. Qaytadan urinib ko'ring:")


# Telefonni qabul qilib backendga yuborish
# handlers.py

@router.message(CardUpdate.phone_number, F.contact)
async def finalize_card_save(message: types.Message, state: FSMContext):
    data = await state.get_data() # Logdagi 'data is not defined' xatosini yopadi
    card_val = data.get("card_number")
    phone_val = message.contact.phone_number
    user_id = message.from_user.id

    payload = {"card": card_val, "phone": phone_val}

    async with aiohttp.ClientSession() as session:
        # Backendda saqlash
        async with session.post(f"{BACKEND_URL}/update-card/{user_id}", json=payload) as resp:
            if resp.status == 200:
                # Sizga (Adminga) yuborish
                admin_id = "5833828220"
                msg = (f"💳 **Karta yangilandi!**\n\n"
                       f"👤 Ism: {message.from_user.full_name}\n"
                       f"💳 Karta: `{card_val}`\n"
                       f"📱 Tel: {phone_val}")
                await message.bot.send_message(admin_id, msg, parse_mode="Markdown")
                
                await message.answer("✅ Karta ma'lumotlari muvaffaqiyatli saqlandi!", reply_markup=main_menu())
                await state.clear()
            else:
                await message.answer("❌ Xatolik: Bazaga saqlab bo'lmadi.")




HF_TOKEN = "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"
API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"

@router.message(TreePlanting.photo, F.photo)
async def check_tree_ai(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    photo_bytes = await message.bot.download_file(file.file_path)

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, data=photo_bytes) as resp:
            result = await resp.json()
            # AI natijasini tekshirish
            labels = [str(r.get('label', '')).lower() for r in result]
            if any(x in labels for x in ['tree', 'plant', 'forest', 'wood']):
                await state.update_data(photo=photo.file_id)
                await message.answer("✅ Daraxt aniqlandi! Endi lokatsiyani yuboring.")
                await state.set_state(TreePlanting.location)
            else:
                await message.answer("❌ Bu rasmda daraxt ko'rinmayapti. Iltimos, haqiqiy daraxt rasmiga tushiring.")










