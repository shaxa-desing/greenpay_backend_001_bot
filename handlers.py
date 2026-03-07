import aiohttp
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import TreeForm, PaymentForm
from keyboards import main_menu, location_keyboard, admin_keyboard, payment_keyboard
from config import BACKEND_URL, ADMIN_ID

router = Router()

# --- ASOSIY MENYU ---

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("GreenPay botiga xush kelibsiz!", reply_markup=main_menu())

@router.message(F.text == "👤 Shaxsiy kabinet")
async def show_profile(message: types.Message):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BACKEND_URL}/user/{message.from_user.id}") as resp:
                if resp.status == 200:
                    user = await resp.json()
                    await message.answer(f"👤 **Kabinet**\n🆔 ID: {user.get('user_id')}\n💳 Karta: {user.get('card', 'Yoq')}\n📱 Tel: {user.get('phone_pay', 'Yoq')}", parse_mode="Markdown")
                else:
                    await message.answer("Siz hali ro'yxatdan o'tmagansiz. Daraxt yuboring!")
        except:
            await message.answer("Server bilan aloqa uzildi.")

@router.message(F.text == "🌳 Daraxt yuborish")
async def start_tree(message: types.Message, state: FSMContext):
    await message.answer("Daraxt turini kiriting:")
    await state.set_state(TreeForm.tree_type)

@router.message(TreeForm.photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Foydalanuvchini bazaga yozish (yangi bo'lsa)
    async with aiohttp.ClientSession() as session:
        await session.post(f"{BACKEND_URL}/users", json={
            "user_id": message.from_user.id,
            "user_name": message.from_user.full_name
        })
    # Adminga yuborish
    await message.bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🌳 Yangi daraxt: {data['tree_type']}", reply_markup=admin_keyboard(message.from_user.id))
    await message.answer("✅ Ma'lumotlar saqlandi!")
    await state.clear()

# --- QO'LLANMA (Video va Ma'lumot) ---
@router.message(F.text == "📖 Qo'llanma")
async def show_guide(message: types.Message):
    # Bu yerga botdan olgan file_id ni qo'yasiz
    video_id = "BAACAgIAAxkBAAIE4GmsCRtT9aUk6DA3x9-aj_ddmAxXAALtlAACm_BhSSm97-LFW-9qOgQ" # O'sha uzun kodni shu yerga yozing
    
    guide_text = (
        "📖 **GreenPay bot qo'llanmasi**\n\n"
        "1️⃣ '🌳 Daraxt yuborish' tugmasini bosing.\n"
        "2️⃣ Daraxt turi, joylashuvi va rasmini yuboring.\n"
        "3️⃣ Admin tasdiqlaganidan so'ng, to'lov ma'lumotlarini kiritasiz.\n\n"
        "🎥 Batafsil videoda ko'ring:"
    )
    
    try:
        await message.answer_video(
            video=video_id,
            caption=guide_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        # Agar video yuborishda xato bo'lsa, matnni o'zini yuboradi
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
    caption = (f"🌳 **Yangi daraxt so'rovi!**\n\n"
               f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
               f"🌲 Turi: {data['tree_type']}\n"
               f"📍 Lokatsiya: `{data['lat']}, {data['lon']}`")
    
    # Adminga yuborish
    await message.bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=caption, 
        reply_markup=admin_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )
    await message.answer("✅ Rahmat! Ma'lumotlar adminga yuborildi. Tasdiqlashni kuting.", reply_markup=main_menu())
    await state.clear()

# --- ADMIN TASDIQLASHI VA AVTOMATIK TO'LOV ---
@router.callback_query(F.data.startswith("accept_"))
async def admin_accept(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BACKEND_URL}/user/{user_id}") as resp:
                user_data = await resp.json() if resp.status == 200 else {}
                
                # Agar karta yoki telefon avval saqlangan bo'lsa
                if user_data.get('card') or user_data.get('phone_pay'):
                    card = user_data.get('card', "Mavjud emas")
                    phone = user_data.get('phone_pay', "Mavjud emas")
                    
                    # Adminga ma'lumotlarni yuborish
                    await call.bot.send_message(
                        ADMIN_ID, 
                        f"💰 **To'lov ma'lumotlari (Avtomatik):**\n\n👤 ID: {user_id}\n💳 Karta: `{card}`\n📱 Raqam: `{phone}`",
                        parse_mode="Markdown"
                    )
                    await call.bot.send_message(user_id, "✅ Daraxtingiz tasdiqlandi! To'lov ma'lumotlaringiz adminga yuborildi.", reply_markup=main_menu())
                else:
                    # Agar birinchi marta bo'lsa
                    await call.bot.send_message(user_id, "✅ Daraxtingiz tasdiqlandi! To'lov ma'lumotlarini kiriting:", reply_markup=payment_keyboard())
        except:
            await call.bot.send_message(user_id, "✅ Tasdiqlandi, lekin to'lov ma'lumotlarini olishda xato yuz berdi.")
    
    await call.answer("Tasdiqlandi")

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
            # Backendda foydalanuvchi ma'lumotlarini yangilash
            await session.post(f"{BACKEND_URL}/update_payment", json={
                "user_id": message.from_user.id,
                "user_name": message.from_user.full_name,
                method: val
            })
            
            # Adminga ham xabar yuboramiz
            await message.bot.send_message(
                ADMIN_ID, 
                f"🆕 **Yangi to'lov ma'lumotlari saqlandi:**\n👤 {message.from_user.full_name}\n📝 {method}: `{val}`",
                parse_mode="Markdown"
            )
        except:
            pass

    await message.answer("✅ Ma'lumotlaringiz saqlandi va adminga yuborildi!", reply_markup=main_menu())
    await state.clear()


# @router.message(F.video)
# async def get_video_id(message: types.Message):
#     video_id = message.video.file_id
#     # Markdown o'rniga oddiy matn qilib yuboramiz
#     await message.answer(f"Sizning video file_id:\n\n{video_id}")
