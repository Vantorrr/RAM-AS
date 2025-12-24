"""
Автоматическая привязка товаров к машинам
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Product, Vehicle, product_vehicles
import re

# Database URL from environment or Railway internal
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:fqlwKmEgqVVRLqTNXiZDlslQajvhAZrj@postgres.railway.internal:5432/railway")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("🚀 Загружаю данные...")

# Получаем все товары и машины
products = db.query(Product).all()
vehicles = db.query(Vehicle).all()

print(f"📦 Товаров: {len(products)}")
print(f"🚗 Машин: {len(vehicles)}")

# Группируем машины по маркам
vehicles_by_make = {}
for v in vehicles:
    if v.make not in vehicles_by_make:
        vehicles_by_make[v.make] = []
    vehicles_by_make[v.make].append(v)

# Универсальные категории (подходят всем)
UNIVERSAL_KEYWORDS = [
    'масло', 'жидкость', 'антифриз', 'тосол', 'омывайка', 
    'аксессуар', 'ароматизатор', 'коврик', 'чехол', 'органайзер',
    'держатель', 'зарядное', 'usb', 'видеорегистратор', 'радар',
    'компрессор', 'насос', 'инструмент', 'ключ', 'домкрат',
    'трос', 'аптечка', 'огнетушитель', 'знак', 'жилет',
    'щетка', 'скребок', 'губка', 'салфетка', 'полироль',
    'шампунь', 'воск', 'полотенце', 'перчатки', 'маска',
]

# Американские марки (для RAM и подобных)
AMERICAN_MAKES = ['RAM', 'Dodge', 'Jeep', 'Chevrolet', 'Ford', 'GMC', 'Cadillac', 'Lincoln', 'Chrysler']

def is_universal(product_name, category_name=None):
    """Проверяет, является ли товар универсальным"""
    text = (product_name + ' ' + (category_name or '')).lower()
    return any(keyword in text for keyword in UNIVERSAL_KEYWORDS)

def get_matching_makes(product_name, category_name=None):
    """Определяет марки машин по названию товара"""
    text = (product_name + ' ' + (category_name or '')).lower()
    
    # Проверяем упоминания конкретных марок
    matches = []
    
    # RAM, Dodge, Jeep
    if any(word in text for word in ['ram', 'рам', 'dodge', 'додж', 'jeep', 'джип', 'hemi', 'хеми', 'trx']):
        matches.extend(['RAM', 'Dodge', 'Jeep'])
    
    # BMW
    if any(word in text for word in ['bmw', 'бмв']):
        matches.append('BMW')
    
    # Mercedes
    if any(word in text for word in ['mercedes', 'мерседес', 'benz', 'бенц']):
        matches.append('Mercedes-Benz')
    
    # Audi
    if any(word in text for word in ['audi', 'ауди']):
        matches.append('Audi')
    
    # Toyota
    if any(word in text for word in ['toyota', 'тойота', 'camry', 'камри', 'land cruiser', 'крузер']):
        matches.append('Toyota')
    
    # Lada
    if any(word in text for word in ['lada', 'лада', 'ваз', 'granta', 'гранта', 'vesta', 'веста', 'приора', 'калина']):
        matches.append('Lada')
    
    # Volkswagen
    if any(word in text for word in ['volkswagen', 'vw', 'фольксваген', 'polo', 'поло', 'tiguan', 'тигуан']):
        matches.append('Volkswagen')
    
    # Hyundai
    if any(word in text for word in ['hyundai', 'хендай', 'хундай', 'solaris', 'солярис', 'creta', 'крета']):
        matches.append('Hyundai')
    
    # Kia
    if any(word in text for word in ['kia', 'киа', 'rio', 'рио', 'sportage', 'спортаж']):
        matches.append('Kia')
    
    # Renault
    if any(word in text for word in ['renault', 'рено', 'duster', 'дастер', 'logan', 'логан']):
        matches.append('Renault')
    
    # Nissan
    if any(word in text for word in ['nissan', 'ниссан', 'qashqai', 'кашкай', 'x-trail', 'икстрейл']):
        matches.append('Nissan')
    
    # Ford
    if any(word in text for word in ['ford', 'форд', 'focus', 'фокус', 'explorer', 'эксплорер']):
        matches.append('Ford')
    
    # Chevrolet
    if any(word in text for word in ['chevrolet', 'шевроле', 'cruze', 'круз', 'tahoe', 'тахо']):
        matches.append('Chevrolet')
    
    return list(set(matches))

print("\n🔗 Начинаю привязку товаров к машинам...\n")

linked_count = 0
universal_count = 0
specific_count = 0

for product in products:
    # Очищаем старые связи
    db.execute(product_vehicles.delete().where(product_vehicles.c.product_id == product.id))
    
    category_name = product.category.name if product.category else None
    
    # Проверяем, универсальный ли товар
    if is_universal(product.name, category_name):
        # Привязываем ко ВСЕМ машинам
        product.vehicles = vehicles
        universal_count += 1
        print(f"🌍 УНИВЕРСАЛЬНЫЙ: {product.name} → ВСЕ {len(vehicles)} машин")
    else:
        # Определяем конкретные марки
        matching_makes = get_matching_makes(product.name, category_name)
        
        if matching_makes:
            # Привязываем к конкретным маркам
            matched_vehicles = []
            for make in matching_makes:
                if make in vehicles_by_make:
                    matched_vehicles.extend(vehicles_by_make[make])
            
            product.vehicles = matched_vehicles
            specific_count += 1
            print(f"🎯 СПЕЦИФИЧНЫЙ: {product.name} → {matching_makes} ({len(matched_vehicles)} моделей)")
        else:
            # Если не определили - привязываем ко всем (на всякий случай)
            product.vehicles = vehicles
            universal_count += 1
            print(f"❓ НЕ ОПРЕДЕЛЕНО (→ всем): {product.name}")
    
    linked_count += 1

db.commit()
db.close()

print(f"\n✅ ГОТОВО!")
print(f"📊 Обработано товаров: {linked_count}")
print(f"🌍 Универсальных: {universal_count}")
print(f"🎯 Специфичных: {specific_count}")
print(f"🚗 Всего машин в базе: {len(vehicles)}")

