import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import API_TOKEN
from dataBase import db  # твій файл db.py, де створюються таблиці
from handlers import menu, registration

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Ініціалізація FSM
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Ініціалізація бота
bot = Bot(token=API_TOKEN)

# Підключаємо всі роутери
dp.include_router(registration.router)
dp.include_router(menu.router)


async def main():
    try:
        # Ініціалізація бази даних
        logger.info("🔄 Ініціалізація бази даних...")
        db.init_db()
        logger.info("✅ База даних успішно ініціалізована")
        
        # Запуск бота
        logger.info("🤖 Бот запускається...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Помилка запуску бота: {e}")
    finally:
        logger.info("🛑 Бот зупинено")


if __name__ == "__main__":
    asyncio.run(main())