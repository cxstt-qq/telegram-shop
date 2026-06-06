from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states.user_states import BuyItemStates
from database.requests import get_categories, get_products_with_counts, get_product_with_count, buy_items, get_admins_for_notifications
from keyboards.user_kb import (
    get_categories_kb, get_products_kb, get_buy_product_kb, 
    get_back_kb, get_cancel_buy_kb, get_confirm_buy_kb, get_main_menu_kb
)

import logging
from aiogram import Bot
from config_data.config import config

router = Router()

# --- НАВИГАЦИЯ ПО МАГАЗИНУ ---

@router.callback_query(F.data == "main_shop")
async def show_shop(callback: CallbackQuery, i18n, db_user):
    """Открывает главное меню магазина со списком категорий"""
    categories = await get_categories()
    
    if not categories:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=i18n.btn_main_menu(), callback_data="back_to_main"))
        return await callback.message.edit_text(i18n.empty_category(), reply_markup=builder.as_markup())

    await callback.message.edit_text(
        text=i18n.shop_desc(),
        reply_markup=get_categories_kb(categories, db_user.language, i18n)
    )

@router.callback_query(F.data.startswith("category_"))
async def show_category_products(callback: CallbackQuery, i18n, db_user):
    """Отображает лоты внутри выбранной категории"""
    category_id = int(callback.data.split("_")[1])
    products_with_counts = await get_products_with_counts(category_id)
    
    if not products_with_counts:
        return await callback.message.edit_text(
            text=i18n.empty_category(),
            reply_markup=get_back_kb(i18n)
        )

    await callback.message.edit_text(
        text=i18n.shop_title(),
        reply_markup=get_products_kb(products_with_counts, db_user.language)
    )

@router.callback_query(F.data.startswith("product_"))
async def show_product_details(callback: CallbackQuery, i18n, db_user):
    """Отображает карточку конкретного товара (описание, цена, наличие)"""
    product_id = int(callback.data.split("_")[1])
    result = await get_product_with_count(product_id)
    
    if not result:
        return await callback.answer(i18n.error_product_not_found(), show_alert=True)
        
    product, count = result
    
    title = product.title_ru if db_user.language == 'ru' else product.title_en
    desc = product.description_ru if db_user.language == 'ru' else product.description_en
    
    stock_label = "В наличии" if db_user.language == 'ru' else "In stock"
    unit = "шт." if db_user.language == 'ru' else "pcs."
    
    text = f"📦 <b>{title}</b>\n\n📝 {desc}\n\n📊 {stock_label}: {count} {unit}\n💰 Цена: {product.price} $"
    
    await callback.message.edit_text(
        text=text,
        reply_markup=get_buy_product_kb(product.id, product.price, count, i18n)
    )

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories_handler(callback: CallbackQuery, i18n, db_user):
    """Кнопка возврата к списку категорий"""
    categories = await get_categories()
    
    if not categories:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=i18n.btn_main_menu(), callback_data="back_to_main"))
        return await callback.message.edit_text(i18n.empty_category(), reply_markup=builder.as_markup())
        
    await callback.message.edit_text(
        text=i18n.shop_desc(),
        reply_markup=get_categories_kb(categories, db_user.language, i18n)
    )


# --- ЦЕПОЧКА ПОКУПКИ С ВЫБОРОМ КОЛИЧЕСТВА ---

@router.callback_query(F.data.startswith("buy_"))
async def process_buy_start(callback: CallbackQuery, state: FSMContext, i18n):
    """Шаг 1: Нажали Купить, просим ввести количество"""
    product_id = int(callback.data.split("_")[1])
    
    result = await get_product_with_count(product_id)
    if not result or result[1] == 0:
        return await callback.answer(i18n.buy_out_of_stock(), show_alert=True)
        
    _, count = result
    
    # Сохраняем ID товара и доступное количество в память FSM
    await state.update_data(buy_product_id=product_id, available_count=count)
    
    await callback.message.edit_text(
        text=i18n.buy_enter_quantity(available=count),
        reply_markup=get_cancel_buy_kb(i18n)
    )
    await state.set_state(BuyItemStates.waiting_for_quantity)


@router.message(BuyItemStates.waiting_for_quantity, F.text)
async def process_buy_quantity(message: Message, state: FSMContext, i18n, db_user):
    """Шаг 2: Юзер ввел число, показываем подытог"""
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.delete()
        return await message.answer(i18n.buy_invalid_quantity())
        
    quantity = int(message.text)
    data = await state.get_data()
    product_id = data['buy_product_id']
    available_count = data['available_count']
    
    await message.delete() # Удаляем цифру из чата
    
    if quantity > available_count:
        return await message.answer(
            i18n.buy_enter_quantity(available=available_count),
            reply_markup=get_cancel_buy_kb(i18n)
        )
        
    # Достаем лот для расчета итогов
    result = await get_product_with_count(product_id)
    if not result:
        await state.clear()
        return await message.answer(i18n.error_product_not_found(), reply_markup=get_main_menu_kb(i18n))
        
    product, _ = result
    title = product.title_ru if db_user.language == 'ru' else product.title_en
    total_price = round(product.price * quantity, 2)
    
    # Скидываем стейт, так как дальше всё идет через инлайн-кнопки
    await state.clear()
    
    # Отправляем сообщение с подытогом
    await message.answer(
        text=i18n.buy_confirm(
            title=title, 
            quantity=quantity, 
            price=product.price, 
            total_price=total_price
        ),
        reply_markup=get_confirm_buy_kb(product_id, quantity, i18n)
    )


@router.callback_query(F.data.startswith("confirmbuy_"))
async def process_buy_confirm(callback: CallbackQuery, i18n, db_user, bot: Bot):
    """Шаг 3: Юзер нажал Подтвердить"""
    _, product_id, quantity = callback.data.split("_")
    product_id, quantity = int(product_id), int(quantity)
    
    result = await buy_items(db_user.telegram_id, product_id, quantity)
    logger = logging.getLogger(__name__) # Инициализируем логгер
    
    if result['status'] == 'no_stock':
        await callback.message.edit_text(i18n.buy_out_of_stock())
    elif result['status'] == 'no_balance':
        await callback.message.edit_text(i18n.buy_no_balance())
    elif result['status'] == 'success':
        # 1. Выводим в лог-файл
        logger.info(f"ПОКУПКА: Юзер {db_user.telegram_id} купил лот #{product_id} (Кол-во: {quantity})")
        
        # 2. Отправляем уведомления админам
        admins_to_notify = await get_admins_for_notifications(config.admins)
        for adm_id in admins_to_notify:
            try:
                await bot.send_message(
                    chat_id=adm_id, 
                    text=f"🛒 <b>Новая покупка!</b>\nПользователь: <code>{db_user.telegram_id}</code>\nТовар ID: {product_id}\nКоличество: {quantity} шт."
                )
            except Exception:
                pass # Если админ заблочил бота, игнорируем
                
        # 3. Выдаем товар пользователю
        await callback.message.edit_text(text=i18n.buy_success(item_data=result['item_data']))
    else:
        await callback.message.edit_text(i18n.error_buy_failed())

@router.callback_query(F.data == "cancel_buy")
async def process_buy_cancel(callback: CallbackQuery, state: FSMContext, i18n):
    """Кнопка отмены на любом этапе покупки"""
    await state.clear()
    await callback.message.edit_text(
        text=i18n.buy_cancelled(),
        reply_markup=get_main_menu_kb(i18n)
    )