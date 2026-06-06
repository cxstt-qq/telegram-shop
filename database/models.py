from datetime import datetime
from sqlalchemy import BigInteger, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db import Base

class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    language: Mapped[str] = mapped_column(String(2), default='ru')
    language_set: Mapped[bool] = mapped_column(Boolean, default=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user")

class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_ru: Mapped[str] = mapped_column(String(64))
    name_en: Mapped[str] = mapped_column(String(64))

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete='CASCADE'))
    
    title_ru: Mapped[str] = mapped_column(String(128))
    title_en: Mapped[str] = mapped_column(String(128))
    description_ru: Mapped[str] = mapped_column(String(1024))
    description_en: Mapped[str] = mapped_column(String(1024))
    price: Mapped[float] = mapped_column(Float)

    category = relationship("Category", back_populates="products")
    items = relationship("Item", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="product")

class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='CASCADE'))
    
    data: Mapped[str] = mapped_column(String)
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    added_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="items")

class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.telegram_id', ondelete='SET NULL'), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    
    # Тот самый слепок названия, который выживет даже после удаления лота
    product_name_snapshot: Mapped[str] = mapped_column(String(128), default="Неизвестный товар")
    
    item_data: Mapped[str] = mapped_column(String)
    purchase_price: Mapped[float] = mapped_column(Float)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")

class AdminSettings(Base):
    __tablename__ = 'admin_settings'
    
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    notifications: Mapped[bool] = mapped_column(Boolean, default=True)

class BybitTransaction(Base):
    __tablename__ = 'bybit_transactions'
    
    tx_id: Mapped[str] = mapped_column(String(128), primary_key=True)  # Уникальный ID перевода от Bybit
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    amount: Mapped[float] = mapped_column(Float)
    checked_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)