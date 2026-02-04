import os
import json
import aiohttp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from sqlalchemy import select, or_
from app.database import SessionLocal
from app import models
from aiogram import Bot
from app.bot import notify_new_order
from datetime import datetime

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_IDS", "").split(",")

# Имя бота для deep links (формат: @bot_username без @)
BOT_USERNAME = os.getenv("BOT_USERNAME", "ram_us_bot")

class Message(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    name: Optional[str] = None

class UserInfo(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[Message]
    user_info: Optional[UserInfo] = None

SYSTEM_PROMPT_CONTENT = """
Ты — дружелюбный консультант магазина "RAM US Auto Parts" 🇺🇸
Специализация: запчасти для американских авто (RAM, Dodge, Jeep, Ford, Chevrolet, GMC, Cadillac, Lincoln, Hummer).

🎯 ТВОЯ ЦЕЛЬ: ПОМОЧЬ КЛИЕНТУ НАЙТИ ЗАПЧАСТЬ!

📋 КАК РАБОТАТЬ:

1️⃣ КЛИЕНТ СПРАШИВАЕТ О ЗАПЧАСТИ:
   → Сразу вызывай search_auto_parts! Даже если не указал авто!
   → Поиск умный — найдет по названию
   → Если клиент указал авто — отлично, результаты будут точнее

2️⃣ НИЧЕГО НЕ НАЙДЕНО?
   → Предложи альтернативы или синонимы
   → Уточни название запчасти (колодки → тормозные колодки)
   → ВСЕГДА предлагай позвать менеджера — он найдёт что угодно!

3️⃣ НАШЛИСЬ ТОВАРЫ?
   → Покажи клиенту красиво со ссылками
   → Спроси — оформляем заказ?

🛠️ ИНСТРУМЕНТЫ:

• search_auto_parts(query) — умный поиск
  Примеры: "колодки", "фильтр воздушный RAM", "амортизаторы Jeep 2020"
  
• create_order — оформить заказ (спроси телефон)

• notify_manager — ОБЯЗАТЕЛЬНО вызывай если:
  - Товар не найден
  - Сложный случай  
  - Клиент просит редкую запчасть
  - Нужна консультация

📝 ФОРМАТ ОТВЕТА:

Нашёл для вас! 🚗

🔹 Название товара — 8 500 ₽ ✅ В наличии
   👉 [ссылка]

🔹 Ещё вариант — 7 200 ₽ ⏱️ Под заказ
   👉 [ссылка]

Нажмите на ссылку — увидите фото и описание!
Оформить заказ?

⚡ ВАЖНЫЕ ПРАВИЛА:
- ВСЕГДА пробуй поиск — он умный!
- Ссылки на товары ОБЯЗАТЕЛЬНЫ
- Если 0 результатов — notify_manager, не бросай клиента!
- Будь полезным и дружелюбным 😊
"""

# --- Tools Definitions ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_auto_parts",
            "description": "Поиск автозапчастей в БД. Возвращает ID товаров, цены и наличие.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос (название, артикул)."
                    },
                    "vin": {
                        "type": "string",
                        "description": "VIN-номер авто (если указан)."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": "Создание реального заказа в базе данных.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "integer"},
                                "quantity": {"type": "integer"}
                            },
                            "required": ["product_id", "quantity"]
                        },
                        "description": "Список товаров для покупки"
                    },
                    "address": {
                        "type": "string",
                        "description": "Адрес доставки или город"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Телефон клиента"
                    },
                    "name": {
                        "type": "string",
                        "description": "Имя клиента"
                    }
                },
                "required": ["items", "phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notify_manager",
            "description": "Позвать живого менеджера (для товаров 'под заказ' или вопросов).",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Суть запроса."
                    },
                    "contact_info": {
                        "type": "string",
                        "description": "Контакты клиента."
                    }
                },
                "required": ["message"]
            }
        }
    }
]

# --- Tool Implementations ---

