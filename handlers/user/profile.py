from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.user_kb import get_profile_kb

# Добавили новую функцию из БД
from database.requests import get_referral_percent, get_referral_stats, get_user_orders_count

router = Router()

@router.callback_query(F.data == "main_profile")
async def show_profile(callback: CallbackQuery, i18n, db_user):
    reg_date_str = db_user.registration_date.strftime("%d.%m.%Y")
    
    # Теперь тут реальная цифра из базы
    orders_count = await get_user_orders_count(db_user.telegram_id)
    referral_percent = await get_referral_percent()
    referral_stats = await get_referral_stats(db_user.telegram_id)
    bot_info = await callback.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{db_user.telegram_id}"
    
    text = i18n.profile_info(
        user_id=str(db_user.telegram_id),
        balance=db_user.balance,
        reg_date=reg_date_str,
        orders_count=orders_count
    )
    text += "\n\n" + i18n.profile_referral_info(
        referral_link=referral_link,
        referrals_count=referral_stats['referrals_count'],
        referral_earned=round(referral_stats['referral_earned'], 2),
        referral_percent=round(referral_percent, 2)
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_profile_kb(i18n)
    )
