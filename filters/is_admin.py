from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from config_data.config import config

class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user.id in config.admins