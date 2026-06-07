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
    import database.models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _run_sqlite_migrations(conn)
    logger.info("Database initialized.")

async def _run_sqlite_migrations(conn):
    """Adds lightweight SQLite columns that create_all cannot add to existing tables."""
    if not config.database_url.startswith("sqlite"):
        return

    result = await conn.exec_driver_sql("PRAGMA table_info(users)")
    user_columns = {row[1] for row in result.fetchall()}

    if "referred_by" not in user_columns:
        await conn.exec_driver_sql("ALTER TABLE users ADD COLUMN referred_by BIGINT")

    if "referral_earned" not in user_columns:
        await conn.exec_driver_sql("ALTER TABLE users ADD COLUMN referral_earned FLOAT DEFAULT 0.0")
