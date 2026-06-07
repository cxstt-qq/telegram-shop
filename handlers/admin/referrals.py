from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.requests import get_referral_percent, set_referral_percent
from filters.is_admin import IsAdmin
from keyboards.admin_kb import get_admin_main_kb, get_cancel_kb
from states.admin_states import ReferralSettingsStates

router = Router()
router.message.filter(IsAdmin())

@router.message(F.text == "🤝 Реферальный процент")
async def show_referral_settings(message: Message, state: FSMContext):
    percent = await get_referral_percent()
    await message.answer(
        f"<b>Текущий реферальный процент:</b> {percent}%\n\n"
        "Введите новый процент от 0 до 100. Например: <code>7.5</code>",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(ReferralSettingsStates.waiting_for_percent)

@router.message(ReferralSettingsStates.waiting_for_percent, F.text)
async def process_referral_percent(message: Message, state: FSMContext):
    raw_percent = message.text.replace(",", ".").strip()

    try:
        percent = float(raw_percent)
    except ValueError:
        return await message.answer("Процент должен быть числом. Например: <code>7.5</code>")

    if percent < 0 or percent > 100:
        return await message.answer("Процент должен быть от 0 до 100.")

    percent = round(percent, 2)
    await set_referral_percent(percent)
    await state.clear()
    await message.answer(
        f"Реферальный процент обновлён: <b>{percent}%</b>.\n"
        "Новое значение применяется ко всем приглашённым пользователям.",
        reply_markup=get_admin_main_kb()
    )
