from aiogram.fsm.state import State, StatesGroup

class BuyItemStates(StatesGroup):
    waiting_for_quantity = State()

class TopupStates(StatesGroup):
    """Состояние для пополнения баланса"""
    waiting_for_amount = State()

class BybitTopupStates(StatesGroup):
    waiting_for_uid = State()