"""
Admin API Router
Управление категориями, витриной и настройками магазина
"""

import os
import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel

from .. import models, schemas
from ..database import get_db

# Список ID админов из переменной окружения
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_IDS", "").split(",")
ADMIN_CHAT_IDS = [x.strip() for x in ADMIN_CHAT_IDS if x.strip()]

def verify_admin(x_telegram_user_id: Optional[str] = Header(None)):
    """Проверка, что запрос от админа"""
    if not x_telegram_user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing Telegram User ID")
    
    if x_telegram_user_id not in ADMIN_CHAT_IDS:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    
    return x_telegram_user_id

router = APIRouter(
    prefix="/api/admin", 
    tags=["Admin"],
    dependencies=[Depends(verify_admin)]  # Защита всех роутов!
)


# ============ ПРИВЯЗКА ТОВАРОВ К МАШИНАМ ============

@router.post("/link-products")
async def link_products_to_vehicles(db: AsyncSession = Depends(get_db)):
    """
    ПРИВЯЗАТЬ ВСЕ ТОВАРЫ К МАШИНАМ
    Быстрая привязка по ключевым словам
    """
    from sqlalchemy import text
    
    print("🚀 БЫСТРАЯ ПРИВЯЗКА - СТАРТ!")
    
    # 1. ОЧИЩАЕМ
    await db.execute(text("TRUNCATE TABLE product_vehicles"))
    await db.commit()
    print("✅ Таблица очищена!")
    
    # 2. ПОЛУЧАЕМ ТОВАРЫ
    result = await db.execute(text("SELECT id, name, part_number, manufacturer FROM products ORDER BY id"))
    products = result.fetchall()
    print(f"📦 Товаров: {len(products)}")
    
    # 3. ПОЛУЧАЕМ ID МАШИН ПО МАРКАМ (ДИНАМИЧЕСКИ!)
    make_ids = {}
    all_vehicle_ids = []
    
    # Все американские марки
    american_makes = ['RAM', 'Dodge', 'Jeep', 'Chrysler', 'Hummer', 'Cadillac', 'Chevrolet', 'GMC', 'Lincoln']
    
    for make in american_makes:
        result = await db.execute(text(f"SELECT id FROM vehicles WHERE make = '{make}'"))
        ids = [row[0] for row in result.fetchall()]
        make_ids[make.upper()] = ids
        all_vehicle_ids.extend(ids)
    
    print(f"🚗 Машин в базе: {len(all_vehicle_ids)}")
    for make, ids in make_ids.items():
        if ids:
            print(f"  → {make}: {len(ids)} моделей")
    
    UNIVERSAL = ['масло', 'oil', 'жидкость', 'fluid', 'моющ', 'wash', 'свеч', 'spark', 
                 'воздушн', 'air filter', 'салон', 'cabin', 'antifreeze', 'антифриз', 
                 'очистител', 'cleaner', 'присадк', 'additive', 'герметик', 'sealant',
                 'смазка', 'grease', 'brake fluid', 'тормозная жидкость']
    
    # Ключевые слова для марок
    MAKE_KEYWORDS = {
        'RAM': ['RAM', '1500', '2500', '3500', 'TRX'],
        'DODGE': ['DODGE', 'CHALLENGER', 'CHARGER', 'DURANGO'],
        'JEEP': ['JEEP', 'WRANGLER', 'CHEROKEE', 'GLADIATOR', 'COMPASS'],
        'CHRYSLER': ['CHRYSLER', 'PACIFICA', '300'],
        'HUMMER': ['HUMMER', 'H1', 'H2', 'H3'],
        'CADILLAC': ['CADILLAC', 'ESCALADE', 'CTS', 'ATS', 'XT5', 'XT6'],
        'CHEVROLET': ['CHEVROLET', 'CHEVY', 'CAMARO', 'CORVETTE', 'TAHOE', 'SUBURBAN', 'SILVERADO'],
        'GMC': ['GMC', 'SIERRA', 'YUKON', 'CANYON', 'ACADIA'],
        'LINCOLN': ['LINCOLN', 'NAVIGATOR', 'AVIATOR', 'CONTINENTAL'],
    }
    
    # 4. СОБИРАЕМ ВСЕ СВЯЗИ
    all_inserts = []
    
    for pid, name, part_num, manuf in products:
        text_check = f"{name} {part_num or ''} {manuf or ''}".upper()
        
        # Определяем машины
        if any(kw.upper() in text_check for kw in UNIVERSAL):
            vehicle_ids = all_vehicle_ids
        else:
            # Ищем совпадения с ключевыми словами марок
            matched_ids = []
            for make, keywords in MAKE_KEYWORDS.items():
                if any(kw in text_check for kw in keywords):
                    matched_ids.extend(make_ids.get(make, []))
            
            # Если нашли совпадения - используем их, иначе - все машины
            vehicle_ids = matched_ids if matched_ids else all_vehicle_ids
        
        # Добавляем в батч
        for vid in vehicle_ids:
            all_inserts.append(f"({pid},{vid})")
    
    print(f"✅ Подготовлено {len(all_inserts):,} связей")
    
    # 5. МАССОВАЯ ВСТАВКА БАТЧАМИ
    batch_size = 5000
    for i in range(0, len(all_inserts), batch_size):
        batch = all_inserts[i:i+batch_size]
        values = ",".join(batch)
        
        await db.execute(text(f"""
            INSERT INTO product_vehicles (product_id, vehicle_id)
            VALUES {values}
            ON CONFLICT DO NOTHING
        """))
        
        if i % 50000 == 0:
            print(f"  → {i:,} / {len(all_inserts):,}")
    
    await db.commit()
    
    # 6. ПРОВЕРКА
    result = await db.execute(text("SELECT COUNT(*) FROM product_vehicles"))
    count = result.scalar()
    
    print(f"✅ ГОТОВО! Создано связей: {count:,}")
    
    return {
        "success": True,
        "products_count": len(products),
        "links_created": count,
        "message": "🎯 Фильтрация по машинам теперь работает!"
    }


