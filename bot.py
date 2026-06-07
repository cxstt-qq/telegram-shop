import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config_data.config import config
from database.db import init_db

# Импорт мидлварей и локализации
from middlewares.i18n import L10nMiddleware, create_translator_hub

# Импорт общих хэндлеров
from handlers import common

# Импорт админских хэндлеров (stats добавлен сюда)
from handlers.admin import admin_main, categories, products, users_man, stats, mailing, notifications, referrals

# Импорт пользовательских хэндлеров
from handlers.user import user_main, profile, shop, payments
from handlers.user.payments import crypto # Импортируем экземпляр CryptoPay


async def main():
    # Настраиваем логирование: и в консоль, и в файл bot.log
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Запуск бота...")

    # Инициализируем бота
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()

    # Регистрация функции создания таблиц БД при запуске
    dp.startup.register(init_db)

    # Настройка локализации и регистрация мидлварей
    translator_hub = create_translator_hub()
    dp.message.middleware(L10nMiddleware(translator_hub))
    dp.callback_query.middleware(L10nMiddleware(translator_hub))

    # --- РЕГИСТРАЦИЯ РОУТЕРОВ (ПОРЯДОК СТРОГО ТАКОЙ!) ---
    
    # 1. Сначала общий роутер (отмена FSM)
    dp.include_router(common.router)
    
    # 2. Затем вся админка (теперь stats.router точно на месте)
    dp.include_router(admin_main.router)
    dp.include_router(categories.router)
    dp.include_router(products.router)
    dp.include_router(users_man.router)
    dp.include_router(stats.router)
    dp.include_router(mailing.router)
    dp.include_router(notifications.router)
    dp.include_router(referrals.router)
    
    # 3. В конце пользовательская часть
    dp.include_router(user_main.router)
    dp.include_router(profile.router)
    dp.include_router(shop.router)
    dp.include_router(payments.router)

    # Пропускаем старые апдейты и запускаем пуллинг
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await crypto.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")
