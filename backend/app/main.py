from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from . import models, schemas, crud, database, currency
from .database import engine
from .bot import notify_new_order

app = FastAPI(
    title="RAM US Auto Parts",
    description="API for Telegram WebApp Auto Parts Store",
    version="0.1.0"
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin Views
class ProductAdmin(ModelView, model=models.Product):
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-box"
    
    # Колонки в списке
    column_list = [
        models.Product.id, 
        models.Product.name, 
        models.Product.part_number,
        models.Product.price_rub, 
        models.Product.is_in_stock,
        models.Product.stock_quantity,
        models.Product.is_installment_available,
        models.Product.category_id,
    ]
    
    # Поля для редактирования
    form_columns = [
        models.Product.name,
        models.Product.part_number,
        models.Product.description,
        models.Product.manufacturer,
        models.Product.price_rub,
        models.Product.price_usd,
        models.Product.is_in_stock,
        models.Product.stock_quantity,
        models.Product.image_url,
        models.Product.is_preorder,
        models.Product.is_installment_available,
        models.Product.category_id,
    ]
    
    # Поиск
    column_searchable_list = [models.Product.name, models.Product.part_number, models.Product.description]
    
    # Сортировка
    column_sortable_list = [
        models.Product.id,
        models.Product.name,
        models.Product.price_rub, 
        models.Product.is_in_stock,
        models.Product.stock_quantity,
    ]
    
    # Фильтры
    column_default_sort = [(models.Product.id, True)]
    
    # Подсказки
    form_args = {
        "name": {"label": "Название товара"},
        "part_number": {"label": "Артикул"},
        "description": {"label": "Описание"},
        "manufacturer": {"label": "Производитель"},
        "price_rub": {"label": "Цена (₽)"},
        "price_usd": {"label": "Цена ($)"},
        "is_in_stock": {"label": "В наличии"},
        "stock_quantity": {"label": "Кол-во на складе"},
        "image_url": {"label": "URL фото"},
        "is_preorder": {"label": "Под заказ"},
        "is_installment_available": {"label": "Рассрочка 0%"},
        "category_id": {"label": "Категория (ID)"},
    }

class CategoryAdmin(ModelView, model=models.Category):
    name = "Категория"
    name_plural = "Категории"
    icon = "fa-solid fa-folder"
    
    column_list = [
        models.Category.id, 
        models.Category.name, 
        models.Category.slug,
        models.Category.parent_id,
        models.Category.image_url
    ]
    
    form_columns = [
        models.Category.name,
        models.Category.slug,
        models.Category.parent_id,
        models.Category.image_url,
    ]
    
    column_searchable_list = [models.Category.name]
    column_sortable_list = [models.Category.id, models.Category.name, models.Category.parent_id]
    
    form_args = {
        "name": {"label": "Название"},
        "slug": {"label": "URL (slug)"},
        "parent_id": {"label": "Родительская категория (ID)"},
        "image_url": {"label": "URL картинки"},
    }

class OrderAdmin(ModelView, model=models.Order):
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-cart-shopping"
    
    column_list = [
        models.Order.id, 
        models.Order.user_telegram_id, 
        models.Order.user_name,
        models.Order.user_phone,
        models.Order.total_amount, 
        models.Order.status,
        models.Order.created_at,
    ]
    
    form_columns = [
        models.Order.user_telegram_id,
        models.Order.user_name,
        models.Order.user_phone,
        models.Order.delivery_address,
        models.Order.total_amount,
        models.Order.status,
    ]
    
    column_sortable_list = [models.Order.id, models.Order.total_amount, models.Order.created_at]
    column_default_sort = [(models.Order.id, True)]
    
    form_args = {
        "user_telegram_id": {"label": "Telegram ID"},
        "user_name": {"label": "Имя клиента"},
        "user_phone": {"label": "Телефон"},
        "delivery_address": {"label": "Адрес доставки"},
        "total_amount": {"label": "Сумма (₽)"},
        "status": {"label": "Статус"},
    }

admin = Admin(app, engine)
admin.add_view(ProductAdmin)
admin.add_view(CategoryAdmin)
admin.add_view(OrderAdmin)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "RAM US Auto Parts API is running. Stay Top."}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/products/", response_model=schemas.Product)
async def create_product(product: schemas.ProductCreate, db: AsyncSession = Depends(database.get_db)):
    db_product = await crud.get_product_by_part_number(db, part_number=product.part_number)
    if db_product:
        raise HTTPException(status_code=400, detail="Product with this part number already exists")
    return await crud.create_product(db=db, product=product)

