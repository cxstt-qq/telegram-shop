from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from filters.is_admin import IsAdmin
from states.admin_states import UserManStates
from database.db import async_session_maker
from database.requests import get_user
from keyboards.admin_kb import get_cancel_kb, get_admin_main_kb

router = Router()
router.message.filter(IsAdmin())

@router.message(F.text == "💰 Выдать баланс")
async def start_give_balance(message: Message, state: FSMContext):
    # Добавили клавиатуру отмены
    await message.answer("Введите Telegram ID пользователя:", reply_markup=get_cancel_kb())
    await state.set_state(UserManStates.waiting_for_user_id)

@router.message(UserManStates.waiting_for_user_id, F.text)
async def process_user_id(message: Message, state: FSMContext):
    # Жестко фильтруем строку, оставляя ТОЛЬКО цифры
    clean_id = ''.join(filter(str.isdigit, message.text))
    
    if not clean_id:
        return await message.answer("❌ ID должен содержать цифры. Попробуйте еще раз:")
        
    user_id = int(clean_id)
    user = await get_user(user_id)
    
    if not user:
        return await message.answer("❌ Пользователь не найден в базе данных. Проверьте ID.")
        
    await state.update_data(target_user_id=user_id)
    await message.answer(
        f"👤 Пользователь найден! Текущий баланс: <b>{user.balance} $</b>\n"
        "Введите сумму для пополнения в USD (можно использовать минус для списания):"
    )
    await state.set_state(UserManStates.waiting_for_balance_amount)

@router.message(UserManStates.waiting_for_balance_amount, F.text)
async def process_balance_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        return await message.answer("Сумма должна быть числом (например, 10 или 5.5).")
        
    data = await state.get_data()
    target_user_id = data['target_user_id']
    
    async with async_session_maker() as session:
        from database.models import User
        user = await session.get(User, target_user_id)
        
        if user:
            user.balance += amount
            await session.commit()
            # Поменяли на $
            await message.answer(
                f"✅ Баланс пользователя {target_user_id} изменен на {amount} $. Текущий баланс: {user.balance} $",
                reply_markup=get_admin_main_kb()
            )
    
    await state.clear()