from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from filters.is_admin import IsAdmin
from database.requests import get_admin_notifications_status, toggle_admin_notifications
from keyboards.admin_kb import get_notifications_kb

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

@router.message(F.text == "⚙️ Настройки уведомлений")
async def show_notif_settings(message: Message):
    is_enabled = await get_admin_notifications_status(message.from_user.id)
    status_text = "ВКЛЮЧЕНЫ ✅" if is_enabled else "ВЫКЛЮЧЕНЫ ❌"
    
    await message.answer(
        f"Уведомления о покупках и пополнениях:\n<b>{status_text}</b>", 
        reply_markup=get_notifications_kb(is_enabled)
    )

@router.callback_query(F.data == "toggle_notif")
async def process_toggle_notif(callback: CallbackQuery):
    new_status = await toggle_admin_notifications(callback.from_user.id)
    status_text = "ВКЛЮЧЕНЫ ✅" if new_status else "ВЫКЛЮЧЕНЫ ❌"
    
    await callback.message.edit_text(
        f"Уведомления о покупках и пополнениях:\n<b>{status_text}</b>", 
        reply_markup=get_notifications_kb(new_status)
    )