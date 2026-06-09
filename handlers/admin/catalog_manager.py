from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.requests import (
    add_category,
    add_product,
    delete_category,
    delete_product,
    extract_items_from_product,
    get_all_products_with_counts,
    get_categories,
    get_category_by_id,
    get_product_with_count,
    update_category_field,
    update_product_field,
)
from filters.is_admin import IsAdmin
from keyboards.admin_kb import get_cancel_kb
from states.admin_states import CatalogManageStates, ItemStates

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

PRODUCT_FIELDS = {
    "title_ru": ("Название RU", str),
    "title_en": ("Название EN", str),
    "description_ru": ("Описание RU", str),
    "description_en": ("Описание EN", str),
    "price": ("Цена", float),
}
CARD_TEXT_LIMIT = 900

CATEGORY_FIELDS = {
    "name_ru": "Название RU",
    "name_en": "Название EN",
}

@router.message(F.text == "🧰 Лоты и категории")
async def open_catalog_manager(message: Message):
    await message.answer(
        "🧰 <b>Управление магазином</b>\nВыберите раздел:",
        reply_markup=_manager_home_kb()
    )

@router.callback_query(F.data == "cm_home")
async def back_to_manager_home(callback: CallbackQuery):
    await callback.message.edit_text(
        "🧰 <b>Управление магазином</b>\nВыберите раздел:",
        reply_markup=_manager_home_kb()
    )

@router.callback_query(F.data == "cm_products")
async def show_products_manager(callback: CallbackQuery):
    products = await get_all_products_with_counts()
    await callback.message.edit_text(
        _products_list_text(products),
        reply_markup=_products_list_kb(products)
    )

@router.callback_query(F.data == "cm_pcreate")
async def start_product_create(callback: CallbackQuery):
    categories = await get_categories()
    if not categories:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="➕ Создать категорию", callback_data="cm_ccreate"))
        builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="cm_products"))
        await callback.message.edit_text(
            "❌ Сначала создайте хотя бы одну категорию.",
            reply_markup=builder.as_markup()
        )
        return

    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.row(InlineKeyboardButton(
            text=f"#{category.id} {category.name_ru}",
            callback_data=f"cm_pcreate_cat:{category.id}"
        ))
    builder.row(InlineKeyboardButton(text="↩️ К лотам", callback_data="cm_products"))
    await callback.message.edit_text(
        "➕ <b>Создание лота</b>\nВыберите категорию:",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("cm_pcreate_cat:"))
async def process_product_create_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(":")[1])
    category = await get_category_by_id(category_id)
    if not category:
        return await callback.answer("Категория не найдена.", show_alert=True)

    await state.update_data(new_product_category_id=category_id)
    await callback.message.answer("Введите название лота на РУССКОМ языке:", reply_markup=get_cancel_kb())
    await state.set_state(CatalogManageStates.waiting_for_new_product_title_ru)
    await callback.answer()

@router.message(CatalogManageStates.waiting_for_new_product_title_ru, F.text)
async def process_new_product_title_ru(message: Message, state: FSMContext):
    await state.update_data(new_product_title_ru=message.text.strip())
    await message.answer("Введите название лота на АНГЛИЙСКОМ языке:")
    await state.set_state(CatalogManageStates.waiting_for_new_product_title_en)

@router.message(CatalogManageStates.waiting_for_new_product_title_en, F.text)
async def process_new_product_title_en(message: Message, state: FSMContext):
    await state.update_data(new_product_title_en=message.text.strip())
    await message.answer("Введите описание лота на РУССКОМ языке:")
    await state.set_state(CatalogManageStates.waiting_for_new_product_desc_ru)

@router.message(CatalogManageStates.waiting_for_new_product_desc_ru, F.text)
async def process_new_product_desc_ru(message: Message, state: FSMContext):
    await state.update_data(new_product_desc_ru=message.text.strip())
    await message.answer("Введите описание лота на АНГЛИЙСКОМ языке:")
    await state.set_state(CatalogManageStates.waiting_for_new_product_desc_en)

@router.message(CatalogManageStates.waiting_for_new_product_desc_en, F.text)
async def process_new_product_desc_en(message: Message, state: FSMContext):
    await state.update_data(new_product_desc_en=message.text.strip())
    await message.answer("Введите цену лота в USD. Например: <code>2.5</code>")
    await state.set_state(CatalogManageStates.waiting_for_new_product_price)

@router.message(CatalogManageStates.waiting_for_new_product_price, F.text)
async def process_new_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        return await message.answer("Цена должна быть числом. Например: <code>2.5</code>")

    if price <= 0:
        return await message.answer("Цена должна быть больше нуля.")

    data = await state.get_data()
    await add_product(
        category_id=data["new_product_category_id"],
        title_ru=data["new_product_title_ru"],
        title_en=data["new_product_title_en"],
        desc_ru=data["new_product_desc_ru"],
        desc_en=data["new_product_desc_en"],
        price=price,
    )
    await state.clear()

    products = await get_all_products_with_counts()
    await message.answer(
        f"✅ Лот <b>{escape(data['new_product_title_ru'])}</b> создан.\n\n" + _products_list_text(products),
        reply_markup=_products_list_kb(products)
    )

