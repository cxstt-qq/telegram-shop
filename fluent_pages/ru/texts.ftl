start_welcome = 👋 Привет! Добро пожаловать в магазин аккаунтов. Пожалуйста, выбери язык:
language_set = 🇷🇺 Язык успешно изменен на Русский!

main_menu = 🏠 Главное меню
btn_profile = 👤 Личный кабинет
btn_shop = 🛒 Магазин
btn_support = 💬 Поддержка

profile_info = 👤 <b>Твой профиль:</b>
    ├ ID: <code>{ $user_id }</code>
    ├ Баланс: { $balance } $
    ├ Дата регистрации: { $reg_date }
    └ Всего покупок: { $orders_count }

shop_title = 🛒 <b>Каталог товаров</b>
shop_desc = Выбери нужную категорию ниже:

empty_category = 😔 В этой категории пока нет товаров.
support_text = 💬 Для связи с поддержкой пиши: @wesqqu

btn_buy = 💳 Купить ({ $price } $)
btn_back = 🔙 Назад
btn_main_menu = 🏠 В главное меню
btn_topup = 💳 Пополнить баланс
buy_no_balance = ❌ Недостаточно средств. Пополни баланс в профиле.
buy_out_of_stock = ❌ К сожалению, этот товар только что закончился.
buy_success = 🎉 Успешная покупка! 
    Вот твои данные:
    <code>{ $item_data }</code>
buy_enter_quantity = 🔢 Введи количество товаров для покупки (доступно: { $available } шт.):
buy_invalid_quantity = ❌ Пожалуйста, введи целое число больше нуля (например: 1, 2, 5).
buy_confirm = 🛒 <b>Подтверждение покупки:</b>
    Товар: { $title }
    Количество: { $quantity } шт.
    Цена за шт: { $price } $
    
    🧾 <b>Итого к оплате: { $total_price } $</b>
btn_confirm = ✅ Подтвердить
btn_cancel = ❌ Отмена
buy_cancelled = 🚫 Покупка отменена. Возврат в меню.

# --- ПОПОЛНЕНИЕ БАЛАНСА ---
topup_choose_method = 💳 <b>Выберите метод пополнения баланса:</b>
topup_cryptobot_info = 💳 <b>Пополнение через CryptoBot</b>

    Введите сумму пополнения в <b>USDT</b> (мин. 0.1):
topup_invalid_amount = ❌ Введите корректное число больше 0.1 (например: 5):
topup_invoice_created = 🧾 <b>Счет #{ $invoice_id }</b>

    Сумма: <b>{ $amount } USDT</b>
topup_invoice_not_found = ❌ Счет не найден.
topup_success = ✅ <b>Оплата успешно получена!</b>
    На ваш баланс зачислено: <b>{ $amount } $</b>
    
    Спасибо за пополнение!
topup_pending = ⏳ Счет еще не оплачен. Ждем поступления средств...
topup_expired = ❌ Время действия счета истекло. Создайте новый.
topup_error = ❌ Счет отменен или произошла ошибка.
topup_cancelled = 🚫 Пополнение отменено.

# --- BYBIT ---
topup_bybit_info = 🔶 <b>Пополнение через Bybit (Внутренний перевод)</b>

    Пожалуйста, введите <b>ваш Bybit UID</b> (строка из цифр), с которого вы будете совершать перевод.
    Это нужно, чтобы бот смог определить именно ваш платеж.
topup_bybit_invalid_uid = ❌ UID должен состоять только из цифр. Введите еще раз:
topup_bybit_instruction = 🔶 <b>Инструкция по переводу Bybit</b>

    1. Откройте Bybit и сделайте <b>Внутренний перевод</b> (Internal Transfer).
    2. UID получателя: <code>{ $bot_uid }</code>
    3. Монета: <b>USDT</b>
    
    ⚠️ Важно: перевод должен быть строго с вашего UID: <code>{ $user_uid }</code>
    
    После отправки перевода подождите пару минут и нажмите кнопку ниже.
topup_bybit_api_error = ❌ Ошибка связи с API Bybit. Попробуйте позже.
topup_bybit_not_found = ⏳ Переводов в USDT пока не обнаружено. Подождите еще немного.
topup_bybit_success = 🎉 <b>Успешно!</b>
    Ваш перевод от Bybit UID { $user_uid } найден.
    На баланс зачислено: <b>{ $amount } $</b>
topup_bybit_not_yours = 🤷‍♂️ Перевод от вашего UID на данный момент не найден. Проверьте статус в приложении Bybit.

# --- КНОПКИ И ОШИБКИ ---
btn_crypto = 🤖 CryptoBot (USDT, TON)
btn_bybit = 🔶 Bybit Внутренний перевод
btn_check_bybit = 🔄 Проверить перевод
btn_pay = 💸 Перейдите к оплате
btn_check_pay = 🔄 Проверить оплату
error_product_not_found = ❌ Товар не найден.
error_buy_failed = ❌ Произошла ошибка при покупке.