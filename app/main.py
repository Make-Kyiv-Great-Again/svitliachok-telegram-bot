import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.config import config
from app.db import init_db
from app.handlers import auth, business

# Set up logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Initialize SQLite database
    await init_db()

    # Initialize bot and dispatcher
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    # Include routers
    dp.include_router(auth.router)
    dp.include_router(business.router)

    # Start polling
    logging.info("Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
