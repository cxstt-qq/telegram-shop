from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from filters.is_admin import IsAdmin
from keyboards.admin_kb import get_admin_main_kb

router = Router()
router.message.filter(IsAdmin())

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(
        "🛠 <b>Админ-панель открыта.</b> Выберите действие:", 
        reply_markup=get_admin_main_kb()
    )