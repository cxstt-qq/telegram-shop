from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart

from keyboards.user_kb import get_language_kb, get_main_menu_kb
from database.requests import update_user_language
from middlewares.i18n import create_translator_hub

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, i18n, db_user):
    if not db_user.language_set:
        await message.answer(
            text=i18n.start_welcome(),
            reply_markup=get_language_kb()
        )
    else:
        # Убиваем старые реплай-кнопки, если они зависли
        msg = await message.answer("🔄", reply_markup=ReplyKeyboardRemove())
        await msg.delete()
        
        welcome_text = "🏠 Главное меню" if db_user.language == 'ru' else "🏠 Main Menu"
        await message.answer(
            text=welcome_text,
            reply_markup=get_main_menu_kb(i18n)
        )

@router.message(F.text.in_(["🇷🇺 Русский", "🇬🇧 English"]))
async def process_language_selection(message: Message, db_user):
    selected_lang = 'ru' if "Русский" in message.text else 'en'
    await update_user_language(db_user.telegram_id, selected_lang)
    
    # Трюк: убираем громоздкую клавиатуру с выбором языка
    msg = await message.answer("🔄", reply_markup=ReplyKeyboardRemove())
    await msg.delete()
    
    # Подтягиваем актуальный словарь прямо сейчас
    hub = create_translator_hub()
    new_i18n = hub.get_translator_by_locale(selected_lang)
    
    success_text = "🇷🇺 Язык успешно изменен на Русский!" if selected_lang == 'ru' else "🇬🇧 Language successfully changed to English!"
    await message.answer(
        text=success_text,
        reply_markup=get_main_menu_kb(new_i18n)
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery, i18n, db_user):
    """Обрабатывает кнопку 'В главное меню' из любой части бота"""
    welcome_text = "🏠 Главное меню" if db_user.language == 'ru' else "🏠 Main Menu"
    await callback.message.edit_text(
        text=welcome_text, 
        reply_markup=get_main_menu_kb(i18n)
    )

@router.callback_query(F.data == "main_support")
async def cmd_support(callback: CallbackQuery, i18n):
    """Вывод контактов саппорта с кнопкой возврата"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_main_menu(), callback_data="back_to_main"))
    
    await callback.message.edit_text(
        text=i18n.support_text(),
        reply_markup=builder.as_markup()
    )