from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    slug: str
    parent_id: Optional[int] = None
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryTree(CategoryBase):
    id: int
    children: List['CategoryTree'] = []
    class Config:
        from_attributes = True

class Category(CategoryBase):
    id: int
    class Config:
        from_attributes = True

# Product Schemas
class ProductBase(BaseModel):
    name: str
    part_number: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    price_usd: Optional[float] = None
    price_rub: Optional[float] = None
    is_in_stock: bool = True
    stock_quantity: int = 0
    image_url: Optional[str] = None
    is_preorder: bool = False
    is_installment_available: bool = False # New field
    category_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    part_number: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    price_usd: Optional[float] = None
    price_rub: Optional[float] = None
    is_in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    is_preorder: Optional[bool] = None
    is_installment_available: Optional[bool] = None
    category_id: Optional[int] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # category: Optional[Category] = None  # Removed to avoid lazy loading issues
    
    class Config:
        from_attributes = True

# Order Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price_at_purchase: float

class OrderCreate(BaseModel):
    user_telegram_id: str
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    total_amount: float
    items: List[OrderItemBase]

class OrderItem(OrderItemBase):
    id: int
    product: Optional[Product] = None
    class Config:
        from_attributes = True

class Order(BaseModel):
    id: int
    user_telegram_id: str
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItem] = []
    
    class Config:
        from_attributes = True


# ============ MARKETPLACE SCHEMAS ============

# --- Seller (Партнер) ---
class SellerBase(BaseModel):
    name: str
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_username: Optional[str] = None
    description: Optional[str] = None

class SellerCreate(SellerBase):
    """Заявка на партнерство (отправляет пользователь)"""
    telegram_id: str

class SellerUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    status: Optional[str] = None
    is_verified: Optional[bool] = None
    subscription_tier: Optional[str] = None
    max_products: Optional[int] = None

class Seller(SellerBase):
    id: int
    telegram_id: str
    logo_url: Optional[str] = None
    status: str
    is_verified: bool
    subscription_tier: str
    subscription_expires: Optional[datetime] = None
    max_products: int
    total_views: int
    total_sales: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SellerPublic(BaseModel):
    """Публичная информация о продавце (для покупателей)"""
    id: int
    name: str
    logo_url: Optional[str] = None
    is_verified: bool
    total_sales: int
    
    class Config:
        from_attributes = True


# --- Listing (Барахолка) ---
class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    city: Optional[str] = None

class ListingCreate(ListingBase):
    """Создание объявления (отправляет пользователь)"""
    seller_name: Optional[str] = None
    seller_phone: Optional[str] = None
    seller_telegram_id: str
    seller_telegram_username: Optional[str] = None
    images: Optional[str] = None  # JSON массив URL

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    city: Optional[str] = None
    images: Optional[str] = None
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_paid: Optional[bool] = None
    is_promoted: Optional[bool] = None

class Listing(ListingBase):
    id: int
    images: Optional[str] = None
    seller_name: Optional[str] = None
    seller_phone: Optional[str] = None
    seller_telegram_id: str
    seller_telegram_username: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    is_paid: bool
    payment_amount: float
    is_promoted: bool
    promoted_until: Optional[datetime] = None
    views_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ListingPublic(BaseModel):
    """Публичная информация об объявлении (для ленты)"""
    id: int
    title: str
    description: Optional[str] = None
    price: float
    city: Optional[str] = None
    images: Optional[str] = None
    seller_name: Optional[str] = None
    seller_telegram_username: Optional[str] = None
    is_promoted: bool
    views_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- Subscription (Подписка) ---
class SubscriptionCreate(BaseModel):
    seller_id: int
    tier: str  # start/pro/magnate
    price_paid: float
    expires_at: datetime
    payment_id: Optional[str] = None

class Subscription(SubscriptionCreate):
    id: int
    started_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# --- Stats ---
class SellerStats(BaseModel):
    """Статистика для кабинета партнера"""
    total_products: int
    total_views: int
    total_orders: int
    products_limit: int
    subscription_tier: str
    subscription_expires: Optional[datetime] = None
