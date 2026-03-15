import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import router

# DIQQAT: Bot tokeningizni aniq shu yerga qo'shtirnoq ichida yozing!
BOT_TOKEN = "8565818987:AAFtp_uIUnZOdeqLRjWP2E_2eObcEFLJ28o"

async def main():
    # Bot obyektini yaratish
    bot = Bot(token=BOT_TOKEN)
    
    # Dispatcher - barcha xabarlar va buyruqlarni boshqaradi
    dp = Dispatcher()
    
    # handlers.py faylidagi routerni ulaymiz
    dp.include_router(router)
    
    # Bot o'chiq paytida kelgan eski xabarlarga javob bermasligi uchun
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("✅ Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda...")
    
    # Botni doimiy ishlab turish rejimida (polling) yoqish
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Terminalda jarayonlarni va ehtimoliy xatoliklarni ko'rsatib turish uchun
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("❌ Bot to'xtatildi.")
