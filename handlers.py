import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
# handlers.py faylining tepasidagi importlar qatori
from states import TreeForm, PaymentForm, UserRegister # <-- UserRegister ni qo'shing
from keyboards import main_menu, location_keyboard, admin_keyboard, payment_keyboard

from config import BACKEND_URL, ADMIN_ID

router = Router()

# --- ASOSIY MENYU ---

# State uchun: class UserRegister(StatesGroup): name = State()

@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # 1. Avval foydalanuvchi bazada bormi tekshiramiz
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BACKEND_URL}/user/{user_id}") as resp:
            if resp.status == 200:
                await message.answer("Siz allaqachon ro'yxatdan o'tgansiz!", reply_markup=main_menu())
            else:
                # 2. Agar yo'q bo'lsa, ro'yxatdan o'tishni boshlaymiz
                await message.answer("Xush kelibsiz! Iltimos, ism-familiyangizni kiriting:")
                await state.set_state(UserRegister.name)

# Botning handlers.py faylida ro'yxatdan o'tish funksiyasida:
print(f"URL: {BACKEND_URL}/users/")
print(f"Payload: {payload}")

async with session.post(f"{BACKEND_URL}/users/", json=payload) as resp:
    status = resp.status
    response_text = await resp.text()
    print(f"Backend javobi: {status}, Text: {response_text}") # <--- SHUNI TEKSHIRING


@router.message(UserRegister.name)
async def save_user(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.text

    # BACKEND_URL oxirida slash bor-yo'qligini tekshirib, xavfsiz URL yaratamiz
    clean_url = BACKEND_URL.rstrip('/') # Oxiridagi slashni olib tashlaymiz
    final_url = f"{clean_url}/users/"   # Backend kutayotgan aniq manzil

@router.message(UserRegister.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Endi pastdagi tugmani bosib, telefon raqamingizni yuboring:", 
                         reply_markup=contact_keyboard())
    await state.set_state(UserRegister.phone)

@router.message(UserRegister.phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username # @username ni olish
    
    payload = {
        "user_id": user_id,
        "user_name": data['full_name'],
        "username": f"@{username}" if username else "Yo'q",
        "phone": message.contact.phone_number
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BACKEND_URL}/users/", json=payload) as resp:
            if resp.status in [200, 201]:
                await message.answer("✅ Ro'yxatdan o'tdingiz!", reply_markup=main_menu())
                await state.clear()
            else:
                await message.answer("❌ Xatolik yuz berdi.")




@router.message(F.text == "👤 Shaxsiy kabinet")
async def show_profile(message: types.Message):
    async with aiohttp.ClientSession() as session:
        # Bu yerda /user/{id} slashsiz bo'lishi mumkin, 
        # lekin backenddagi kodingiz bilan bir xilligini tekshiring
        async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
            if resp.status == 200:
                user = await resp.json()
                text = (
                    f"👤 **Sizning profilingiz:**\n\n"
                    f"🆔 ID: `{user['user_id']}`\n"
                    f"👤 Ism: {user['full_name']}\n"
                    f"💳 Karta: {user.get('card') or 'Kiritilmagan'}\n"
                    f"📱 Tel: {user.get('phone_pay') or 'Kiritilmagan'}"
                )
                await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("⚠️ Siz hali ro'yxatdan o'tmagansiz. Iltimos, /start bosing.")


# --- QO'LLANMA ---
@router.message(F.text == "📖 Qo'llanma")
async def show_guide(message: types.Message):
    video_id = "BAACAgIAAxkBAAIE4GmsCRtT9aUk6DA3x9-aj_ddmAxXAALtlAACm_BhSSm97-LFW-9qOgQ" 
    guide_text = (
        "📖 **GreenPay bot qo'llanmasi**\n\n"
        "1️⃣ '🌳 Daraxt yuborish' tugmasini bosing.\n"
        "2️⃣ Daraxt turi, joylashuvi va rasmini yuboring.\n"
        "3️⃣ Admin tasdiqlaganidan so'ng, to'lov ma'lumotlarini kiritasiz.\n\n"
        "🎥 Batafsil videoda ko'ring:"
    )
    try:
        await message.answer_video(video=video_id, caption=guide_text, parse_mode="Markdown")
    except:
        await message.answer(guide_text, parse_mode="Markdown")

# --- DARAXT YUBORISH JARAYONI ---
@router.message(F.text == "🌳 Daraxt yuborish")
async def start_tree(message: types.Message, state: FSMContext):
    await message.answer("Daraxt turini kiriting (masalan: Archa, Pavlovniya):")
    await state.set_state(TreeForm.tree_type)

@router.message(TreeForm.tree_type)
async def set_tree_type(message: types.Message, state: FSMContext):
    await state.update_data(tree_type=message.text)
    await message.answer("📍 Daraxt ekilgan joy lokatsiyasini yuboring:", reply_markup=location_keyboard())
    await state.set_state(TreeForm.location)

@router.message(TreeForm.location, F.location)
async def set_location(message: types.Message, state: FSMContext):
    await state.update_data(lat=message.location.latitude, lon=message.location.longitude)
    await message.answer("📷 Daraxtning rasmini yuboring (Sifatli rasm bo'lsin):")
    await state.set_state(TreeForm.photo)

@router.message(TreeForm.photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id # Eng sifatli rasmni olish
    
    # 1. Foydalanuvchini bazaga yozish
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BACKEND_URL}/users/", json={
            "user_id": message.from_user.id,
            "user_name": message.from_user.full_name,
            "phone": "" # Agar schemas.py da bu maydon majburiy bo'lsa qo'shish kerak
        })
        
        # 2. MUHIM: Daraxt ma'lumotlarini Backendga yuborish (Sizda shu narsa yo'q edi!)
        tree_payload = {
            "user_id": message.from_user.id,
            "user_name": message.from_user.full_name,
            "phone": "Noma'lum", # Keyinchalik to'g'rilash mumkin
            "tree_type": data['tree_type'],
            "latitude": data['lat'],
            "longitude": data['lon'],
            "photo": file_id
        }
        
        # Bu yerdagi /trees/ manziliga murojaat qilinmoqda
        tree_resp = await session.post(f"{BACKEND_URL}/trees/", json=tree_payload)
        print(f"Backend javobi (Daraxt yuborish): {tree_resp.status}")

    caption = (f"🌳 **Yangi daraxt so'rovi!**\n\n"
               f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
               f"🌲 Turi: {data['tree_type']}\n"
               f"📍 Lokatsiya: `{data['lat']}, {data['lon']}`")
    
    # Adminga yuborish
    await message.bot.send_photo(
        ADMIN_ID, 
        file_id, 
        caption=caption, 
        reply_markup=admin_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )
    
    await message.answer("✅ Rahmat! Ma'lumotlar adminga yuborildi va bazaga saqlandi. Tasdiqlashni kuting.", reply_markup=main_menu())
    await state.clear()

