import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from filters.is_admin import IsAdmin
from states.admin_states import BroadcastStates, PrivateMsgStates
from database.requests import get_all_users, get_user
from keyboards.admin_kb import get_cancel_kb, get_admin_main_kb

router = Router()
router.message.filter(IsAdmin())

# --- БЛОК 1: МАССОВАЯ РАССЫЛКА ---

@router.message(F.text == "📢 Рассылка")
async def start_broadcast(message: Message, state: FSMContext):
    await message.answer(
        "Перешлите или отправьте мне сообщение для рассылки.\n"
        "<i>Поддерживаются текст, форматирование, картинки, видео и т.д.</i>", 
        reply_markup=get_cancel_kb()
    )
    await state.set_state(BroadcastStates.waiting_for_message)

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    await state.clear()
    
    users = await get_all_users()
    if not users:
        return await message.answer("В базе данных еще нет пользователей.", reply_markup=get_admin_main_kb())
        
    status_msg = await message.answer(f"⏳ Начинаю рассылку для {len(users)} пользователей...")
    
    success_count = 0
    failed_count = 0
    
    for user in users:
        # Не отправляем рассылку самому админу, чтобы он не спамил себе
        if user.telegram_id == message.from_user.id:
            continue
            
        try:
            # Копируем сообщение один в один
            await message.copy_to(chat_id=user.telegram_id)
            success_count += 1
            # Небольшая пауза (микро-слип), чтобы Telegram не выдал лимиты (FloodWait)
            await asyncio.sleep(0.05)
        except TelegramAPIError:
            # Сюда залетают юзеры, блокировавшие бота или удалившие аккаунты
            failed_count += 1
            
    await status_msg.delete()
    await message.answer(
        f"📢 <b>Рассылка завершена!</b>\n\n"
        f"✅ Доставлено: <b>{success_count}</b>\n"
        f"❌ Не доставлено (блок бота): <b>{failed_count}</b>",
        reply_markup=get_admin_main_kb()
    )


# --- БЛОК 2: ЛИЧНОЕ СООБЩЕНИЕ ЮЗЕРУ ---

@router.message(F.text == "✉️ ЛС юзеру")
async def start_private_msg(message: Message, state: FSMContext):
    await message.answer("Введите Telegram ID пользователя, которому хотите написать:", reply_markup=get_cancel_kb())
    await state.set_state(PrivateMsgStates.waiting_for_user_id)

@router.message(PrivateMsgStates.waiting_for_user_id, F.text)
async def process_pm_user_id(message: Message, state: FSMContext):
    clean_id = ''.join(filter(str.isdigit, message.text))
    
    if not clean_id:
        return await message.answer("❌ ID должен содержать цифры. Попробуйте еще раз:")
        
    user_id = int(clean_id)
    user = await get_user(user_id)
    
    if not user:
        return await message.answer("❌ Пользователь не найден в базе данных. Проверьте ID.")
        
    await state.update_data(pm_target_user_id=user_id)
    await message.answer(f"👤 Пользователь найден!\nТеперь отправьте сообщение, которое нужно ему передать:")
    await state.set_state(PrivateMsgStates.waiting_for_message)

@router.message(PrivateMsgStates.waiting_for_message)
async def process_pm_send(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['pm_target_user_id']
    await state.clear()
    
    try:
        # Копируем сообщение юзеру
        await message.copy_to(chat_id=user_id)
        await message.answer(f"✅ Сообщение успешно доставлено пользователю {user_id}!", reply_markup=get_admin_main_kb())
    except TelegramAPIError:
        await message.answer(f"❌ Ошибка! Не удалось доставить сообщение. Пользователь заблокировал бота.", reply_markup=get_admin_main_kb())