from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from filters.is_admin import IsAdmin
from states.admin_states import UserStatsStates
from database.requests import get_detailed_stats, get_user, get_user_orders_count, get_user_orders
from keyboards.admin_kb import get_stats_tabs_kb, get_cancel_kb, get_admin_main_kb, get_user_history_kb

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# --- 1. ОБЩАЯ СТАТИСТИКА МАГАЗИНА ---

async def generate_stats_text(period: str) -> str:
    stats = await get_detailed_stats(period)
    
    period_names = {
        '24h': 'последние 24 часа', 'week': 'последнюю неделю',
        'month': 'последний месяц', 'year': 'последний год', 'all': 'всё время'
    }
    
    text = f"📊 <b>Статистика за {period_names[period]}</b>\n\n"
    text += f"Общих продаж: <b>{stats['total_sales']} шт.</b>\n"
    text += f"Общий оборот: <b>{stats['total_rev']:.2f} $</b>\n\n"
    
    if stats['items']:
        text += "📝 <b>Детализация по товарам:</b>\n"
        for name, count, rev in stats['items']:
            safe_name = name if name else "Неизвестный товар"
            text += f"▪️ {safe_name}: {count} шт. (на {rev:.2f} $)\n"
    else:
        text += "🤷‍♂️ <i>В этот период продаж не было.</i>"
        
    return text

@router.message(F.text == "📊 Магазин")
async def show_statistics(message: Message):
    text = await generate_stats_text('24h')
    await message.answer(text, reply_markup=get_stats_tabs_kb('24h'))

@router.callback_query(F.data.startswith("stats_"))
async def process_stats_tab(callback: CallbackQuery):
    period = callback.data.split("_")[1]
    text = await generate_stats_text(period)
    await callback.message.edit_text(text, reply_markup=get_stats_tabs_kb(period))


# --- 2. СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ ---

@router.message(F.text == "🔍 Юзер")
async def start_user_stats(message: Message, state: FSMContext):
    await message.answer("Введите Telegram ID пользователя:", reply_markup=get_cancel_kb())
    await state.set_state(UserStatsStates.waiting_for_user_id)

@router.message(UserStatsStates.waiting_for_user_id, F.text)
async def process_user_stats_id(message: Message, state: FSMContext):
    # Очищаем ID от юникод-мусора
    clean_id = ''.join(filter(str.isdigit, message.text))
    
    if not clean_id:
        return await message.answer("❌ ID должен содержать цифры.")
        
    user_id = int(clean_id)
    user = await get_user(user_id)
    
    if not user:
        return await message.answer("❌ Пользователь не найден в базе данных.")
        
    orders_count = await get_user_orders_count(user_id)
    reg_date_str = user.registration_date.strftime("%d.%m.%Y %H:%M")
    
    text = (
        f"👤 <b>Статистика пользователя {user_id}</b>\n\n"
        f"💰 Текущий баланс: <b>{user.balance:.2f} $</b>\n"
        f"📅 Дата регистрации: <b>{reg_date_str}</b>\n"
        f"🛒 Всего покупок: <b>{orders_count} шт.</b>\n"
    )
    
    # Возвращаем админ-клавиатуру, но к сообщению цепляем инлайн-кнопку истории
    await state.clear()
    await message.answer(text, reply_markup=get_admin_main_kb())
    
    if orders_count > 0:
        await message.answer("Посмотреть детализацию?", reply_markup=get_user_history_kb(user_id))

@router.callback_query(F.data.startswith("userhist_"))
async def show_user_history(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    orders = await get_user_orders(user_id)
    
    if not orders:
        return await callback.answer("У пользователя нет покупок.", show_alert=True)
        
    # Формируем и бьем сообщение на части, чтобы обойти лимит в 4096 символов
    text = f"📋 <b>История покупок ({user_id}):</b>\n\n"
    
    for order in orders:
        date_str = order.purchase_date.strftime('%d.%m.%Y %H:%M')
        chunk = (
            f"📦 <b>{order.product_name_snapshot}</b>\n"
            f"➖ Списано: {order.purchase_price} $\n"
            f"🕒 {date_str}\n"
            f"🔑 Данные: <code>{order.item_data}</code>\n"
            f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        )
        
        if len(text) + len(chunk) > 4000:
            await callback.message.answer(text)
            text = ""
            
        text += chunk
        
    if text:
        await callback.message.answer(text)
        
    await callback.answer()