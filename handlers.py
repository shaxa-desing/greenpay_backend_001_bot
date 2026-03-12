import os
import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import UserRegister, TreePlanting, CardUpdate
from keyboards import main_menu, contact_keyboard

router = Router()

# Konfuralar
BACKEND_URL = os.getenv("BACKEND_URL", "https://greenpaybackend-production.up.railway.app").rstrip('/')
HF_TOKEN = "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" 
API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"

# --- START & RO'YXATDAN O'TISH ---
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
            if resp.status == 200:
                await message.answer("Xush kelibsiz! Siz ro'yxatdan o'tgansiz.", reply_markup=main_menu())
            else:
                await message.answer("Assalomu alaykum! Green Pay botiga xush kelibsiz.\nRo'yxatdan o'tish uchun Ism-familiyangizni kiriting:")
                await state.set_state(UserRegister.name)

@router.message(UserRegister.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📱 Telefon raqamingizni pastdagi tugma orqali yuboring:", reply_markup=contact_keyboard())
    await state.set_state(UserRegister.phone)

@router.message(UserRegister.phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Payload indentatsiyasi to'g'rilandi
    # handlers.py ichidagi ro'yxatdan o'tish qismi:
    payload = {
        "user_id": message.from_user.id,
        "full_name": data.get('name'), # 'name' o'rniga 'full_name' bo'lishi ham mumkin, tekshiring
        "phone": message.contact.phone_number
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/users/", json=payload) as resp:
            if resp.status in [200, 201]:
                await message.answer("✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=main_menu())
                await state.clear()
            else:
                await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

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
                await message.answer("Ma'lumot topilmadi. /start tugmasini bosing.")

# --- DARAXT EKISH VA AI TEKSHIRUV ---
@router.message(F.text == "🌳 Daraxt ekish")
async def start_tree(message: types.Message, state: FSMContext):
    await message.answer("Daraxtga nom bering (masalan: Archa yoki Akatsiya):")
    await state.set_state(TreePlanting.name)

@router.message(TreePlanting.name)
async def get_tree_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📸 Daraxtning aniq rasmini yuboring (AI tekshiradi):")
    await state.set_state(TreePlanting.photo)

# --- DARAXT EKISH VA AI TEKSHIRUV ---
@router.message(TreePlanting.photo, F.photo)
async def check_tree_ai(message: types.Message, state: FSMContext):
    # 1. Kutib turish xabarini yuboramiz
    msg = await message.answer("🔍 AI rasmda nima borligini tezkor tekshirmoqda...")
    
    # Telegramdan eng yuqori sifatli rasmni olamiz
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    photo_bytes = await message.bot.download_file(file.file_path)

    # 2. Lokatsiya sorash uchun tugma (faqat tasdiqlansa ko'rinadi)
    loc_kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]], 
        resize_keyboard=True,
        one_time_keyboard=True
    )

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # API dan keladigan kalit so'zlar ro'yxati (AI daraxtni taniy olishi uchun)
    tree_keywords = ['tree', 'plant', 'forest', 'leaf', 'nature', 'wood', 'pine', 'oak']

    async with aiohttp.ClientSession() as session:
        try:
            # HuggingFace API ga so'rov yuborish (Sizning oldingi kodingizdek)
            async with session.post(API_URL, headers=headers, data=photo_bytes) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    # Natijalar ichidan daraxtga oid so'zlarni qidiramiz
                    # is_tree = True bo'ladi, agar topilsa
                    is_tree = any(item.get('label', '').lower() in tree_keywords for item in result)
                    
                    # 3. Kutish xabarini o'chiramiz
                    await msg.delete() 
                    
                    if is_tree:
                        await state.update_data(photo=photo.file_id)
                        await message.answer(
                            "✅ Ajoyib! AI rasmda daraxt borligini tasdiqladi.\nEndi daraxt joylashgan lokatsiyani yuboring:", 
                            reply_markup=loc_kb
                        )
                        await state.set_state(TreePlanting.location)
                    else:
                        await message.answer(
                            "❌ Kechirasiz, AI tizimi rasmda daraxtni aniqlay olmadi.\nIltimos, yorug'roq joyda va daraxt to'liq ko'rinadigan qilib qayta rasm yuboring."
                        )
                        # State o'zgarmaydi, bot yana rasm kutishda davom etadi
                else:
                    await msg.delete()
                    await message.answer("⚠️ AI xizmatida vaqtincha uzilish. Iltimos, birozdan so'ng qayta urinib ko'ring.")

        except Exception as e:
            await msg.delete()
            print(f"AI tekshiruvda xatolik: {e}")
            await message.answer("⚠️ Kutilmagan xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")





@router.message(TreePlanting.location, F.location)
async def save_tree(message: types.Message, state: FSMContext):
    data = await state.get_data()
    admin_id = "5833828220" 

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
                await message.answer("✅ Ma'lumotlar adminga yuborildi. Rahmat!", reply_markup=main_menu())
                
                kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tree_approve_{message.from_user.id}"),
                        types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"tree_reject_{message.from_user.id}")
                    ]
                ])
                await message.bot.send_photo(
                    admin_id, 
                    photo=data.get("photo"), 
                    caption=f"🌳 Yangi daraxt!\nKimdan: {message.from_user.full_name}\nNomi: {data.get('name')}\nManzil: {payload['latitude']}, {payload['longitude']}", 
                    reply_markup=kb
                )
                await state.clear()
            else:
                await message.answer("❌ Serverga yuborishda xatolik.")