@app.get("/products/", response_model=List[schemas.Product])
async def read_products(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    sort_by: Optional[str] = None,  # price_asc, price_desc, name_asc, name_desc
    db: AsyncSession = Depends(database.get_db)
):
    query = select(models.Product)
    
    if category_id:
        query = query.where(models.Product.category_id == category_id)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (models.Product.name.ilike(search_filter)) |
            (models.Product.part_number.ilike(search_filter)) |
            (models.Product.manufacturer.ilike(search_filter))
        )
    
    if min_price is not None:
        query = query.where(models.Product.price_rub >= min_price)
    
    if max_price is not None:
        query = query.where(models.Product.price_rub <= max_price)
    
    if in_stock is not None:
        query = query.where(models.Product.is_in_stock == in_stock)
    
    # Сортировка
    if sort_by == "price_asc":
        query = query.order_by(models.Product.price_rub.asc())
    elif sort_by == "price_desc":
        query = query.order_by(models.Product.price_rub.desc())
    elif sort_by == "name_asc":
        query = query.order_by(models.Product.name.asc())
    elif sort_by == "name_desc":
        query = query.order_by(models.Product.name.desc())
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/products/count")
async def get_products_count(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    db: AsyncSession = Depends(database.get_db)
):
    from sqlalchemy import func
    query = select(func.count(models.Product.id))
    
    if category_id:
        query = query.where(models.Product.category_id == category_id)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (models.Product.name.ilike(search_filter)) |
            (models.Product.part_number.ilike(search_filter)) |
            (models.Product.manufacturer.ilike(search_filter))
        )
    
    if min_price is not None:
        query = query.where(models.Product.price_rub >= min_price)
    
    if max_price is not None:
        query = query.where(models.Product.price_rub <= max_price)
    
    if in_stock is not None:
        query = query.where(models.Product.is_in_stock == in_stock)
    
    result = await db.execute(query)
    return {"count": result.scalar()}

@app.get("/products/{product_id}", response_model=schemas.Product)
async def read_product(product_id: int, db: AsyncSession = Depends(database.get_db)):
    db_product = await crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.put("/products/{product_id}", response_model=schemas.Product)
async def update_product(product_id: int, product_data: schemas.ProductUpdate, db: AsyncSession = Depends(database.get_db)):
    """Обновить товар (для админки)"""
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    db_product = result.scalar_one_or_none()
    
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_product, field):
            setattr(db_product, field, value)
    
    await db.commit()
    await db.refresh(db_product)
    return db_product

@app.get("/categories/tree", response_model=List[schemas.CategoryTree])
async def get_categories_tree(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.Category))
    categories = result.scalars().all()
    
    # Строим словарь категорий вручную, без from_orm
    cat_dict = {}
    for cat in categories:
        cat_dict[cat.id] = schemas.CategoryTree(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            parent_id=cat.parent_id,
            image_url=cat.image_url,
            children=[]
        )
    
    root_cats = []
    
    for cat in categories:
        if cat.parent_id is None:
            root_cats.append(cat_dict[cat.id])
        else:
            if cat.parent_id in cat_dict:
                cat_dict[cat.parent_id].children.append(cat_dict[cat.id])
                
    return root_cats

@app.get("/currency/usd-rate")
async def get_usd_rate():
    """Получить текущий курс USD/RUB"""
    rate = await currency.get_usd_rate()
    return {"rate": rate, "currency": "USD/RUB"}

@app.post("/orders/", response_model=schemas.Order)
async def create_order(
    order: schemas.OrderCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(database.get_db)
):
    """Создать новый заказ"""
    db_order = models.Order(
        user_telegram_id=order.user_telegram_id,
        user_name=order.user_name,
        user_phone=order.user_phone,
        delivery_address=order.delivery_address,
        total_amount=order.total_amount,
        status="pending"
    )
    db.add(db_order)
    await db.flush()
    
    # Добавляем товары в заказ
    for item in order.items:
        db_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=item.price_at_purchase
        )
        db.add(db_item)
    
    await db.commit()
    await db.refresh(db_order)
    
    # Отправляем уведомление в фоне
    background_tasks.add_task(
        notify_new_order,
        {
            "id": db_order.id,
            "user_name": db_order.user_name,
            "user_phone": db_order.user_phone,
            "delivery_address": db_order.delivery_address,
            "total_amount": db_order.total_amount,
            "items": order.items,
            "created_at": db_order.created_at.strftime("%d.%m.%Y %H:%M")
        }
    )
    
    return db_order
