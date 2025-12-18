from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from .database import Base
import enum


# ============ ENUMS ============
class SellerStatus(str, enum.Enum):
    PENDING = "pending"       # Ожидает модерации
    APPROVED = "approved"     # Одобрен
    REJECTED = "rejected"     # Отклонен
    BANNED = "banned"         # Заблокирован


class SubscriptionTier(str, enum.Enum):
    FREE = "free"             # Бесплатный (до 10 товаров)
    START = "start"           # Старт (до 50 товаров) - 2000р/мес
    PRO = "pro"               # Профи (до 1000 товаров) - 10000р/мес
    MAGNATE = "magnate"       # Магнат (безлимит + приоритет) - 25000р/мес


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"           # Черновик (не оплачен)
    PENDING = "pending"       # Ожидает модерации
    APPROVED = "approved"     # Одобрен, показывается
    REJECTED = "rejected"     # Отклонен
    SOLD = "sold"             # Продано
    EXPIRED = "expired"       # Истек срок

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, unique=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    image_url = Column(String, nullable=True)
    
    products = relationship("Product", back_populates="category")
    
    children = relationship("Category", 
                            backref=backref("parent", remote_side=[id]),
                            cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    part_number = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)  # Производитель
    price_usd = Column(Float, nullable=True)
    price_rub = Column(Float, nullable=True)
    is_in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    image_url = Column(String, nullable=True)
    is_preorder = Column(Boolean, default=False)
    is_installment_available = Column(Boolean, default=False)
    
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="products")
    
    # Маркетплейс: чей товар (NULL = RAM US, иначе = ID партнера)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=True)
    seller = relationship("Seller", back_populates="products")
    
    # Статистика просмотров
    views_count = Column(Integer, default=0)
    
    # Витрина: показывать на главной
    is_featured = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)  # Порядок на витрине
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_telegram_id = Column(String, index=True)
    user_name = Column(String, nullable=True)
    user_phone = Column(String, nullable=True)
    delivery_address = Column(String, nullable=True)
    total_amount = Column(Float)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    price_at_purchase = Column(Float)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product")


# ============ MARKETPLACE MODELS ============

class Seller(Base):
    """Продавец/Партнер на маркетплейсе"""
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    
    # Контактные данные
    name = Column(String, index=True)                    # Название магазина/ИП
    contact_name = Column(String, nullable=True)         # Контактное лицо
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telegram_id = Column(String, unique=True, index=True)  # Telegram ID для авторизации
    telegram_username = Column(String, nullable=True)
    
    # Описание
    description = Column(Text, nullable=True)            # О компании
    logo_url = Column(String, nullable=True)
    
    # Статус и верификация
    status = Column(String, default=SellerStatus.PENDING.value)
    is_verified = Column(Boolean, default=False)         # Галочка "Проверенный"
    
    # Подписка
    subscription_tier = Column(String, default=SubscriptionTier.FREE.value)
    subscription_expires = Column(DateTime(timezone=True), nullable=True)
    max_products = Column(Integer, default=10)           # Лимит товаров по подписке
    
    # Статистика
    total_views = Column(Integer, default=0)
    total_sales = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="seller")
    subscriptions = relationship("Subscription", back_populates="seller")


class Subscription(Base):
    """История подписок партнеров"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"))
    
    tier = Column(String)                                # start/pro/magnate
    price_paid = Column(Float)                           # Сколько заплатил
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    payment_id = Column(String, nullable=True)           # ID платежа (ЮКасса и т.д.)
    
    seller = relationship("Seller", back_populates="subscriptions")


class Listing(Base):
    """Объявление Барахолки (частные продажи)"""
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Контент объявления
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float)
    
    # Фото (до 5 шт, JSON массив URL)
    images = Column(Text, nullable=True)                 # JSON: ["url1", "url2", ...]
    
    # Контакты продавца
    seller_name = Column(String, nullable=True)
    seller_phone = Column(String, nullable=True)
    seller_telegram_id = Column(String, index=True)
    seller_telegram_username = Column(String, nullable=True)
    
    # Локация
    city = Column(String, nullable=True)
    
    # Статус и модерация
    status = Column(String, default=ListingStatus.DRAFT.value)
    rejection_reason = Column(String, nullable=True)     # Причина отклонения
    
    # Оплата за размещение
    is_paid = Column(Boolean, default=False)
    payment_amount = Column(Float, default=200.0)        # Стоимость размещения
    payment_id = Column(String, nullable=True)
    
    # Продвижение
    is_promoted = Column(Boolean, default=False)         # Закреплен в топе
    promoted_until = Column(DateTime(timezone=True), nullable=True)
    
    # Статистика
    views_count = Column(Integer, default=0)
    
    # Сроки
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Когда истекает (30 дней)


class ProductView(Base):
    """Счетчик просмотров товаров (для статистики партнеров)"""
    __tablename__ = "product_views"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    
    viewer_telegram_id = Column(String, nullable=True)   # Кто смотрел (если известно)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Для уникальности (1 пользователь = 1 просмотр в день)
    # Можно добавить уникальный индекс на (product_id, viewer_telegram_id, date)

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_telegram_id = Column(String, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
