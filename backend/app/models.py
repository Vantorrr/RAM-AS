from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from .database import Base

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
