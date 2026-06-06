from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config_data.config import config
from keyboards.admin_kb import get_admin_main_kb

router = Router()

@router.message(Command("cancel"))
@router.message(F.text.lower().in_(["отмена", "cancel", "❌ отмена"]))
async def cancel_handler(message: Message, state: FSMContext):
    """Сбрасывает текущее состояние машины состояний (FSM)"""
    current_state = await state.get_state()
    if current_state is None:
        return 

    await state.clear()
    
    # Если это админ — возвращаем ему меню админки. Если обычный юзер — просто убираем кнопку
    if message.from_user.id in config.admins:
        await message.answer("🚫 Ввод данных прерван. Возврат в меню.", reply_markup=get_admin_main_kb())
    else:
        await message.answer("🚫 Действие отменено.", reply_markup=ReplyKeyboardRemove())