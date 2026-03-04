from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN
import handlers

from states import TreeForm, PaymentForm

bot = Bot(BOT_TOKEN)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)


dp.register_message_handler(handlers.start, commands=["start"])

dp.register_message_handler(
    handlers.start_tree,
    lambda message: message.text == "🌳 Daraxt yuborish"
)

dp.register_message_handler(
    handlers.tree_type,
    state=TreeForm.tree_type
)

dp.register_message_handler(
    handlers.location,
    content_types=types.ContentType.LOCATION,
    state=TreeForm.location
)

dp.register_message_handler(
    handlers.phone,
    content_types=types.ContentType.CONTACT,
    state=TreeForm.phone
)

dp.register_message_handler(
    handlers.receive_photo,
    content_types=types.ContentType.PHOTO,
    state=TreeForm.photo
)

dp.register_callback_query_handler(
    handlers.admin_buttons,
    lambda c: c.data.startswith("accept_") or c.data.startswith("reject_")
)

dp.register_message_handler(handlers.payment_method, lambda m: m.text in ["💳 Karta", "📱 Telefon raqam"])

dp.register_message_handler(handlers.payment_card)

dp.register_message_handler(handlers.payment_phone)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)