@router.post("/distribute-products-by-categories")
async def distribute_products_by_categories(db: AsyncSession = Depends(get_db)):
    """
    РАСПРЕДЕЛИТЬ ТОВАРЫ ПО КАТЕГОРИЯМ (УМНЫЙ АЛГОРИТМ)
    Извлекает ключевые слова из названий категорий и распределяет товары
    Приоритизирует более специфичные категории (больше совпадений)
    """
    from sqlalchemy import text
    import re
    
    print("🗂️ УМНОЕ РАСПРЕДЕЛЕНИЕ ТОВАРОВ ПО КАТЕГОРИЯМ - СТАРТ!")
    
    # 1. Получаем все товары
    result = await db.execute(text("SELECT id, name, part_number, manufacturer FROM products"))
    products = result.fetchall()
    print(f"📦 Товаров: {len(products)}")
    
    # 2. Получаем все категории с parent_id для определения приоритета
    result = await db.execute(text("SELECT id, name, slug, parent_id FROM categories ORDER BY parent_id DESC"))
    categories = result.fetchall()
    print(f"📁 Категорий: {len(categories)}")
    
    # СТОП-СЛОВА (игнорируем при извлечении ключевых слов)
    STOP_WORDS = {
        'и', 'в', 'на', 'с', 'для', 'по', 'к', 'из', 'от', 'у', 'о', 
        'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'to', 'of', 'in'
    }
    
    def extract_keywords(text: str) -> list:
        """Извлекает ключевые слова из текста (без стоп-слов)"""
        # Убираем спецсимволы, оставляем только буквы и цифры
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Разбиваем на слова
        words = clean_text.split()
        # Фильтруем стоп-слова и короткие слова (меньше 3 символов)
        keywords = [w for w in words if w not in STOP_WORDS and len(w) >= 3]
        return keywords
    
    # 3. Подготавливаем категории с ключевыми словами
    category_data = []
    for cat_id, cat_name, cat_slug, parent_id in categories:
        # Извлекаем ключевые слова из названия и slug
        keywords = extract_keywords(f"{cat_name} {cat_slug}")
        
        # Определяем уровень вложенности (подкатегории = более специфичные)
        depth = 0
        if parent_id is not None:
            depth = 1  # Подкатегория
        
        category_data.append({
            'id': cat_id,
            'name': cat_name,
            'keywords': keywords,
            'depth': depth,  # Чем больше глубина, тем выше приоритет
            'keyword_count': len(keywords)
        })
    
    print(f"✅ Подготовлено {len(category_data)} категорий с ключевыми словами")
    
    # 4. Распределяем товары
    updates = []
    distributed = 0
    not_distributed = 0
    
    for pid, name, part_num, manuf in products:
        # Извлекаем ключевые слова из товара
        product_text = f"{name} {part_num or ''} {manuf or ''}"
        product_keywords = set(extract_keywords(product_text))
        
        # Ищем лучшую категорию
        best_match = None
        best_score = 0
        
        for cat in category_data:
            # Считаем совпадения ключевых слов
            matches = sum(1 for kw in cat['keywords'] if kw in product_keywords)
            
            if matches > 0:
                # Вычисляем score:
                # - Количество совпадений (главный фактор)
                # - Глубина вложенности (подкатегории приоритетнее)
                # - Процент покрытия ключевых слов категории
                coverage = matches / len(cat['keywords']) if cat['keywords'] else 0
                score = (matches * 100) + (cat['depth'] * 10) + (coverage * 5)
                
                if score > best_score:
                    best_score = score
                    best_match = cat['id']
        
        # Если нашли категорию - обновляем
        if best_match:
            updates.append((best_match, pid))
            distributed += 1
        else:
            not_distributed += 1
    
    print(f"✅ Распределено: {distributed}")
    print(f"⚠️ Не распределено: {not_distributed}")
    
    # 5. Применяем обновления батчами
    if updates:
        batch_size = 1000
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            
            # Используем CASE для batch update
            cases = []
            product_ids = []
            for cat_id, prod_id in batch:
                cases.append(f"WHEN {prod_id} THEN {cat_id}")
                product_ids.append(str(prod_id))
            
            if cases:
                await db.execute(text(f"""
                    UPDATE products 
                    SET category_id = CASE id
                        {' '.join(cases)}
                    END
                    WHERE id IN ({','.join(product_ids)})
                """))
        
        await db.commit()
    
    print(f"✅ ГОТОВО! Обновлено товаров: {distributed}")
    
    return {
        "success": True,
        "products_total": len(products),
        "distributed": distributed,
        "not_distributed": not_distributed,
        "message": f"🎯 Умное распределение завершено! Распределено: {distributed}, Не распределено: {not_distributed}"
    }


