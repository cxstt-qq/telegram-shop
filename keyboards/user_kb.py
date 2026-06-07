from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database.models import Category, Product

def get_language_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🇷🇺 Русский"))
    builder.add(KeyboardButton(text="🇬🇧 English"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def get_main_menu_kb(i18n) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_shop(), callback_data="main_shop"))
    builder.row(
        InlineKeyboardButton(text=i18n.btn_profile(), callback_data="main_profile"),
        InlineKeyboardButton(text=i18n.btn_support(), callback_data="main_support")
    )
    return builder.as_markup()

def get_main_menu_only_kb(i18n) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_main_menu(), callback_data="back_to_main"))
    return builder.as_markup()

def get_categories_kb(categories: list[Category], lang: str, i18n) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        cat_name = category.name_ru if lang == 'ru' else category.name_en
        builder.row(
            InlineKeyboardButton(text=cat_name, callback_data=f"category_{category.id}")
        )
    builder.row(InlineKeyboardButton(text=i18n.btn_main_menu(), callback_data="back_to_main"))
    return builder.as_markup()

def get_products_kb(products_with_counts: list[tuple[Product, int]], lang: str) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура со списком лотов и количеством"""
    builder = InlineKeyboardBuilder()
    for product, count in products_with_counts:
        prod_name = product.title_ru if lang == 'ru' else product.title_en
        unit = "шт." if lang == 'ru' else "pcs."
        
        # Если товара нет, добавляем крестик
        prefix = "❌ " if count == 0 else ""
        
        builder.row(
            InlineKeyboardButton(
                text=f"{prefix}{prod_name} | {count} {unit} | {product.price} $", 
                callback_data=f"product_{product.id}"
            )
        )
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_categories"))
    return builder.as_markup()

def get_buy_product_kb(product_id: int, price: float, count: int, i18n) -> InlineKeyboardMarkup:
    """Кнопка покупки товара (скрывается, если товара нет) и возврата назад"""
    builder = InlineKeyboardBuilder()
    
    # Показываем кнопку Купить, только если товар есть в наличии
    if count > 0:
        builder.row(
            InlineKeyboardButton(text=i18n.btn_buy(price=price), callback_data=f"buy_{product_id}")
        )
        
    builder.row(InlineKeyboardButton(text=i18n.btn_back(), callback_data="back_to_categories"))
    return builder.as_markup()

def get_back_kb(i18n) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_back(), callback_data="back_to_categories"))
    return builder.as_markup()

def get_profile_kb(i18n) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_topup(), callback_data="choose_topup_method")) # Поменяли коллбэк
    builder.row(InlineKeyboardButton(text=i18n.btn_main_menu(), callback_data="back_to_main"))
    return builder.as_markup()

def get_cancel_buy_kb(i18n) -> InlineKeyboardMarkup:
    """Кнопка отмены при вводе количества"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_cancel(), callback_data="cancel_buy"))
    return builder.as_markup()

def get_confirm_buy_kb(product_id: int, quantity: int, i18n) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения покупки"""
    builder = InlineKeyboardBuilder()
    # Зашиваем ID товара и количество прямо в callback_data
    builder.row(
        InlineKeyboardButton(text=i18n.btn_confirm(), callback_data=f"confirmbuy_{product_id}_{quantity}"),
        InlineKeyboardButton(text=i18n.btn_cancel(), callback_data="cancel_buy")
    )
    return builder.as_markup()

def get_topup_methods_kb(i18n) -> InlineKeyboardMarkup:
    """Выбор платежки (С переводом)"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_crypto(), callback_data="topup_cryptobot"))
    builder.row(InlineKeyboardButton(text=i18n.btn_bybit(), callback_data="topup_bybit"))
    builder.row(InlineKeyboardButton(text=i18n.btn_cancel(), callback_data="back_to_main"))
    return builder.as_markup()

def get_invoice_kb(url: str, invoice_id: int, i18n) -> InlineKeyboardMarkup:
    """Клавиатура счета CryptoBot (С переводом)"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_pay(), url=url))
    builder.row(InlineKeyboardButton(text=i18n.btn_check_pay(), callback_data=f"check_inv_{invoice_id}"))
    builder.row(InlineKeyboardButton(text=i18n.btn_cancel(), callback_data="cancel_topup"))
    return builder.as_markup()

def get_bybit_check_kb(user_bybit_uid: str, i18n) -> InlineKeyboardMarkup:
    """Кнопка проверки депозита Bybit (С переводом)"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_check_bybit(), callback_data=f"check_bybit_{user_bybit_uid}"))
    builder.row(InlineKeyboardButton(text=i18n.btn_cancel(), callback_data="back_to_main"))
    return builder.as_markup()

def get_cancel_topup_kb(i18n) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.btn_cancel(), callback_data="cancel_topup"))
    return builder.as_markup()