# --- KARTA MA'LUMOTLARI ---
@router.message(F.text == "💳 Karta ma'lumotlari")
async def show_card_info(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
            if resp.status == 200:
                user_data = await resp.json()
                if user_data.get("card"):
                    text = f"Sizning ulangan kartangiz: `{user_data['card']}`\n\nYangilashni xohlaysizmi?"
                    kb = types.InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="update_card_start")]
                    ])
                    await message.answer(text, reply_markup=kb, parse_mode="Markdown")
                else:
                    await message.answer("Sizda hali karta ulanmagan. Karta raqamingizni kiriting (16 xonali):")
                    await state.set_state(CardUpdate.card_number)
            else:
                await message.answer("Avval ro'yxatdan o'ting.")

@router.callback_query(F.data == "update_card_start")
async def update_card_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Yangi 16 xonali karta raqamini kiriting:")
    await state.set_state(CardUpdate.card_number)
    await callback.answer()

@router.message(CardUpdate.card_number)
async def process_card_number(message: types.Message, state: FSMContext):
    card = message.text.replace(" ", "")
    if len(card) == 16 and card.isdigit():
        await state.update_data(card_number=card)
        await message.answer("📱 Kartaga ulangan telefon raqamingizni yuboring:", reply_markup=contact_keyboard())
        await state.set_state(CardUpdate.phone_number)
    else:
        await message.answer("⚠️ Xato! Karta raqami 16 ta raqamdan iborat bo'lishi kerak:")

@router.message(CardUpdate.phone_number, F.contact)
async def save_card_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Karta raqami va telefon raqamini to'g'ri shaklda yuborish
    payload = {
        "card": str(data.get("card_number")),
        "phone": str(message.contact.phone_number)
    }

    async with aiohttp.ClientSession() as session:
        # URL va payloadni logga chiqaramiz (xatoni aniqlash uchun)
        url = f"{BACKEND_URL}/update-card/{message.from_user.id}"
        async with session.post(url, json=payload) as resp:
            response_text = await resp.text() # Server nima deganini ko'ramiz
            if resp.status == 200:
                await message.answer("✅ Karta muvaffaqiyatli saqlandi!", reply_markup=main_menu())
                await state.clear()
            else:
                # Xatolikni batafsilroq ko'rsatish
                print(f"Server error: {resp.status}, Body: {response_text}")
                await message.answer(f"❌ Karta saqlashda xatolik yuz berdi. (Status: {resp.status})")





