from datetime import datetime, timedelta
from sqlalchemy import select, delete, update, func
from sqlalchemy.exc import IntegrityError
from database.db import async_session_maker
from database.models import (
    User, Category, Product, Item, Order, AdminSettings, BybitTransaction,
    BotSettings, CryptoBotInvoice, ReferralTransaction
)

# --- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ---

async def get_or_create_user(telegram_id: int, username: str | None, language: str = 'ru') -> User:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, username=username, language=language)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            user.is_new_user = True
        else:
            user.is_new_user = False
        return user

async def get_user(telegram_id: int) -> User | None:
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

async def update_user_language(telegram_id: int, language: str):
    async with async_session_maker() as session:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(language=language, language_set=True)
        )
        await session.commit()

async def bind_referrer(user_id: int, referrer_id: int) -> bool:
    async with async_session_maker() as session:
        if user_id == referrer_id:
            return False

        user = await session.get(User, user_id)
        referrer = await session.get(User, referrer_id)

        if not user or not referrer or user.referred_by is not None:
            return False

        user.referred_by = referrer_id
        await session.commit()
        return True

async def get_referral_percent() -> float:
    async with async_session_maker() as session:
        settings = await session.get(BotSettings, 1)
        if settings is None:
            settings = BotSettings(id=1, referral_percent=0.0)
            session.add(settings)
            await session.commit()
        return settings.referral_percent

async def set_referral_percent(percent: float):
    async with async_session_maker() as session:
        settings = await session.get(BotSettings, 1)
        if settings is None:
            settings = BotSettings(id=1, referral_percent=percent)
            session.add(settings)
        else:
            settings.referral_percent = percent
        await session.commit()

async def get_referral_stats(telegram_id: int) -> dict:
    async with async_session_maker() as session:
        referrals_count = await session.scalar(
            select(func.count(User.telegram_id)).where(User.referred_by == telegram_id)
        )
        earned = await session.scalar(
            select(User.referral_earned).where(User.telegram_id == telegram_id)
        )
        return {
            "referrals_count": referrals_count or 0,
            "referral_earned": earned or 0.0,
        }

# --- РАБОТА С КАТЕГОРИЯМИ И ТОВАРАМИ ---

async def get_categories():
    async with async_session_maker() as session:
        result = await session.execute(select(Category))
        return result.scalars().all()

async def get_category_by_id(category_id: int) -> Category | None:
    async with async_session_maker() as session:
        result = await session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

async def add_category(name_ru: str, name_en: str):
    async with async_session_maker() as session:
        category = Category(name_ru=name_ru, name_en=name_en)
        session.add(category)
        await session.commit()

async def delete_category(category_id: int):
    async with async_session_maker() as session:
        await session.execute(delete(Category).where(Category.id == category_id))
        await session.commit()

async def update_category_field(category_id: int, field: str, value: str) -> bool:
    allowed_fields = {"name_ru", "name_en"}
    if field not in allowed_fields:
        return False

    async with async_session_maker() as session:
        category = await session.get(Category, category_id)
        if not category:
            return False

        setattr(category, field, value)
        await session.commit()
        return True

async def get_products(category_id: int):
    async with async_session_maker() as session:
        result = await session.execute(select(Product).where(Product.category_id == category_id))
        return result.scalars().all()

async def get_products_with_counts(category_id: int):
    async with async_session_maker() as session:
        stmt = (
            select(Product, func.count(Item.id))
            .outerjoin(Item, (Item.product_id == Product.id) & (Item.is_sold == False))
            .where(Product.category_id == category_id)
            .group_by(Product.id)
        )
        result = await session.execute(stmt)
        return result.all()

async def get_all_products():
    async with async_session_maker() as session:
        result = await session.execute(select(Product))
        return result.scalars().all()

async def get_all_products_with_counts():
    async with async_session_maker() as session:
        stmt = (
            select(Product, func.count(Item.id))
            .outerjoin(Item, (Item.product_id == Product.id) & (Item.is_sold == False))
            .group_by(Product.id)
            .order_by(Product.id)
        )
        result = await session.execute(stmt)
        return result.all()

async def get_product_by_id(product_id: int) -> Product | None:
    async with async_session_maker() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

async def get_product_with_count(product_id: int):
    async with async_session_maker() as session:
        stmt = (
            select(Product, func.count(Item.id))
            .outerjoin(Item, (Item.product_id == Product.id) & (Item.is_sold == False))
            .where(Product.id == product_id)
            .group_by(Product.id)
        )
        result = await session.execute(stmt)
        return result.first()

