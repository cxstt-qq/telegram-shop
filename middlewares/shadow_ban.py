from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

class ShadowBanMiddleware(BaseMiddleware):
    """
    Мидлварь для теневой блокировки пользователей.
    Бот просто будет игнорировать все их сообщения и нажатия кнопок.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        # Достаем юзера, которого уже выгрузила предыдущая мидлварь (L10nMiddleware)
        db_user = data.get("db_user")
        
        if db_user:
            # Заглушка: если у юзера статус "забанен", прерываем обработку
            # if getattr(db_user, 'is_banned', False):
            #     return
            pass
            
        return await handler(event, data)