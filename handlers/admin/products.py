from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from filters.is_admin import IsAdmin
from states.admin_states import ProductStates, ItemStates
from database.requests import add_product, add_items_bulk, get_categories, get_all_products, delete_product
from keyboards.admin_kb import get_cancel_kb, get_admin_main_kb

router = Router()
# Защищаем роутер и для сообщений, и для инлайн-кнопок админки
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# --- СОЗДАНИЕ ЛОТА ---

@router.message(F.text == "📦 Создать лот")
async def start_create_product(message: Message, state: FSMContext):
    categories = await get_categories()
    if not categories:
        return await message.answer("❌ Сначала создайте хотя бы одну категорию!", reply_markup=get_admin_main_kb())
        
    cats_text = "\n".join([f"ID <b>{c.id}</b>: {c.name_ru}" for c in categories])
    
    await message.answer(
        f"Выберите категорию для лота и отправьте её <b>ID</b>:\n\n{cats_text}",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(ProductStates.waiting_for_category)

@router.message(ProductStates.waiting_for_category, F.text)
async def process_prod_category(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом.")
        
    await state.update_data(category_id=int(message.text))
    await message.answer("Введите название лота на РУССКОМ языке:")
    await state.set_state(ProductStates.waiting_for_title_ru)

@router.message(ProductStates.waiting_for_title_ru, F.text)
async def process_prod_title_ru(message: Message, state: FSMContext):
    await state.update_data(title_ru=message.text)
    await message.answer("Введите название лота на АНГЛИЙСКОМ языке:")
    await state.set_state(ProductStates.waiting_for_title_en)

@router.message(ProductStates.waiting_for_title_en, F.text)
async def process_prod_title_en(message: Message, state: FSMContext):
    await state.update_data(title_en=message.text)
    await message.answer("Введите описание лота на РУССКОМ языке:")
    await state.set_state(ProductStates.waiting_for_desc_ru)

@router.message(ProductStates.waiting_for_desc_ru, F.text)
async def process_prod_desc_ru(message: Message, state: FSMContext):
    await state.update_data(desc_ru=message.text)
    await message.answer("Введите описание лота на АНГЛИЙСКОМ языке:")
    await state.set_state(ProductStates.waiting_for_desc_en)

@router.message(ProductStates.waiting_for_desc_en, F.text)
async def process_prod_desc_en(message: Message, state: FSMContext):
    await state.update_data(desc_en=message.text)
    await message.answer("Введите цену лота (в USD, например 2.5):")
    await state.set_state(ProductStates.waiting_for_price)

@router.message(ProductStates.waiting_for_price, F.text)
async def process_prod_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        return await message.answer("Цена должна быть числом (например, 150 или 150.5).")
        
    data = await state.get_data()
    
    await add_product(
        category_id=data['category_id'],
        title_ru=data['title_ru'],
        title_en=data['title_en'],
        desc_ru=data['desc_ru'],
        desc_en=data['desc_en'],
        price=price
    )
    
    await state.clear()
    await message.answer(
        f"✅ Лот <b>{data['title_ru']}</b> успешно создан!", 
        reply_markup=get_admin_main_kb()
    )


# --- УДАЛЕНИЕ ЛОТА ---

@router.message(F.text == "🗑 Удалить лот")
async def start_delete_product(message: Message):
    products = await get_all_products()
    
    if not products:
        return await message.answer("Лотов пока нет.")
        
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.row(
            InlineKeyboardButton(
                text=f"❌ {p.title_ru} ({p.price} $)", 
                callback_data=f"delprod_{p.id}"
            )
        )
    
    await message.answer(
        "Выберите лот для удаления (Внимание: удалятся и все загруженные в него аккаунты!):", 
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("delprod_"))
async def process_delete_product(callback: CallbackQuery):
    prod_id = int(callback.data.split("_")[1])
    
    await delete_product(prod_id)
    
    await callback.message.edit_text("✅ Лот и все загруженные в него аккаунты успешно удалены.")
    await callback.answer()


# --- МАССОВЫЙ ЗАЛИВ АККАУНТОВ ---

@router.message(F.text == "📥 Залить аккаунты")
async def start_bulk_upload(message: Message, state: FSMContext):
    products = await get_all_products()
    
    if not products:
        return await message.answer("❌ Нет ни одного созданного лота!", reply_markup=get_admin_main_kb())
        
    products_text = "\n".join([f"ID <b>{p.id}</b>: {p.title_ru} ({p.price} $)" for p in products])
    
    await message.answer(
        f"Доступные лоты:\n\n{products_text}\n\n"
        "Введите <b>ID лота</b>, в который будем заливать товар:", 
        reply_markup=get_cancel_kb()
    )
    await state.set_state(ItemStates.waiting_for_product_id)

@router.message(ItemStates.waiting_for_product_id, F.text)
async def process_product_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("ID должен быть числом. Попробуйте еще раз:")
        
    await state.update_data(product_id=int(message.text))
    await message.answer(
        "Отлично! Теперь отправьте мне список аккаунтов.\n"
        "<b>Каждая новая строка = один отдельный товар.</b>\n"
        "<i>Пример:</i>\nlog1:pass1\nlog2:pass2"
    )
    await state.set_state(ItemStates.waiting_for_items_data)

@router.message(ItemStates.waiting_for_items_data, F.text)
async def process_bulk_data(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    
    accounts_list = [line.strip() for line in message.text.split('\n') if line.strip()]
    
    if not accounts_list:
        return await message.answer("Вы прислали пустой список. Попробуйте снова.")
        
    await add_items_bulk(product_id=product_id, data_list=accounts_list)
    
    await state.clear()
    await message.answer(
        f"✅ Успешно загружено <b>{len(accounts_list)}</b> аккаунтов в лот #{product_id}!",
        reply_markup=get_admin_main_kb()
    )