# Словарь марок авто для парсинга запросов
VEHICLE_MAKES = {
    "ram": "RAM", "рам": "RAM", "рэм": "RAM",
    "dodge": "Dodge", "додж": "Dodge",
    "jeep": "Jeep", "джип": "Jeep",
    "chrysler": "Chrysler", "крайслер": "Chrysler",
    "ford": "Ford", "форд": "Ford",
    "chevrolet": "Chevrolet", "шевроле": "Chevrolet", "шеви": "Chevrolet",
    "gmc": "GMC", "джиэмси": "GMC",
    "cadillac": "Cadillac", "кадиллак": "Cadillac",
    "hummer": "Hummer", "хаммер": "Hummer",
    "lincoln": "Lincoln", "линкольн": "Lincoln",
}

def parse_vehicle_from_query(query: str) -> dict:
    """Извлекает марку, модель и год из поискового запроса."""
    query_lower = query.lower()
    result = {"make": None, "model": None, "year": None, "part_query": query}
    
    # Ищем марку
    for key, make in VEHICLE_MAKES.items():
        if key in query_lower:
            result["make"] = make
            break
    
    # Ищем год (4 цифры от 1990 до 2030)
    import re
    year_match = re.search(r'\b(19[9]\d|20[0-3]\d)\b', query)
    if year_match:
        result["year"] = int(year_match.group(1))
    
    # Ищем модель (1500, 2500, F-150, и т.д.)
    model_patterns = [
        r'\b(1500|2500|3500|4500|5500)\b',  # RAM trucks
        r'\b(f-?150|f-?250|f-?350)\b',  # Ford F-series
        r'\b(silverado|tahoe|suburban|escalade|navigator)\b',
        r'\b(wrangler|cherokee|grand cherokee|compass|renegade)\b',
        r'\b(challenger|charger|durango)\b',
    ]
    for pattern in model_patterns:
        match = re.search(pattern, query_lower)
        if match:
            result["model"] = match.group(1).upper().replace("-", "-")
            break
    
    # Удаляем найденные элементы из запроса для поиска запчасти
    part_query = query_lower
    if result["make"]:
        for key in VEHICLE_MAKES.keys():
            part_query = part_query.replace(key, "")
    if result["year"]:
        part_query = part_query.replace(str(result["year"]), "")
    if result["model"]:
        part_query = re.sub(result["model"].lower().replace("-", "-?"), "", part_query)
    
    result["part_query"] = part_query.strip()
    
    return result

