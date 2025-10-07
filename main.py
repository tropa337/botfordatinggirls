import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import API_TOKEN
from dataBase import db  # твой файл db.py, где создаются таблицы
from handlers import menu, registration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Инициализируем FSM
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


db.init_db()  # создаем таблицу

bot = Bot(token=API_TOKEN)

# Подключаем все роутеры
dp.include_router(registration.router)
dp.include_router(menu.router)


async def main():
    logging.info("🤖 Бот запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