async def add_product(category_id: int, title_ru: str, title_en: str, desc_ru: str, desc_en: str, price: float):
    async with async_session_maker() as session:
        product = Product(
            category_id=category_id, title_ru=title_ru, title_en=title_en,
            description_ru=desc_ru, description_en=desc_en, price=price
        )
        session.add(product)
        await session.commit()

async def delete_product(product_id: int):
    async with async_session_maker() as session:
        await session.execute(delete(Product).where(Product.id == product_id))
        await session.commit()

async def update_product_field(product_id: int, field: str, value) -> bool:
    allowed_fields = {"category_id", "title_ru", "title_en", "description_ru", "description_en", "price"}
    if field not in allowed_fields:
        return False

    async with async_session_maker() as session:
        product = await session.get(Product, product_id)
        if not product:
            return False

        setattr(product, field, value)
        await session.commit()
        return True

async def add_items_bulk(product_id: int, data_list: list[str]):
    async with async_session_maker() as session:
        items = [Item(product_id=product_id, data=data) for data in data_list if data.strip()]
        session.add_all(items)
        await session.commit()

async def extract_items_from_product(product_id: int, quantity: int) -> dict:
    async with async_session_maker() as session:
        product = await session.get(Product, product_id)
        if not product:
            return {"status": "not_found", "items": []}

        items_result = await session.execute(
            select(Item)
            .where(Item.product_id == product_id, Item.is_sold == False)
            .order_by(Item.id)
            .limit(quantity)
        )
        items = items_result.scalars().all()

        if not items:
            return {"status": "empty", "items": []}

        if len(items) < quantity:
            return {"status": "not_enough", "items": [], "available": len(items)}

        extracted = [item.data for item in items]
        for item in items:
            await session.delete(item)

        await session.commit()
        return {
            "status": "success",
            "items": extracted,
            "product_title": product.title_ru,
        }

# --- ТРАНЗАКЦИИ И СТАТИСТИКА ---

async def buy_items(telegram_id: int, product_id: int, quantity: int) -> dict:
    """
    Проводит массовую транзакцию покупки.
    Списывает баланс, сохраняет чек в историю и УДАЛЯЕТ выданные аккаунты из БД.
    """
    async with async_session_maker() as session:
        user = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = user.scalar_one_or_none()

        product = await session.execute(select(Product).where(Product.id == product_id))
        product = product.scalar_one_or_none()

        if not user or not product:
            return {'status': 'error'}

        # Запрашиваем нужное количество непроданных аккаунтов
        items_result = await session.execute(
            select(Item).where(Item.product_id == product_id, Item.is_sold == False).limit(quantity)
        )
        items = items_result.scalars().all()

        if len(items) < quantity:
            return {'status': 'no_stock'}

        total_price = product.price * quantity

        if user.balance < total_price:
            return {'status': 'no_balance'}

        # Списываем баланс
        user.balance -= total_price

        purchased_data = []
        for item in items:
            # Добавляем данные в список на выдачу
            purchased_data.append(item.data)
            
            # Записываем чек в историю заказов
            order = Order(
                user_id=user.telegram_id,
                product_id=product.id,
                product_name_snapshot=product.title_ru, 
                item_data=item.data,
                purchase_price=product.price
            )
            session.add(order)
            
            # ФИЗИЧЕСКИ УДАЛЯЕМ ТОВАР ИЗ БАЗЫ
            await session.delete(item)

        await session.commit()
        
        return {'status': 'success', 'item_data': '\n\n'.join(purchased_data)}

async def get_user_orders_count(telegram_id: int) -> int:
    async with async_session_maker() as session:
        result = await session.execute(select(func.count(Order.id)).where(Order.user_id == telegram_id))
        return result.scalar() or 0

async def get_detailed_stats(period: str) -> dict:
    async with async_session_maker() as session:
        now = datetime.utcnow()
        if period == '24h': start_date = now - timedelta(days=1)
        elif period == 'week': start_date = now - timedelta(days=7)
        elif period == 'month': start_date = now - timedelta(days=30)
        elif period == 'year': start_date = now - timedelta(days=365)
        else: start_date = datetime.min

        totals_result = await session.execute(
            select(func.count(Order.id), func.sum(Order.purchase_price))
            .where(Order.purchase_date >= start_date)
        )
        total_sales, total_rev = totals_result.first()
        total_sales = total_sales or 0
        total_rev = total_rev or 0.0

        items_result = await session.execute(
            select(
                Order.product_name_snapshot,
                func.count(Order.id),
                func.sum(Order.purchase_price)
            )
            .where(Order.purchase_date >= start_date)
            .group_by(Order.product_name_snapshot)
            .order_by(func.sum(Order.purchase_price).desc())
        )
        items_stats = items_result.all()

        return {'total_sales': total_sales, 'total_rev': total_rev, 'items': items_stats}

