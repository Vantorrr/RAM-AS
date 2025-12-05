"""
Скрипт для автоматического распределения товаров по категориям
на основе ключевых слов в названии товара
"""
import asyncio
from sqlalchemy import select, update
from app.database import SessionLocal
from app.models import Product, Category

# Ключевые слова для категорий
CATEGORY_KEYWORDS = {
    # Детали для ТО
    "Фильтр масляный": ["фильтр масл", "oil filter", "масляный фильтр"],
    "Фильтр воздушный": ["фильтр воздуш", "air filter", "воздушный фильтр"],
    "Фильтр салонный": ["фильтр салон", "cabin filter", "салонный фильтр"],
    "Фильтр трансмиссионный, фильтр ГУР": ["фильтр трансмисс", "фильтр гур", "transmission filter"],
    "Свечи зажигания": ["свеч", "spark plug"],
    "Ремень приводной": ["ремень", "belt", "приводн"],
    "Насос системы охлаждения": ["помпа", "водяной насос", "water pump"],
    "Термостат": ["термостат", "thermostat"],
    "Колодки тормозные": ["колодк", "brake pad", "тормозн"],
    "Пробка сливного отверстия": ["пробка", "drain plug", "сливн"],
    "Щетки стеклоочистителя": ["щетк", "wiper", "дворник"],
    
    # Двигатель
    "Поршни и кольца": ["поршень", "поршн", "кольц", "piston", "ring"],
    "Прокладки ГБЦ": ["прокладк", "gasket", "гбц"],
    "Цепь / ремень ГРМ": ["цепь грм", "ремень грм", "timing"],
    "Клапаны": ["клапан", "valve"],
    "Распредвал": ["распредвал", "camshaft"],
    "Коленвал": ["коленвал", "crankshaft"],
    "Маслосъемные колпачки": ["маслосъем", "колпач", "seal"],
    
    # Топливная система  
    "Форсунки": ["форсунк", "injector"],
    "Топливный насос": ["топливный насос", "fuel pump", "бензонасос"],
    "Топливный фильтр": ["топливный фильтр", "fuel filter"],
    
    # Система охлаждения
    "Радиатор": ["радиатор", "radiator"],
    "Вентилятор охлаждения": ["вентилятор", "fan", "охлажд"],
    "Патрубки": ["патруб", "hose", "шланг охлажд"],
    
    # Система выпуска
    "Глушитель": ["глушител", "muffler", "exhaust"],
    "Катализатор": ["катализатор", "catalyst", "converter"],
    "Выпускной коллектор": ["коллектор", "manifold"],
    
    # Трансмиссия
    "АКПП": ["акпп", "automatic", "автомат"],
    "МКПП": ["мкпп", "manual", "механик"],
    "Сцепление": ["сцеплен", "clutch"],
    "Кардан": ["кардан", "driveshaft", "shaft"],
    "Раздаточная коробка": ["раздат", "transfer case"],
    "Редуктор": ["редуктор", "differential"],
    
    # Ходовая часть
    "Амортизаторы": ["амортизатор", "shock", "стойк"],
    "Пружины": ["пружин", "spring", "coil"],
    "Рычаги": ["рычаг", "arm", "control arm"],
    "Шаровые опоры": ["шаров", "ball joint"],
    "Сайлентблоки": ["сайлентблок", "сайлент", "bushing", "втулк"],
    "Ступицы": ["ступиц", "hub", "подшипник ступ"],
    
    # Рулевое управление
    "Рулевая рейка": ["рулев", "рейк", "steering", "rack"],
    "Наконечники": ["наконечник", "tie rod"],
    "Насос ГУР": ["насос гур", "power steering pump"],
    
    # Тормозная система
    "Тормозные диски": ["диск тормоз", "brake disc", "brake rotor", "тормозной диск"],
    "Тормозные суппорты": ["суппорт", "caliper"],
    "Тормозные шланги": ["тормозной шланг", "brake hose", "brake line"],
    "Главный тормозной цилиндр": ["главный тормоз", "master cylinder"],
    
    # Электрооборудование
    "Генератор": ["генератор", "alternator"],
    "Стартер": ["стартер", "starter"],
    "Аккумулятор": ["аккумулятор", "battery", "акб"],
    "Датчики": ["датчик", "sensor"],
    "Фары": ["фар", "headlight", "headlamp", "light"],
    "Проводка": ["провод", "wire", "harness", "жгут"],
    
    # Отопление / кондиционирование
    "Компрессор кондиционера": ["компрессор", "compressor", "кондиционер"],
    "Радиатор печки": ["радиатор печк", "heater core"],
    "Мотор печки": ["мотор печк", "blower"],
    
    # Детали кузова
    "Бампер": ["бампер", "bumper"],
    "Капот": ["капот", "hood"],
    "Крыло": ["крыл", "fender"],
    "Дверь": ["двер", "door"],
    "Зеркало": ["зеркал", "mirror"],
    
    # Тюнинг
    "Системы холодного впуска": ["холодн", "впуск", "cold air", "intake"],
    "Освещение": ["led", "лед", "свет", "подсветк"],
}

async def distribute_products():
    async with SessionLocal() as db:
        # Получаем все категории
        result = await db.execute(select(Category))
        categories = result.scalars().all()
        cat_by_name = {cat.name: cat.id for cat in categories}
        
        print(f"Найдено {len(categories)} категорий")
        
        # Получаем все товары
        result = await db.execute(select(Product))
        products = result.scalars().all()
        
        print(f"Найдено {len(products)} товаров")
        
        updated = 0
        
        for product in products:
            product_name_lower = product.name.lower()
            product_desc_lower = (product.description or "").lower()
            
            matched_category = None
            
            # Ищем совпадение по ключевым словам
            for cat_name, keywords in CATEGORY_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in product_name_lower or keyword.lower() in product_desc_lower:
                        if cat_name in cat_by_name:
                            matched_category = cat_by_name[cat_name]
                            break
                if matched_category:
                    break
            
            # Если нашли категорию - обновляем
            if matched_category and product.category_id != matched_category:
                product.category_id = matched_category
                updated += 1
                
                if updated % 500 == 0:
                    print(f"Обновлено {updated} товаров...")
        
        await db.commit()
        print(f"\n✅ Готово! Обновлено {updated} товаров")

if __name__ == "__main__":
    asyncio.run(distribute_products())