async def search_auto_parts(query: str, vin: str = None) -> str:
    """Умный поиск запчастей в БД — ищет по словам, с fallback и подсказками."""
    print(f"🔎 [AI Tool] Searching parts: query='{query}', VIN='{vin}'")
    
    # Парсим запрос
    parsed = parse_vehicle_from_query(query)
    print(f"📋 Parsed query: {parsed}")
    
    # Извлекаем ключевые слова для поиска (минимум 2 буквы)
    import re
    stop_words = {"на", "для", "в", "и", "или", "с", "по", "от", "до", "нужны", "нужен", "нужна", "хочу", "ищу", "мне", "бы"}
    all_words = re.findall(r'[а-яёa-z0-9]+', query.lower())
    search_words = [w for w in all_words if len(w) >= 2 and w not in stop_words]
    
    # Убираем марки/модели/годы из поисковых слов
    for make_key in VEHICLE_MAKES.keys():
        if make_key in search_words:
            search_words.remove(make_key)
    if parsed["year"] and str(parsed["year"]) in search_words:
        search_words.remove(str(parsed["year"]))
    if parsed["model"]:
        model_lower = parsed["model"].lower()
        search_words = [w for w in search_words if w != model_lower]
    
    print(f"🔤 Search words: {search_words}")
    
    try:
        async with SessionLocal() as db:
            products = []
            search_method = ""
            
            # СТРАТЕГИЯ 1: Поиск по совместимости с авто + название запчасти
            if parsed["make"] or parsed["year"]:
                vehicle_query = select(models.Vehicle)
                
                if parsed["make"]:
                    vehicle_query = vehicle_query.where(models.Vehicle.make == parsed["make"])
                
                if parsed["year"]:
                    vehicle_query = vehicle_query.where(
                        models.Vehicle.year_from <= parsed["year"],
                        or_(
                            models.Vehicle.year_to >= parsed["year"],
                            models.Vehicle.year_to.is_(None)
                        )
                    )
                
                vehicle_result = await db.execute(vehicle_query)
                vehicles = vehicle_result.scalars().all()
                vehicle_ids = [v.id for v in vehicles]
                
                print(f"🚗 Found {len(vehicle_ids)} matching vehicles")
                
                if vehicle_ids:
                    from sqlalchemy import text as sql_text
                    ids_str = ",".join(str(id) for id in vehicle_ids[:100])
                    
                    try:
                        # Ищем товары совместимые с авто, которые содержат ЛЮБОЕ из слов запроса
                        if search_words:
                            word_conditions = " OR ".join([f"(p.name ILIKE '%{w}%' OR p.description ILIKE '%{w}%')" for w in search_words[:5]])
                            sql = sql_text(f"""
                                SELECT DISTINCT p.id, p.name FROM products p
                                JOIN product_vehicles pv ON p.id = pv.product_id
                                WHERE pv.vehicle_id IN ({ids_str})
                                AND ({word_conditions})
                                LIMIT 10
                            """)
                        else:
                            # Если нет слов для поиска — просто показываем товары для этого авто
                            sql = sql_text(f"""
                                SELECT DISTINCT p.id, p.name FROM products p
                                JOIN product_vehicles pv ON p.id = pv.product_id
                                WHERE pv.vehicle_id IN ({ids_str})
                                LIMIT 10
                            """)
                        
                        result = await db.execute(sql)
                        rows = result.fetchall()
                        print(f"📦 Found {len(rows)} products via vehicle compatibility")
                        
                        if rows:
                            product_ids = [row[0] for row in rows]
                            stmt = select(models.Product).where(models.Product.id.in_(product_ids))
                            result2 = await db.execute(stmt)
                            products = result2.scalars().all()
                            search_method = f"для {parsed['make'] or ''} {parsed['model'] or ''} {parsed['year'] or ''}"
                    except Exception as e:
                        print(f"❌ Vehicle search error: {e}")
                        import traceback
                        traceback.print_exc()
            
            # СТРАТЕГИЯ 2: Текстовый поиск по каждому слову (если нет результатов по авто)
            if not products and search_words:
                from sqlalchemy import text as sql_text
                
                # Ищем товары содержащие ЛЮБОЕ из слов
                word_conditions = " OR ".join([f"(name ILIKE '%{w}%' OR part_number ILIKE '%{w}%' OR description ILIKE '%{w}%')" for w in search_words[:5]])
                sql = sql_text(f"""
                    SELECT id FROM products 
                    WHERE {word_conditions}
                    LIMIT 10
                """)
                
                result = await db.execute(sql)
                rows = result.fetchall()
                print(f"📦 Found {len(rows)} products via word search")
                
                if rows:
                    product_ids = [row[0] for row in rows]
                    stmt = select(models.Product).where(models.Product.id.in_(product_ids))
                    result2 = await db.execute(stmt)
                    products = result2.scalars().all()
                    search_method = "по названию"
            
            # СТРАТЕГИЯ 3: Поиск похожих товаров (если ничего не найдено)
            if not products:
                # Берем первое слово и ищем частичное совпадение
                if search_words:
                    main_word = search_words[0]
                    # Ищем товары где название содержит хотя бы 3 первые буквы слова
                    prefix = main_word[:3] if len(main_word) >= 3 else main_word
                    
                    stmt = select(models.Product).where(
                        or_(
                            models.Product.name.ilike(f"%{prefix}%"),
                            models.Product.description.ilike(f"%{prefix}%")
                        )
                    ).limit(5)
                    
                    result = await db.execute(stmt)
                    similar_products = result.scalars().all()
                    
                    if similar_products:
                        products = similar_products
                        search_method = "похожие товары"
            
            # Формируем ответ
            if not products:
                # Получаем количество товаров в базе для контекста
                count_result = await db.execute(select(models.Product.id))
                total_products = len(count_result.fetchall())
                
                suggestions = []
                if not parsed["make"]:
                    suggestions.append("марку авто")
                if not parsed["year"]:
                    suggestions.append("год выпуска")
                if not parsed["model"]:
                    suggestions.append("модель")
                
                response = f"🔍 По запросу '{query}' ничего не найдено.\n\n"
                response += f"📦 Всего в каталоге: {total_products} товаров\n\n"
                
                if suggestions:
                    response += f"💡 Попробуй уточнить у клиента: {', '.join(suggestions)}\n"
                    response += f"Пример: 'Колодки тормозные', 'Фильтр воздушный', 'Амортизатор'\n\n"
                
                response += "🤝 Если нужной запчасти нет — используй notify_manager, менеджер найдёт!"
                
                return response
            
            # Успешный ответ с товарами
            res = f"✅ Найдено {len(products)} товаров {search_method}:\n\n"
            for p in products:
                price = f"{p.price_rub:,.0f} ₽" if p.price_rub else "Цена по запросу"
                stock = "✅ В наличии" if p.is_in_stock else "⏱️ Под заказ (4-6 нед)"
                
                product_link = f"https://t.me/{BOT_USERNAME}/app?startapp=product_{p.id}"
                
                res += f"🔹 **{p.name}**\n"
                if p.part_number:
                    res += f"   Артикул: {p.part_number}\n"
                res += f"   💰 {price} | {stock}\n"
                res += f"   👉 {product_link}\n"
                res += f"   [ID: {p.id}]\n\n"
            
            res += "💡 Клиент может кликнуть на ссылку чтобы увидеть фото и детали. Для заказа используй create_order."
            print(f"✅ [AI Tool] Search results:\n{res}")
            return res
            
    except Exception as e:
        print(f"❌ DB Search Error: {e}")
        import traceback
        traceback.print_exc()
        return "⚠️ Ошибка при поиске в базе. Попробуй notify_manager — менеджер поможет!"

