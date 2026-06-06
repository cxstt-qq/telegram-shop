from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from filters.is_admin import IsAdmin
from states.admin_states import CategoryStates
from database.requests import add_category, get_categories, delete_category

router = Router()
# Защищаем роутер и для сообщений, и для инлайн-кнопок
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# --- СОЗДАНИЕ КАТЕГОРИИ ---

@router.message(F.text == "📁 Создать категорию")
async def start_add_category(message: Message, state: FSMContext):
    await message.answer("Введите название категории на РУССКОМ языке:")
    await state.set_state(CategoryStates.waiting_for_name_ru)

@router.message(CategoryStates.waiting_for_name_ru, F.text)
async def process_cat_name_ru(message: Message, state: FSMContext):
    await state.update_data(name_ru=message.text)
    await message.answer("Теперь введите название категории на АНГЛИЙСКОМ языке:")
    await state.set_state(CategoryStates.waiting_for_name_en)

@router.message(CategoryStates.waiting_for_name_en, F.text)
async def process_cat_name_en(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Записываем в БД
    await add_category(name_ru=data['name_ru'], name_en=message.text)
    
    await state.clear()
    await message.answer(f"✅ Категория <b>{data['name_ru']}</b> успешно создана!")

# --- УДАЛЕНИЕ КАТЕГОРИИ ---

@router.message(F.text == "🗑 Удалить категорию")
async def start_delete_category(message: Message):
    categories = await get_categories()
    
    if not categories:
        return await message.answer("Категорий пока нет.")
        
    # Генерируем инлайн-кнопки со списком категорий для удаления
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"❌ {cat.name_ru}", 
                callback_data=f"delcat_{cat.id}"
            )
        )
    
    await message.answer(
        "Выберите категорию для удаления (Внимание: удалятся и все товары внутри неё!):", 
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("delcat_"))
async def process_delete_category(callback: CallbackQuery):
    cat_id = int(callback.data.split("_")[1])
    
    # Удаляем из БД
    await delete_category(cat_id)
    
    await callback.message.edit_text("✅ Категория и все связанные с ней товары удалены.")
    await callback.answer()