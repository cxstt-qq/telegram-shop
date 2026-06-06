import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config_data.config import config

logger = logging.getLogger(__name__)

# Создаем асинхронный движок, беря путь из конфига
engine = create_async_engine(config.database_url, echo=False)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных SQLite успешно инициализирована.")