# ============ КАТЕГОРИИ ============

@router.get("/categories", response_model=List[schemas.Category])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """Получить все категории (плоский список)"""
    result = await db.execute(select(models.Category).order_by(models.Category.name))
    return result.scalars().all()


@router.get("/categories/tree")
async def get_categories_tree(db: AsyncSession = Depends(get_db)):
    """Получить дерево категорий (отсортировано по алфавиту)"""
    # Загружаем все категории СОРТИРОВАННЫЕ ПО АЛФАВИТУ
    result = await db.execute(
        select(models.Category).order_by(models.Category.name)
    )
    all_categories = result.scalars().all()
    
    # Строим дерево вручную
    cat_dict = {}
    for cat in all_categories:
        cat_dict[cat.id] = {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "image_url": cat.image_url,
            "parent_id": cat.parent_id,
            "children": []
        }
    
    # Собираем дерево
    root_cats = []
    for cat in all_categories:
        if cat.parent_id is None:
            root_cats.append(cat_dict[cat.id])
        elif cat.parent_id in cat_dict:
            cat_dict[cat.parent_id]["children"].append(cat_dict[cat.id])
    
    # Сортируем корневые категории по алфавиту
    root_cats.sort(key=lambda x: x["name"])
    
    # Сортируем подкатегории внутри каждой корневой
    for cat in root_cats:
        cat["children"].sort(key=lambda x: x["name"])
    
    return root_cats


