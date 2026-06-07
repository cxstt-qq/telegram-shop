import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiocryptopay import AioCryptoPay, Networks
from pybit.unified_trading import HTTP
import time  # Не забудь добавить импорт в начало файла

from config_data.config import config
from states.user_states import TopupStates, BybitTopupStates
from database.requests import (
    add_user_balance, get_admins_for_notifications, 
    is_bybit_tx_processed, register_bybit_tx
)
from keyboards.user_kb import (
    get_invoice_kb, get_cancel_topup_kb, get_topup_methods_kb, get_bybit_check_kb
)

router = Router()
logger = logging.getLogger(__name__)

crypto = AioCryptoPay(token=config.crypto_bot_token, network=Networks.MAIN_NET)
bybit_session = HTTP(
    api_key=config.bybit_api_key,
    api_secret=config.bybit_api_secret,
    testnet=False
)

@router.callback_query(F.data == "choose_topup_method")
async def show_topup_methods(callback: CallbackQuery, i18n):
    await callback.message.edit_text(
        text=i18n.topup_choose_method(), 
        reply_markup=get_topup_methods_kb(i18n)
    )

# --- БЛОК CRYPTOBOT ---
@router.callback_query(F.data == "topup_cryptobot")
async def start_topup(callback: CallbackQuery, state: FSMContext, i18n):
    await callback.message.edit_text(
        text=i18n.topup_cryptobot_info(), 
        reply_markup=get_cancel_topup_kb(i18n)
    )
    await state.set_state(TopupStates.waiting_for_amount)

@router.message(TopupStates.waiting_for_amount, F.text)
async def process_topup_amount(message: Message, state: FSMContext, i18n):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount < 0.1: raise ValueError
    except ValueError:
        await message.delete()
        return await message.answer(i18n.topup_invalid_amount(), reply_markup=get_cancel_topup_kb(i18n))

    await message.delete()
    await state.clear()
    
    invoice = await crypto.create_invoice(asset='USDT', amount=amount, description=f"Topup {message.from_user.id}")
    await message.answer(
        text=i18n.topup_invoice_created(invoice_id=str(invoice.invoice_id), amount=amount), 
        reply_markup=get_invoice_kb(invoice.bot_invoice_url, invoice.invoice_id, i18n)
    )

@router.callback_query(F.data.startswith("check_inv_"))
async def check_invoice_status(callback: CallbackQuery, i18n, db_user, bot: Bot):
    invoice_id = int(callback.data.split("_")[2])
    invoice = await crypto.get_invoices(invoice_ids=invoice_id)
    
    if not invoice: 
        return await callback.answer(i18n.topup_invoice_not_found(), show_alert=True)
        
    if invoice.status == 'paid':
        amount = float(invoice.amount)
        await add_user_balance(db_user.telegram_id, amount)
        logger.info(f"ПОПОЛНЕНИЕ: Юзер {db_user.telegram_id} через CryptoBot на {amount} $")
        
        admins_to_notify = await get_admins_for_notifications(config.admins)
        for adm_id in admins_to_notify:
            try: await bot.send_message(adm_id, f"💰 <b>CryptoBot!</b>\nЮзер: <code>{db_user.telegram_id}</code>\nСумма: <b>{amount} $</b>")
            except Exception: pass
            
        await callback.message.edit_text(i18n.topup_success(amount=amount))
    elif invoice.status == 'active':
        await callback.answer(i18n.topup_pending(), show_alert=True)
    elif invoice.status == 'expired':
        await callback.message.edit_text(i18n.topup_expired())
    else:
        await callback.message.edit_text(i18n.topup_error())

# --- БЛОК BYBIT ---
@router.callback_query(F.data == "topup_bybit")
async def start_bybit_topup(callback: CallbackQuery, state: FSMContext, i18n):
    await callback.message.edit_text(i18n.topup_bybit_info())
    await state.set_state(BybitTopupStates.waiting_for_uid)

@router.message(BybitTopupStates.waiting_for_uid, F.text)
async def process_bybit_uid(message: Message, state: FSMContext, i18n):
    clean_uid = ''.join(filter(str.isdigit, message.text))
    if not clean_uid:
        await message.delete()
        return await message.answer(i18n.topup_bybit_invalid_uid())
        
    await message.delete()
    await state.clear()
    
    await message.answer(
        text=i18n.topup_bybit_instruction(bot_uid=config.bybit_uid, user_uid=clean_uid), 
        reply_markup=get_bybit_check_kb(clean_uid, i18n)
    )

@router.callback_query(F.data.startswith("check_bybit_"))
async def check_bybit_deposit(callback: CallbackQuery, bot: Bot, db_user, i18n):
    user_uid = callback.data.split("_")[2]
    
    try:
        response = bybit_session.get_internal_deposit_records(coin="USDT", limit=20)
        records = response.get("result", {}).get("rows", [])
    except Exception as e:
        logger.error(f"Bybit API Error: {e}")
        return await callback.answer(i18n.topup_bybit_api_error(), show_alert=True)
        
    if not records:
        return await callback.answer(i18n.topup_bybit_not_found(), show_alert=True)
        
    # Вычисляем отсечку
    six_hours_ago_sec = int(time.time() - 6 * 3600)
    logger.info(f"🕒 Отсечка 6 часов назад: {six_hours_ago_sec}")
    
    found_any = False
    for record in records:
        tx_time = int(record.get("createdTime", 0))
        status = int(record.get("status", 0)) # Принудительно в int, вдруг там строка "2"
        from_uid = str(record.get("fromMemberId"))
        
        # Выводим инфу по каждой транзе в консоль!
        logger.info(f"🔎 Чек транзы: API_UID={from_uid} (Ждем={user_uid}) | Статус={status} | Время={tx_time} > {six_hours_ago_sec}: {tx_time > six_hours_ago_sec}")
        
        if from_uid == user_uid and status == 2 and tx_time > six_hours_ago_sec:
            tx_id = record.get("txID")
            amount = float(record.get("amount"))
            
            if await is_bybit_tx_processed(tx_id):
                logger.info(f"⚠️ Транзакция {tx_id} уже обрабатывалась.")
                continue  
                
            found_any = True
            await register_bybit_tx(tx_id, db_user.telegram_id, amount)
            await add_user_balance(db_user.telegram_id, amount)
            logger.info(f"✅ ПОПОЛНЕНИЕ: Юзер {db_user.telegram_id} Bybit UID {user_uid} на {amount} $")
            
            admins_to_notify = await get_admins_for_notifications(config.admins)
            for adm_id in admins_to_notify:
                try: await bot.send_message(adm_id, f"🔶 <b>Bybit!</b>\nЮзер: <code>{db_user.telegram_id}</code>\nUID: <code>{user_uid}</code>\nСумма: <b>{amount} $</b>")
                except Exception: pass
                
            await callback.message.edit_text(i18n.topup_bybit_success(user_uid=user_uid, amount=amount))
            break
            
    if not found_any:
        await callback.answer(i18n.topup_bybit_not_yours(), show_alert=True)

@router.callback_query(F.data == "cancel_topup")
async def cancel_topup(callback: CallbackQuery, state: FSMContext, i18n):
    await state.clear()
    await callback.message.edit_text(i18n.topup_cancelled())