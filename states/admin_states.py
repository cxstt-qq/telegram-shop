from aiogram.fsm.state import State, StatesGroup

class CategoryStates(StatesGroup):
    waiting_for_name_ru = State()
    waiting_for_name_en = State()

class ProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_title_ru = State()
    waiting_for_title_en = State()
    waiting_for_desc_ru = State()
    waiting_for_desc_en = State()
    waiting_for_price = State()

class ItemStates(StatesGroup):
    waiting_for_product_id = State()
    waiting_for_items_data = State()

class UserManStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_balance_amount = State()

class UserStatsStates(StatesGroup):
    waiting_for_user_id = State()

class BroadcastStates(StatesGroup):
    """Состояния для массовой рассылки"""
    waiting_for_message = State()

class PrivateMsgStates(StatesGroup):
    """Состояния для отправки ЛС пользователю"""
    waiting_for_user_id = State()
    waiting_for_message = State()

class ReferralSettingsStates(StatesGroup):
    waiting_for_percent = State()
