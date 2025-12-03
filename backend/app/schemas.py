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
