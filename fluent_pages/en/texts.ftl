start_welcome = 👋 Hello! Welcome to the account shop. Please choose your language:
language_set = 🇬🇧 Language successfully changed to English!

main_menu = 🏠 Main Menu
btn_profile = 👤 Profile
btn_shop = 🛒 Shop
btn_support = 💬 Support

profile_info = 👤 <b>Your Profile:</b>
    ├ ID: <code>{ $user_id }</code>
    ├ Balance: ${ $balance }
    ├ Registration Date: { $reg_date }
    └ Total Orders: { $orders_count }
profile_referral_info = 🤝 <b>Referral program:</b>
    ├ Link: <code>{ $referral_link }</code>
    ├ Invited: <b>{ $referrals_count }</b>
    ├ Earned: <b>${ $referral_earned }</b>
    └ Current percent: <b>{ $referral_percent }%</b>
referral_bonus_received = 🤝 <b>Referral reward!</b>
    Your referral <code>{ $referred_id }</code> topped up <b>${ $topup_amount }</b>.
    Your percent: <b>{ $percent }%</b>
    Reward: <b>${ $bonus_amount }</b>

shop_title = 🛒 <b>Product Catalog</b>
shop_desc = Choose a category below:

empty_category = 😔 No products available in this category yet.
support_text = 💬 For support, please contact: @wesqqu
action_cancelled = 🚫 Action cancelled.

btn_buy = 💳 Buy (${ $price })
btn_back = 🔙 Back
btn_main_menu = 🏠 Main Menu
btn_topup = 💳 Top up balance
buy_no_balance = ❌ Insufficient funds. Please top up your balance in Profile.
buy_out_of_stock = ❌ Sorry, this item is out of stock.
buy_success = 🎉 Successful purchase! 
    Here is your data:
    <code>{ $item_data }</code>
buy_enter_quantity = 🔢 Enter the quantity of items to buy (available: { $available } pcs.):
buy_invalid_quantity = ❌ Please enter a whole number greater than zero (e.g., 1, 2, 5).
buy_confirm = 🛒 <b>Purchase Confirmation:</b>
    Item: { $title }
    Quantity: { $quantity } pcs.
    Price per item: ${ $price }
    
    🧾 <b>Total to pay: ${ $total_price }</b>
btn_confirm = ✅ Confirm
btn_cancel = ❌ Cancel
buy_cancelled = 🚫 Purchase cancelled. Returning to menu.

# --- BALANCE TOPUP ---
topup_choose_method = 💳 <b>Choose a top-up method:</b>
topup_cryptobot_info = 💳 <b>Top-up via CryptoBot</b>

    Enter the top-up amount in <b>USDT</b> (min. 0.1):
topup_invalid_amount = ❌ Please enter a valid number greater than 0.1 (e.g., 5):
topup_invoice_created = 🧾 <b>Invoice #{ $invoice_id }</b>

    Amount: <b>{ $amount } USDT</b>
topup_invoice_not_found = ❌ Invoice not found.
topup_invoice_already_credited = ✅ This invoice has already been credited to your balance.
topup_success = ✅ <b>Payment successfully received!</b>
    Credited to your balance: <b>${ $amount }</b>
    
    Thank you for your top-up!
topup_pending = ⏳ The invoice is not paid yet. Waiting for funds...
topup_expired = ❌ The invoice has expired. Please create a new one.
topup_error = ❌ The invoice was cancelled or an error occurred.
topup_cancelled = 🚫 Top-up cancelled.

# --- BYBIT ---
topup_bybit_info = 🔶 <b>Top-up via Bybit (Internal Transfer)</b>

    Please enter <b>your Bybit UID</b> (numbers only) from which you will make the transfer.
    This is necessary for the bot to identify your payment.
topup_bybit_invalid_uid = ❌ UID must contain only numbers. Please try again:
topup_bybit_instruction = 🔶 <b>Bybit Transfer Instructions</b>

    1. Open Bybit and make an <b>Internal Transfer</b>.
    2. Recipient UID: <code>{ $bot_uid }</code>
    3. Coin: <b>USDT</b>
    
    ⚠️ Important: The transfer must be strictly from your UID: <code>{ $user_uid }</code>
    
    After sending the transfer, wait a couple of minutes and click the button below.
topup_bybit_api_error = ❌ Bybit API connection error. Please try again later.
topup_bybit_not_found = ⏳ No USDT transfers found yet. Please wait a little longer.
topup_bybit_success = 🎉 <b>Success!</b>
    Your transfer from Bybit UID { $user_uid } was found.
    Credited to your balance: <b>${ $amount }</b>
topup_bybit_not_yours = 🤷‍♂️ Transfer from your UID not found at the moment. Check the status in the Bybit app.

# --- BUTTONS & ERRORS ---
btn_crypto = 🤖 CryptoBot (USDT, TON)
btn_bybit = 🔶 Bybit Internal Transfer
btn_check_bybit = 🔄 Check Transfer
btn_pay = 💸 Go to Payment
btn_check_pay = 🔄 Check Payment
error_product_not_found = ❌ Product not found.
error_buy_failed = ❌ An error occurred during the purchase.