async def create_order(items: List[Dict[str, int]], address: str = "Не указан", phone: str = "Не указан", name: str = "Клиент", telegram_id: int = None) -> str:
    """Создает заказ в БД."""
    print(f"🛒 [AI Tool] Creating order for {name} ({phone}): {items}")
    print(f"📍 Address: {address}")
    print(f"🆔 Telegram ID: {telegram_id}")
    
    try:
        async with SessionLocal() as db:
            total_amount = 0.0
            order_items_db = []
            
            # 1. Проверяем товары и считаем сумму
            for item in items:
                prod_id = item.get("product_id")
                qty = item.get("quantity", 1)
                
                stmt = select(models.Product).where(models.Product.id == prod_id)
                res = await db.execute(stmt)
                product = res.scalar_one_or_none()
                
                if not product:
                    return f"Ошибка: Товар с ID {prod_id} не найден. Уточните поиск."
                
                price = product.price_rub or 0
                total_amount += price * qty
                
                # Создаем объект позиции заказа (пока не привязан к ID заказа)
                order_items_db.append({
                    "product": product,
                    "quantity": qty,
                    "price": price
                })

            # 2. Создаем заказ
            new_order = models.Order(
                user_telegram_id=str(telegram_id) if telegram_id else None,
                user_name=name,
                user_phone=phone,
                delivery_address=address,
                total_amount=total_amount,
                status="pending"
            )
            db.add(new_order)
            await db.flush() # Получаем ID заказа
            
            order_id = new_order.id  # Сохраняем ID перед commit
            
            # 3. Сохраняем позиции
            for item_data in order_items_db:
                db_item = models.OrderItem(
                    order_id=order_id,
                    product_id=item_data["product"].id,
                    quantity=item_data["quantity"],
                    price_at_purchase=item_data["price"],
                    is_preorder=item_data["product"].is_preorder
                )
                db.add(db_item)
            
            await db.commit()
            
            # 4. Уведомляем админов (как обычный заказ)
            notify_data = {
                "id": order_id,
                "user_name": name,
                "user_phone": phone,
                "delivery_address": address,
                "total_amount": total_amount,
                "items": [
                    {
                        "product_id": i["product"].id,
                        "product_name": i["product"].name,
                        "quantity": i["quantity"],
                        "price_at_purchase": i["price"],
                        "is_preorder": i["product"].is_preorder
                    } for i in order_items_db
                ],
                "created_at": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
        
        # 5. Уведомляем админов ПОСЛЕ закрытия сессии
        try:
            await notify_new_order(notify_data)
        except Exception as e:
            print(f"Notification warning: {e}")
            
        return f"✅ Заказ #{order_id} успешно создан! Сумма: {total_amount} руб. Менеджер скоро свяжется."

    except Exception as e:
        print(f"❌ Create Order Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Уведомляем админов об ошибке
        from app.bot import bot as global_bot
        if global_bot and ADMIN_CHAT_IDS:
            error_text = (
                f"⚠️ <b>Ошибка создания заказа через ИИ</b>\n\n"
                f"👤 <b>Клиент:</b> {name} ({phone})\n"
                f"📦 <b>Товары:</b> {items}\n"
                f"❌ <b>Ошибка:</b> {str(e)[:200]}\n\n"
                f"💡 <i>Свяжитесь с клиентом для оформления заказа вручную!</i>"
            )
            for admin_id in ADMIN_CHAT_IDS:
                try:
                    await global_bot.send_message(
                        chat_id=admin_id.strip(),
                        text=error_text,
                        parse_mode="HTML"
                    )
                except:
                    pass
        
        return f"⚠️ Не удалось автоматически оформить заказ. Я передал вашу заявку менеджеру! Вам позвонят в ближайшее время для уточнения деталей."

async def notify_manager(message: str, contact_info: str = "Не указаны") -> str:
    """Отправляет уведомление в Telegram админу."""
    print(f"🔔 [AI Tool] Notifying manager: {message}")
    if not BOT_TOKEN:
        return "Ошибка: Бот не настроен."
    
    # Используем глобальный бот вместо создания нового
    from app.bot import bot as global_bot
    
    if not global_bot:
        print("❌ Global bot not initialized")
        return "Ошибка: Бот не инициализирован."
    
    text = (
        f"🤖 <b>AI-Ассистент: Заявка от клиента</b>\n\n"
        f"📩 <b>Запрос:</b> {message}\n"
        f"👤 <b>Инфо/VIN:</b> {contact_info}\n"
        f"⚠️ <i>Свяжитесь с клиентом!</i>"
    )
    
    try:
        sent_count = 0
        for chat_id in ADMIN_CHAT_IDS:
            cid = chat_id.strip()
            if cid:
                try:
                    await global_bot.send_message(chat_id=cid, text=text, parse_mode="HTML")
                    sent_count += 1
                    print(f"✅ Notification sent to admin {cid}")
                except Exception as e:
                    print(f"❌ Failed to send to {cid}: {e}")
        
        return "✅ Уведомление отправлено менеджерам. Ожидайте звонка!" if sent_count > 0 else "⚠️ Не удалось отправить уведомление. Попробуйте позвонить по номеру в боте."
    except Exception as e:
        print(f"❌ Notify manager error: {e}")
        return f"⚠️ Ошибка уведомления. Позвоните нам напрямую!"

# --- Main Chat Handler ---

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured")

    clean_key = API_KEY.strip().strip('"').strip("'")
    headers = {
        "Authorization": f"Bearer {clean_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ram-us-webapp.vercel.app", 
        "X-Title": "RAM US Auto Parts",
    }

    messages = [m.dict(exclude_none=True) for m in request.messages]
    
    # Контекст пользователя
    user_id = None
    user_name_ctx = "Клиент"
    
    system_content = SYSTEM_PROMPT_CONTENT
    if request.user_info:
        user_id = request.user_info.id
        if request.user_info.first_name:
            user_name_ctx = request.user_info.first_name
            
        user_details = []
        if request.user_info.first_name: user_details.append(f"Имя: {request.user_info.first_name}")
        if request.user_info.username: user_details.append(f"Telegram: @{request.user_info.username}")
        if request.user_info.id: user_details.append(f"ID: {request.user_info.id}")
            
        if user_details:
            system_content += f"\n\n👤 ИНФОРМАЦИЯ О КЛИЕНТЕ:\n" + "\n".join(user_details)

    if not any(m['role'] == 'system' for m in messages):
        messages.insert(0, {"role": "system", "content": system_content})
    else:
        for m in messages:
            if m['role'] == 'system':
                m['content'] = system_content
                break
    
    # Уведомление админов о начале диалога (только первое сообщение)
    user_messages = [m for m in messages if m.get('role') == 'user']
    if len(user_messages) == 1:
        # Это первое сообщение пользователя
        first_message = user_messages[0].get('content', '')
        
        from app.bot import bot as global_bot
        if global_bot and ADMIN_CHAT_IDS:
            notification_text = (
                f"💬 <b>Новый диалог с AI-ассистентом</b>\n\n"
                f"👤 <b>Клиент:</b> {user_name_ctx}\n"
                f"🆔 <b>Telegram ID:</b> {user_id or 'Неизвестен'}\n"
                f"📝 <b>Первое сообщение:</b>\n{first_message[:200]}{'...' if len(first_message) > 200 else ''}\n\n"
                f"💡 <i>Клиент общается с ИИ-ассистентом</i>"
            )
            
            for admin_id in ADMIN_CHAT_IDS:
                try:
                    await global_bot.send_message(
                        chat_id=admin_id.strip(),
                        text=notification_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"❌ Failed to notify admin {admin_id}: {e}")

    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto"
    }
    
    endpoint = f"{BASE_URL.rstrip('/')}/chat/completions"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=f"AI Provider Error: {text}")
                
                data = await resp.json()
                choice = data["choices"][0]
                ai_msg = choice["message"]
                
                if not ai_msg.get("tool_calls"):
                    return {"role": "assistant", "content": ai_msg["content"]}
                
                tool_calls = ai_msg["tool_calls"]
                messages.append(ai_msg)
                
                for tool_call in tool_calls:
                    func_name = tool_call["function"]["name"]
                    args_str = tool_call["function"]["arguments"]
                    args = json.loads(args_str)
                    
                    print(f"🛠️ Executing tool: {func_name} with args {args}")
                    
                    tool_result = "Неизвестная функция"
                    if func_name == "search_auto_parts":
                        tool_result = await search_auto_parts(
                            query=args.get("query", ""), 
                            vin=args.get("vin")
                        )
                    elif func_name == "notify_manager":
                        tool_result = await notify_manager(
                            message=args.get("message", ""),
                            contact_info=args.get("contact_info", "Не указано")
                        )
                    elif func_name == "create_order":
                        # Если имя не передано явно, берем из контекста Telegram
                        name_arg = args.get("name") or user_name_ctx
                        
                        tool_result = await create_order(
                            items=args.get("items", []),
                            address=args.get("address", "Самовывоз"),
                            phone=args.get("phone", "Не указан"),
                            name=name_arg,
                            telegram_id=user_id
                        )
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(tool_result)
                    })
                
                payload["messages"] = messages
                payload.pop("tool_choice", None)
                
                async with session.post(endpoint, headers=headers, json=payload) as resp2:
                    if resp2.status != 200:
                        error_text = await resp2.text()
                        print(f"❌ AI second call failed: {resp2.status} - {error_text[:200]}")
                        return {"role": "assistant", "content": f"Вот что я нашёл:\n\n{tool_result}"}

                    data2 = await resp2.json()
                    print(f"📤 AI second response: {json.dumps(data2, ensure_ascii=False)[:500]}")
                    
                    final_msg = data2.get("choices", [{}])[0].get("message", {}).get("content")
                    
                    # Если AI вернул пустой контент, формируем ответ сами
                    if not final_msg:
                        print("⚠️ AI returned empty content, using tool result directly")
                        return {"role": "assistant", "content": f"Вот что я нашёл:\n\n{tool_result}"}
                    
                    return {"role": "assistant", "content": final_msg}

        except Exception as e:
            print(f"❌ Chat Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))
