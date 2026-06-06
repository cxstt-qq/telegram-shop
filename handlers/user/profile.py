from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.user_kb import get_profile_kb

# Добавили новую функцию из БД
from database.requests import get_user_orders_count

router = Router()

@router.callback_query(F.data == "main_profile")
async def show_profile(callback: CallbackQuery, i18n, db_user):
    reg_date_str = db_user.registration_date.strftime("%d.%m.%Y")
    
    # Теперь тут реальная цифра из базы
    orders_count = await get_user_orders_count(db_user.telegram_id)
    
    text = i18n.profile_info(
        user_id=str(db_user.telegram_id),
        balance=db_user.balance,
        reg_date=reg_date_str,
        orders_count=orders_count
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_profile_kb(i18n)
    )