async def get_user_orders(telegram_id: int):
    """Достает полную историю заказов конкретного пользователя"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == telegram_id)
            .order_by(Order.purchase_date.desc()) # Сортируем от новых к старым
        )
        return result.scalars().all()

async def get_all_users() -> list[User]:
    """Получает всех пользователей из базы данных (для рассылки)"""
    async with async_session_maker() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

async def add_user_balance(telegram_id: int, amount: float, apply_referral: bool = True):
    """Начисляет баланс пользователю после успешной оплаты"""
    async with async_session_maker() as session:
        user = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = user.scalar_one_or_none()
        if not user:
            return {"credited": False, "referral": None}

        user.balance += amount
        referral = None

        if apply_referral and amount > 0 and user.referred_by:
            referral = await _apply_referral_bonus(session, user, amount)

        await session.commit()
        return {"credited": True, "referral": referral}

async def credit_cryptobot_invoice(telegram_id: int, invoice_id: int, amount: float) -> dict:
    async with async_session_maker() as session:
        processed_invoice = await session.get(CryptoBotInvoice, invoice_id)
        if processed_invoice:
            return {"credited": False, "referral": None}

        user = await session.get(User, telegram_id)
        if not user:
            return {"credited": False, "referral": None}

        user.balance += amount
        referral = await _apply_referral_bonus(session, user, amount)
        session.add(CryptoBotInvoice(invoice_id=invoice_id, telegram_id=telegram_id, amount=amount))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return {"credited": False, "referral": None}
        return {"credited": True, "referral": referral}

async def _apply_referral_bonus(session, user: User, amount: float):
    if amount <= 0 or not user.referred_by:
        return None

    settings = await session.get(BotSettings, 1)
    referral_percent = settings.referral_percent if settings else 0.0
    bonus_amount = round(amount * referral_percent / 100, 2)

    if bonus_amount <= 0:
        return None

    referrer = await session.get(User, user.referred_by)
    if not referrer:
        return None

    referrer.balance += bonus_amount
    referrer.referral_earned = (referrer.referral_earned or 0.0) + bonus_amount
    session.add(ReferralTransaction(
        referrer_id=referrer.telegram_id,
        referred_id=user.telegram_id,
        topup_amount=amount,
        bonus_amount=bonus_amount,
        percent=referral_percent
    ))
    return {
        "referrer_id": referrer.telegram_id,
        "referrer_language": referrer.language,
        "referred_id": user.telegram_id,
        "topup_amount": amount,
        "bonus_amount": bonus_amount,
        "percent": referral_percent,
    }

async def get_admin_notifications_status(telegram_id: int) -> bool:
    """Получает статус уведомлений админа. По умолчанию - включены."""
    async with async_session_maker() as session:
        result = await session.execute(select(AdminSettings).where(AdminSettings.telegram_id == telegram_id))
        settings = result.scalar_one_or_none()
        
        if settings is None:
            settings = AdminSettings(telegram_id=telegram_id, notifications=True)
            session.add(settings)
            await session.commit()
            
        return settings.notifications

async def toggle_admin_notifications(telegram_id: int) -> bool:
    """Переключает статус уведомлений (Вкл/Выкл)"""
    async with async_session_maker() as session:
        result = await session.execute(select(AdminSettings).where(AdminSettings.telegram_id == telegram_id))
        settings = result.scalar_one_or_none()
        
        if settings is None:
            settings = AdminSettings(telegram_id=telegram_id, notifications=False)
            session.add(settings)
        else:
            settings.notifications = not settings.notifications
            
        await session.commit()
        return settings.notifications

async def get_admins_for_notifications(all_admins: list[int]) -> list[int]:
    """Возвращает список ID админов, у которых НЕ выключены уведомления"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(AdminSettings.telegram_id).where(AdminSettings.notifications == False)
        )
        opted_out = set(result.scalars().all())
        
        # Берем список всех админов из конфига и исключаем тех, кто нажал "Выключить"
        return [adm for adm in all_admins if adm not in opted_out]
    
async def is_bybit_tx_processed(tx_id: str) -> bool:
    """Проверяет, обрабатывался ли этот перевод ранее"""
    async with async_session_maker() as session:
        result = await session.execute(select(BybitTransaction).where(BybitTransaction.tx_id == tx_id))
        return result.scalar_one_or_none() is not None

async def register_bybit_tx(tx_id: str, telegram_id: int, amount: float):
    """Регистрирует перевод в базе, чтобы его нельзя было использовать повторно"""
    async with async_session_maker() as session:
        tx = BybitTransaction(tx_id=tx_id, telegram_id=telegram_id, amount=amount)
        session.add(tx)
        await session.commit()
