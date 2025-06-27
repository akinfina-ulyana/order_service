import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from telegram_bot.handlers import router  # Импортируем router из handlers.py


async def main():
    # Инициализация бота
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'), parse_mode=ParseMode.HTML)

    # Настройка диспетчера
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Запуск бота
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())