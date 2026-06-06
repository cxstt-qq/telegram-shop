from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_main_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📁 Создать категорию"), KeyboardButton(text="🗑 Удалить категорию")],
        [KeyboardButton(text="📦 Создать лот"), KeyboardButton(text="🗑 Удалить лот")],
        [KeyboardButton(text="📥 Залить аккаунты"), KeyboardButton(text="💰 Выдать баланс")],
        [KeyboardButton(text="📊 Магазин"), KeyboardButton(text="🔍 Юзер")],
        [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="✉️ ЛС юзеру")],
        [KeyboardButton(text="⚙️ Настройки уведомлений")] # Новая кнопка
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_cancel_kb() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_stats_tabs_kb(current_tab: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tabs = {
        '24h': '24 часа', 'week': 'Неделя', 'month': 'Месяц', 'year': 'Год', 'all': 'Всё время'
    }
    buttons = []
    for key, label in tabs.items():
        text = f"🔘 {label}" if key == current_tab else label
        buttons.append(InlineKeyboardButton(text=text, callback_data=f"stats_{key}"))
    
    builder.row(*buttons[:3])
    builder.row(*buttons[3:])
    return builder.as_markup()

def get_user_history_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 История покупок", callback_data=f"userhist_{user_id}"))
    return builder.as_markup()

def get_notifications_kb(is_enabled: bool) -> InlineKeyboardMarkup:
    """Инлайн-кнопка для включения/выключения уведомлений"""
    builder = InlineKeyboardBuilder()
    text = "🔕 Выключить уведомления" if is_enabled else "🔔 Включить уведомления"
    builder.row(InlineKeyboardButton(text=text, callback_data="toggle_notif"))
    return builder.as_markup()