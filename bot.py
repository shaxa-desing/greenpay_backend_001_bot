import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import router

BOT_TOKEN = "8565818987:AAEciIAbwHVGjkuJ7TwwdCfKjKlXYj8annI"

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