# --- ADMIN TASDIQLASHI ---
@router.callback_query(F.data.startswith("accept_"))
async def admin_accept(call: types.CallbackQuery):
    await call.answer("Tasdiqlandi")
    user_id = int(call.data.split("_")[1])
    
    # Admindagi xabarni o'zgartirib qo'yamiz (Tugmalarni olib tashlaymiz)
    await call.message.edit_caption(
        caption=f"{call.message.caption}\n\n✅ **QABUL QILINDI**",
        reply_markup=None
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BACKEND_URL}/user/{user_id}") as resp:
                user_data = await resp.json() if resp.status == 200 else {}
                if user_data.get('card') or user_data.get('phone_pay'):
                    card = user_data.get('card', "Mavjud emas")
                    phone = user_data.get('phone_pay', "Mavjud emas")
                    await call.bot.send_message(
                        ADMIN_ID, 
                        f"💰 **To'lov ma'lumotlari (Avtomatik):**\n\n👤 ID: {user_id}\n💳 Karta: `{card}`\n📱 Raqam: `{phone}`",
                        parse_mode="Markdown"
                    )
                    await call.bot.send_message(user_id, "✅ Daraxtingiz tasdiqlandi! To'lov ma'lumotlaringiz adminga yuborildi.", reply_markup=main_menu())
                else:
                    await call.bot.send_message(user_id, "✅ Daraxtingiz tasdiqlandi! To'lov ma'lumotlarini kiriting:", reply_markup=payment_keyboard())
        except Exception as e:
            print(f"Error in admin_accept: {e}")
            await call.bot.send_message(user_id, "✅ Tasdiqlandi, lekin to'lov ma'lumotlarini olishda xato yuz berdi.")

# --- ADMIN RAD ETISHI ---
@router.callback_query(F.data.startswith("reject_"))
async def admin_reject(call: types.CallbackQuery):
    # 1. Tezkor javob
    await call.answer("Rad etildi")
    user_id = int(call.data.split("_")[1])
    
    # 2. Tugmalarni olib tashlash (edit_caption o'rniga faqat tugmalarni tozalash)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except:
        pass # Agar tugmalar bo'lmasa, o'tkazib yuborish

    # 3. Foydalanuvchiga xabar yuborish
    try:
        await call.bot.send_message(
            user_id, 
            "❌ Daraxtingiz ma'lumotlari admin tomonidan rad etildi. Iltimos, ma'lumotlarni tekshirib qaytadan yuboring.", 
            reply_markup=main_menu()
        )
    except Exception as e:
        print(f"Xabar yuborishda xato: {e}")

    # Foydalanuvchiga rad etilgani haqida xabar yuboramiz
    reject_text = (
        "❌ **Kechirasiz, siz yuborgan daraxt ma'lumotlari admin tomonidan rad etildi.**\n\n"
        "Sabablar quyidagilardan biri bo'lishi mumkin:\n"
        "• Rasm sifatsiz yoki noaniq.\n"
        "• Lokatsiya xato yuborilgan.\n"
        "• Daraxt turi noto'g'ri kiritilgan.\n\n"
        "Iltimos, ma'lumotlarni tekshirib qaytadan yuboring."
    )
    
    try:
        await call.bot.send_message(user_id, reject_text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        print(f"Xabar yuborishda xatolik (Rad etish): {e}")
# --- TO'LOV MA'LUMOTLARINI SAQLASH ---
@router.message(F.text.in_(["💳 Karta", "📱 Telefon raqam"]))
async def start_payment_save(message: types.Message, state: FSMContext):
    method = "card" if "Karta" in message.text else "phone_pay"
    await state.update_data(pay_method=method)
    await message.answer(f"Iltimos, {message.text} ma'lumotlarini kiriting (Masalan: 8600... yoki +998...):")
    await state.set_state(PaymentForm.details)

@router.message(PaymentForm.details)
async def save_payment_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    method = data['pay_method']
    val = message.text
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(f"{BACKEND_URL}/update_payment/", json={
                "user_id": message.from_user.id,
                "user_name": message.from_user.full_name,
                method: val
            })
            await message.bot.send_message(
                ADMIN_ID, 
                f"🆕 **Yangi to'lov ma'lumotlari saqlandi:**\n👤 {message.from_user.full_name}\n📝 {method}: `{val}`",
                parse_mode="Markdown"
            )
        except:
            pass
    await message.answer("✅ Ma'lumotlaringiz saqlandi va adminga yuborildi!", reply_markup=main_menu())
    await state.clear()