@router.post("/categories", response_model=schemas.Category)
async def create_category(
    category: schemas.CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать категорию"""
    # Проверяем уникальность slug
    existing = await db.execute(
        select(models.Category).where(models.Category.slug == category.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Категория с таким slug уже существует")
    
    db_category = models.Category(
        name=category.name,
        slug=category.slug,
        parent_id=category.parent_id,
        image_url=category.image_url
    )
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.put("/categories/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: int,
    category_data: schemas.CategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить категорию"""
    result = await db.execute(
        select(models.Category).where(models.Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    # Проверяем slug на уникальность если меняется
    if category_data.slug and category_data.slug != category.slug:
        existing = await db.execute(
            select(models.Category).where(models.Category.slug == category_data.slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Категория с таким slug уже существует")
    
    # Обновляем только переданные поля
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.slug is not None:
        category.slug = category_data.slug
    if category_data.parent_id is not None:
        category.parent_id = category_data.parent_id if category_data.parent_id != 0 else None
    if category_data.image_url is not None:
        category.image_url = category_data.image_url
    
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить категорию"""
    result = await db.execute(
        select(models.Category).where(models.Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    # Проверяем есть ли товары в категории
    products_result = await db.execute(
        select(models.Product).where(models.Product.category_id == category_id).limit(1)
    )
    if products_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Нельзя удалить категорию с товарами. Сначала переместите товары."
        )
    
    await db.delete(category)
    await db.commit()
    return {"status": "ok", "message": "Категория удалена"}


# ============ ВИТРИНА ============

class FeaturedProductRequest(BaseModel):
    product_id: int
    is_featured: bool
    display_order: Optional[int] = 0


@router.get("/showcase")
async def get_showcase_products(db: AsyncSession = Depends(get_db)):
    """Получить товары витрины"""
    result = await db.execute(
        select(models.Product)
        .where(models.Product.is_featured == True)
        .order_by(models.Product.display_order, models.Product.id)
    )
    products = result.scalars().all()
    
    return [{
        "id": p.id,
        "name": p.name,
        "part_number": p.part_number,
        "price_rub": p.price_rub,
        "image_url": p.image_url,
        "display_order": p.display_order,
        "is_featured": p.is_featured,
        "category_id": p.category_id
    } for p in products]


@router.post("/showcase/add")
async def add_to_showcase(
    request: FeaturedProductRequest,
    db: AsyncSession = Depends(get_db)
):
    """Добавить товар на витрину"""
    result = await db.execute(
        select(models.Product).where(models.Product.id == request.product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    product.is_featured = request.is_featured
    product.display_order = request.display_order
    
    await db.commit()
    return {"status": "ok", "message": "Товар обновлён на витрине"}


@router.post("/showcase/reorder")
async def reorder_showcase(
    products: List[dict],  # [{"id": 1, "display_order": 0}, ...]
    db: AsyncSession = Depends(get_db)
):
    """Изменить порядок товаров на витрине"""
    for item in products:
        result = await db.execute(
            select(models.Product).where(models.Product.id == item["id"])
        )
        product = result.scalar_one_or_none()
        if product:
            product.display_order = item.get("display_order", 0)
    
    await db.commit()
    return {"status": "ok", "message": "Порядок обновлён"}


@router.delete("/showcase/{product_id}")
async def remove_from_showcase(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Убрать товар с витрины"""
    result = await db.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    product.is_featured = False
    product.display_order = 0
    
    await db.commit()
    return {"status": "ok", "message": "Товар убран с витрины"}


# ============ СТАТИСТИКА ============

@router.get("/stats")
async def get_admin_stats(db: AsyncSession = Depends(get_db)):
    """Общая статистика для админки"""
    from sqlalchemy import func
    
    # Количество товаров
    products_count = await db.execute(select(func.count(models.Product.id)))
    
    # Количество категорий
    categories_count = await db.execute(select(func.count(models.Category.id)))
    
    # Количество заказов
    orders_count = await db.execute(select(func.count(models.Order.id)))
    
    # Количество партнеров
    sellers_count = await db.execute(select(func.count(models.Seller.id)))
    
    # Товары на витрине
    featured_count = await db.execute(
        select(func.count(models.Product.id)).where(models.Product.is_featured == True)
    )
    
    return {
        "total_products": products_count.scalar(),
        "total_categories": categories_count.scalar(),
        "total_orders": orders_count.scalar(),
        "total_sellers": sellers_count.scalar(),
        "featured_products": featured_count.scalar()
    }


# ============ ИМПОРТ ТОВАРОВ ИЗ EXCEL ============

@router.post("/import-products")
async def import_products_from_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    ИМПОРТ ТОВАРОВ ИЗ EXCEL/CSV
    Поддерживает умное распределение по категориям
    """
    from sqlalchemy import text
    import re
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")
    
    # Проверяем расширение
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        raise HTTPException(status_code=400, detail="Только .xlsx или .csv файлы")
    
    try:
        # Читаем файл
        contents = await file.read()
        
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            df = pd.read_csv(io.BytesIO(contents))
        
        # Проверяем обязательные колонки
        required = ['name', 'part_number', 'price_rub']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise HTTPException(
                status_code=400, 
                detail=f"Отсутствуют обязательные колонки: {', '.join(missing)}"
            )
        
        # Получаем все категории для сопоставления
        result = await db.execute(text("SELECT id, name, slug, parent_id FROM categories"))
        categories = result.fetchall()
        cat_name_to_id = {cat[1].lower().strip(): cat[0] for cat in categories}
        
        print(f"📊 Импорт из {file.filename}: {len(df)} строк")
        print(f"📁 Категорий в базе: {len(categories)}")
        
        # Функция извлечения ключевых слов
        STOP_WORDS = {'и', 'в', 'на', 'с', 'для', 'по', 'к', 'из', 'от', 'у', 'о'}
        
        def extract_keywords(text: str) -> list:
            clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
            words = clean_text.split()
            return [w for w in words if w not in STOP_WORDS and len(w) >= 3]
        
        # Подготавливаем категории с keywords
        category_data = []
        for cat_id, cat_name, cat_slug, parent_id in categories:
            keywords = extract_keywords(f"{cat_name} {cat_slug}")
            category_data.append({
                'id': cat_id,
                'name': cat_name,
                'keywords': keywords,
                'depth': 1 if parent_id else 0
            })
        
        # Статистика
        created = 0
        skipped = 0
        errors = []
        
        # Обрабатываем каждую строку
        for idx, row in df.iterrows():
            try:
                name = str(row['name']).strip()
                part_number = str(row['part_number']).strip()
                price_rub = float(row['price_rub'])
                
                if not name or not part_number or price_rub <= 0:
                    errors.append(f"Строка {idx + 2}: пропущены обязательные поля")
                    skipped += 1
                    continue
                
                # Проверяем дубликат
                check = await db.execute(
                    text("SELECT id FROM products WHERE part_number = :pn"),
                    {"pn": part_number}
                )
                if check.scalar():
                    errors.append(f"Строка {idx + 2}: артикул {part_number} уже существует")
                    skipped += 1
                    continue
                
                # Определяем категорию
                category_id = None
                
                # Способ 1: Прямое указание category_name
                if 'category_name' in df.columns and pd.notna(row['category_name']):
                    cat_name = str(row['category_name']).lower().strip()
                    category_id = cat_name_to_id.get(cat_name)
                
                # Способ 2: Умный поиск по ключевым словам
                if not category_id:
                    product_text = f"{name} {part_number} {row.get('manufacturer', '')}"
                    product_keywords = set(extract_keywords(product_text))
                    
                    best_match = None
                    best_score = 0
                    
                    for cat in category_data:
                        matches = sum(1 for kw in cat['keywords'] if kw in product_keywords)
                        if matches > 0:
                            coverage = matches / len(cat['keywords']) if cat['keywords'] else 0
                            score = (matches * 100) + (cat['depth'] * 10) + (coverage * 5)
                            if score > best_score:
                                best_score = score
                                best_match = cat['id']
                    
                    category_id = best_match or 1  # Default fallback
                
                # Собираем данные товара
                product_data = {
                    'name': name,
                    'part_number': part_number,
                    'price_rub': price_rub,
                    'category_id': category_id,
                    'stock_quantity': int(row.get('stock_quantity', 0)) if pd.notna(row.get('stock_quantity')) else 0,
                    'manufacturer': str(row.get('manufacturer', '')).strip() if pd.notna(row.get('manufacturer')) else None,
                    'image_url': str(row.get('image_url', '')).strip() if pd.notna(row.get('image_url')) else None,
                    'is_in_stock': bool(row.get('is_in_stock', True)) if pd.notna(row.get('is_in_stock')) else True,
                    'is_installment_available': bool(row.get('is_installment_available', False)) if pd.notna(row.get('is_installment_available')) else False,
                    'description': str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                    'images': [],
                    'price_usd': None,
                    'is_preorder': False
                }
                
                # Создаём товар
                db_product = models.Product(**product_data)
                db.add(db_product)
                created += 1
                
            except Exception as e:
                errors.append(f"Строка {idx + 2}: {str(e)}")
                skipped += 1
        
        # Сохраняем все товары
        await db.commit()
        
        print(f"✅ Создано: {created}")
        print(f"⚠️ Пропущено: {skipped}")
        
        return {
            "success": True,
            "total_rows": len(df),
            "created": created,
            "skipped": skipped,
            "errors": errors[:20],  # Первые 20 ошибок
            "message": f"✅ Импорт завершён! Создано: {created}, Пропущено: {skipped}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки файла: {str(e)}")