@router.callback_query(F.data.startswith("cm_product:"))
async def show_product_card(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await _edit_product_card(callback, product_id)

async def _edit_product_card(callback: CallbackQuery, product_id: int):
    product_result = await get_product_with_count(product_id)
    if not product_result:
        return await callback.answer("Лот не найден.", show_alert=True)

    await callback.message.edit_text(
        _product_card_text(*product_result),
        reply_markup=_product_card_kb(product_id)
    )

@router.callback_query(F.data.startswith("cm_pedit:"))
async def start_product_edit(callback: CallbackQuery, state: FSMContext):
    _, field, product_id_raw = callback.data.split(":")
    product_id = int(product_id_raw)

    if field not in PRODUCT_FIELDS:
        return await callback.answer("Неизвестное поле.", show_alert=True)

    product_result = await get_product_with_count(product_id)
    if not product_result:
        return await callback.answer("Лот не найден.", show_alert=True)

    field_label, _ = PRODUCT_FIELDS[field]
    await state.update_data(product_id=product_id, product_field=field)
    await callback.message.answer(
        f"✏️ Введите новое значение для поля <b>{field_label}</b>:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(CatalogManageStates.waiting_for_product_value)
    await callback.answer()

@router.message(CatalogManageStates.waiting_for_product_value, F.text)
async def process_product_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]
    field = data["product_field"]
    field_label, caster = PRODUCT_FIELDS[field]

    try:
        value = caster(message.text.replace(",", ".")) if caster is float else message.text.strip()
    except ValueError:
        return await message.answer("Цена должна быть числом. Например: <code>2.5</code>")

    if value == "":
        return await message.answer("Значение не может быть пустым.")

    if field == "price" and value <= 0:
        return await message.answer("Цена должна быть больше нуля.")

    await update_product_field(product_id, field, value)
    await state.clear()

    product_result = await get_product_with_count(product_id)
    if not product_result:
        return await message.answer("✅ Поле обновлено, но лот больше не найден.")

    text = f"✅ Поле <b>{escape(field_label)}</b> обновлено.\n\n" + _product_card_text(*product_result)
    await message.answer(text, reply_markup=_product_card_kb(product_id))

@router.callback_query(F.data.startswith("cm_extract:"))
async def start_extract_items(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    product_result = await get_product_with_count(product_id)
    if not product_result:
        return await callback.answer("Лот не найден.", show_alert=True)

    _, count = product_result
    if count <= 0:
        return await callback.answer("В этом лоте нет товаров в наличии.", show_alert=True)

    await state.update_data(extract_product_id=product_id, extract_available=count)
    await callback.message.answer(
        f"📤 Сколько товаров выгрузить и убрать из наличия?\nДоступно: <b>{count}</b>",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(CatalogManageStates.waiting_for_extract_quantity)
    await callback.answer()

@router.callback_query(F.data.startswith("cm_upload:"))
async def start_upload_items_from_card(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    product_result = await get_product_with_count(product_id)
    if not product_result:
        return await callback.answer("Лот не найден.", show_alert=True)

    product, _ = product_result
    await state.update_data(product_id=product_id, return_to_catalog_product_id=product_id)
    await callback.message.answer(
        f"📥 <b>Загрузка товаров в лот #{product_id}</b>\n"
        f"Лот: <b>{escape(product.title_ru)}</b>\n\n"
        "Отправьте список товаров текстом или .txt файлом.\n"
        "<b>Каждая новая строка = один отдельный товар.</b>",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(ItemStates.waiting_for_items_data)
    await callback.answer()

@router.message(CatalogManageStates.waiting_for_extract_quantity, F.text)
async def process_extract_items(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        return await message.answer("Введите целое число больше нуля.")

    quantity = int(message.text)
    data = await state.get_data()
    product_id = data["extract_product_id"]
    available = data["extract_available"]

    if quantity > available:
        return await message.answer(f"В наличии только <b>{available}</b>. Введите меньшее число.")

    result = await extract_items_from_product(product_id, quantity)
    if result["status"] == "not_enough":
        await state.clear()
        return await message.answer(f"Не удалось выгрузить: сейчас в наличии только <b>{result['available']}</b>.")

    if result["status"] != "success":
        await state.clear()
        return await message.answer("Не удалось выгрузить товары: лот пуст или не найден.")

    await state.clear()
    file = BufferedInputFile(
        "\n".join(result["items"]).encode("utf-8"),
        filename=f"items_lot_{product_id}_{len(result['items'])}.txt"
    )
    await message.answer_document(
        document=file,
        caption=(
            f"✅ Выгружено и удалено из наличия: <b>{len(result['items'])}</b>\n"
            f"Лот: <b>{escape(result['product_title'])}</b> #{product_id}"
        )
    )

    product_result = await get_product_with_count(product_id)
    if product_result:
        await message.answer(_product_card_text(*product_result), reply_markup=_product_card_kb(product_id))

@router.callback_query(F.data.startswith("cm_pdel:"))
async def confirm_delete_product(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product_result = await get_product_with_count(product_id)
    if not product_result:
        return await callback.answer("Лот не найден.", show_alert=True)

    product, count = product_result
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"cm_pdel_ok:{product_id}"))
    builder.row(InlineKeyboardButton(text="↩️ Назад к лоту", callback_data=f"cm_product:{product_id}"))
    await callback.message.edit_text(
        f"⚠️ Удалить лот <b>{escape(product.title_ru)}</b> и все товары внутри?\nОстаток: <b>{count}</b>",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("cm_pdel_ok:"))
async def delete_product_from_manager(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await delete_product(product_id)
    products = await get_all_products_with_counts()
    await callback.message.edit_text(
        "✅ Лот удалён.\n\n" + _products_list_text(products),
        reply_markup=_products_list_kb(products)
    )

@router.callback_query(F.data == "cm_categories")
async def show_categories_manager(callback: CallbackQuery):
    categories = await get_categories()
    await callback.message.edit_text(
        _categories_list_text(categories),
        reply_markup=_categories_list_kb(categories)
    )

@router.callback_query(F.data == "cm_ccreate")
async def start_category_create(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "➕ <b>Создание категории</b>\nВведите название категории на РУССКОМ языке:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(CatalogManageStates.waiting_for_new_category_name_ru)
    await callback.answer()

@router.message(CatalogManageStates.waiting_for_new_category_name_ru, F.text)
async def process_new_category_name_ru(message: Message, state: FSMContext):
    name_ru = message.text.strip()
    if not name_ru:
        return await message.answer("Название не может быть пустым.")

    await state.update_data(new_category_name_ru=name_ru)
    await message.answer("Введите название категории на АНГЛИЙСКОМ языке:")
    await state.set_state(CatalogManageStates.waiting_for_new_category_name_en)

@router.message(CatalogManageStates.waiting_for_new_category_name_en, F.text)
async def process_new_category_name_en(message: Message, state: FSMContext):
    name_en = message.text.strip()
    if not name_en:
        return await message.answer("Название не может быть пустым.")

    data = await state.get_data()
    await add_category(name_ru=data["new_category_name_ru"], name_en=name_en)
    await state.clear()

    categories = await get_categories()
    await message.answer(
        f"✅ Категория <b>{escape(data['new_category_name_ru'])}</b> создана.\n\n" + _categories_list_text(categories),
        reply_markup=_categories_list_kb(categories)
    )

@router.callback_query(F.data.startswith("cm_category:"))
async def show_category_card(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    category = await get_category_by_id(category_id)
    if not category:
        return await callback.answer("Категория не найдена.", show_alert=True)

    await callback.message.edit_text(
        _category_card_text(category),
        reply_markup=_category_card_kb(category.id)
    )

@router.callback_query(F.data.startswith("cm_cedit:"))
async def start_category_edit(callback: CallbackQuery, state: FSMContext):
    _, field, category_id_raw = callback.data.split(":")
    category_id = int(category_id_raw)

    if field not in CATEGORY_FIELDS:
        return await callback.answer("Неизвестное поле.", show_alert=True)

    category = await get_category_by_id(category_id)
    if not category:
        return await callback.answer("Категория не найдена.", show_alert=True)

    await state.update_data(category_id=category_id, category_field=field)
    await callback.message.answer(
        f"✏️ Введите новое значение для поля <b>{CATEGORY_FIELDS[field]}</b>:",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(CatalogManageStates.waiting_for_category_value)
    await callback.answer()

@router.message(CatalogManageStates.waiting_for_category_value, F.text)
async def process_category_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    value = message.text.strip()
    if not value:
        return await message.answer("Значение не может быть пустым.")

    await update_category_field(data["category_id"], data["category_field"], value)
    await state.clear()

    category = await get_category_by_id(data["category_id"])
    if not category:
        return await message.answer("✅ Категория обновлена, но больше не найдена.")

    await message.answer(
        "✅ Категория обновлена.\n\n" + _category_card_text(category),
        reply_markup=_category_card_kb(category.id)
    )

@router.callback_query(F.data.startswith("cm_cdel:"))
async def confirm_delete_category(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    category = await get_category_by_id(category_id)
    if not category:
        return await callback.answer("Категория не найдена.", show_alert=True)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"cm_cdel_ok:{category_id}"))
    builder.row(InlineKeyboardButton(text="↩️ Назад к категории", callback_data=f"cm_category:{category_id}"))
    await callback.message.edit_text(
        f"⚠️ Удалить категорию <b>{escape(category.name_ru)}</b> и все лоты внутри?",
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("cm_cdel_ok:"))
async def delete_category_from_manager(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    await delete_category(category_id)
    categories = await get_categories()
    await callback.message.edit_text(
        "✅ Категория удалена.\n\n" + _categories_list_text(categories),
        reply_markup=_categories_list_kb(categories)
    )

def _manager_home_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📦 Лоты", callback_data="cm_products"))
    builder.row(InlineKeyboardButton(text="📁 Категории", callback_data="cm_categories"))
    return builder.as_markup()

def _products_list_text(products_with_counts) -> str:
    if not products_with_counts:
        return "📦 <b>Лоты</b>\n\nЛотов пока нет."
    return "📦 <b>Лоты</b>\n\nВыберите лот для управления:"

def _products_list_kb(products_with_counts):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Создать лот", callback_data="cm_pcreate"))
    for product, count in products_with_counts:
        builder.row(InlineKeyboardButton(
            text=f"#{product.id} {product.title_ru} | {count} шт. | {product.price} $",
            callback_data=f"cm_product:{product.id}"
        ))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="cm_home"))
    return builder.as_markup()

def _product_card_text(product, count: int) -> str:
    return (
        f"📦 <b>Лот #{product.id}</b>\n"
        f"Категория ID: <b>{product.category_id}</b>\n"
        f"Остаток: <b>{count}</b> шт.\n"
        f"Цена: <b>{product.price} $</b>\n\n"
        f"<b>Название RU:</b> {escape(product.title_ru)}\n"
        f"<b>Название EN:</b> {escape(product.title_en)}\n\n"
        f"<b>Описание RU:</b>\n{_short_text(product.description_ru)}\n\n"
        f"<b>Описание EN:</b>\n{_short_text(product.description_en)}"
    )

def _product_card_kb(product_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Название RU", callback_data=f"cm_pedit:title_ru:{product_id}"),
        InlineKeyboardButton(text="✏️ Название EN", callback_data=f"cm_pedit:title_en:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Описание RU", callback_data=f"cm_pedit:description_ru:{product_id}"),
        InlineKeyboardButton(text="📝 Описание EN", callback_data=f"cm_pedit:description_en:{product_id}")
    )
    builder.row(InlineKeyboardButton(text="💵 Цена", callback_data=f"cm_pedit:price:{product_id}"))
    builder.row(InlineKeyboardButton(text="📥 Загрузить товары", callback_data=f"cm_upload:{product_id}"))
    builder.row(InlineKeyboardButton(text="📤 Скачать и убрать товары", callback_data=f"cm_extract:{product_id}"))
    builder.row(InlineKeyboardButton(text="🗑 Удалить лот", callback_data=f"cm_pdel:{product_id}"))
    builder.row(InlineKeyboardButton(text="↩️ К лотам", callback_data="cm_products"))
    return builder.as_markup()

def _categories_list_text(categories) -> str:
    if not categories:
        return "📁 <b>Категории</b>\n\nКатегорий пока нет."
    return "📁 <b>Категории</b>\n\nВыберите категорию для управления:"

def _categories_list_kb(categories):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➕ Создать категорию", callback_data="cm_ccreate"))
    for category in categories:
        builder.row(InlineKeyboardButton(
            text=f"#{category.id} {category.name_ru} / {category.name_en}",
            callback_data=f"cm_category:{category.id}"
        ))
    builder.row(InlineKeyboardButton(text="↩️ Назад", callback_data="cm_home"))
    return builder.as_markup()

def _category_card_text(category) -> str:
    return (
        f"📁 <b>Категория #{category.id}</b>\n\n"
        f"<b>Название RU:</b> {escape(category.name_ru)}\n"
        f"<b>Название EN:</b> {escape(category.name_en)}"
    )

def _category_card_kb(category_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Название RU", callback_data=f"cm_cedit:name_ru:{category_id}"),
        InlineKeyboardButton(text="✏️ Название EN", callback_data=f"cm_cedit:name_en:{category_id}")
    )
    builder.row(InlineKeyboardButton(text="🗑 Удалить категорию", callback_data=f"cm_cdel:{category_id}"))
    builder.row(InlineKeyboardButton(text="↩️ К категориям", callback_data="cm_categories"))
    return builder.as_markup()

def _short_text(text: str) -> str:
    escaped = escape(text)
    if len(escaped) <= CARD_TEXT_LIMIT:
        return escaped
    return escaped[:CARD_TEXT_LIMIT] + "\n…"
