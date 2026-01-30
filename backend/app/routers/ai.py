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
Ты — профессиональный консультант компании "RAM US Auto Parts".

🎯 Твоя миссия:
Помогать клиентам находить автозапчасти, проверять наличие и ОФОРМЛЯТЬ ЗАКАЗЫ.

🛠️ ТВОИ ИНСТРУМЕНТЫ (Tools):
1. `search_auto_parts`: ОБЯЗАТЕЛЬНО вызывай эту функцию, если клиент ищет запчасть. Не отвечай наугад!
   - Функция вернет список товаров с их ID.
2. `create_order`: Вызывай эту функцию, когда клиент согласен купить товар(ы).
   - Спроси у клиента адрес доставки (или город) и телефон, если их нет.
   - Используй ID товара, который ты нашел через `search_auto_parts`.
   - Если клиент покупает несколько товаров, передавай их списком.
3. `notify_manager`: Вызывай, только если клиент хочет нестандартный товар (нет в базе) или просит живого оператора.

📋 Алгоритм продажи:
1. Клиент: "Нужен фильтр" -> Ты: `search_auto_parts("фильтр")`.
2. Результат: "ID: 105 - Фильтр масляный - 1500р".
3. Ты: "Есть масляный фильтр за 1500р. Оформим заказ?"
4. Клиент: "Да, беру".
5. Ты: "Отлично! Напишите ваш телефон и адрес доставки."
6. Клиент: "Москва, Ленина 1, +7999..."
7. Ты: `create_order(items=[{"product_id": 105, "quantity": 1}], address="Москва, Ленина 1", phone="+7999...", name="Имя")`.
8. Результат: "Заказ #55 создан".
9. Ты: "Ваш заказ №55 принят! Менеджер свяжется для подтверждения."

ВАЖНО:
- Всегда старайся закрыть сделку через `create_order`.
- `notify_manager` используй только для сложных случаев "под заказ".
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

async def search_auto_parts(query: str, vin: str = None) -> str:
    """Ищет запчасти в БД."""
    print(f"🔎 [AI Tool] Searching parts: query='{query}', VIN='{vin}'")
    try:
        async with SessionLocal() as db:
            search_term = f"%{query}%"
            stmt = select(models.Product).where(
                or_(
                    models.Product.name.ilike(search_term),
                    models.Product.part_number.ilike(search_term),
                    models.Product.description.ilike(search_term)
                )
            ).limit(8)
            
            result = await db.execute(stmt)
            products = result.scalars().all()
            
            if not products:
                return "Поиск не дал результатов. Предложите поиск 'под заказ' через менеджера."
            
            res = f"Найдено {len(products)} товаров (используй ID для создания заказа):\n"
            for p in products:
                price = f"{p.price_rub} ₽" if p.price_rub else "Цена по запросу"
                stock = "В наличии" if p.is_in_stock else "Под заказ"
                # ВАЖНО: Добавляем ID в вывод, чтобы AI мог его считать
                res += f"[ID: {p.id}] {p.name} (Арт: {p.part_number}) — {price} ({stock})\n"
            return res
    except Exception as e:
        print(f"❌ DB Search Error: {e}")
        return "Ошибка при поиске в базе данных."

async def create_order(items: List[Dict[str, int]], address: str = "Не указан", phone: str = "Не указан", name: str = "Клиент", telegram_id: int = None) -> str:
    """Создает заказ в БД."""
    print(f"🛒 [AI Tool] Creating order for {name} ({phone}): {items}")
    
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
            
            # 3. Сохраняем позиции
            for item_data in order_items_db:
                db_item = models.OrderItem(
                    order_id=new_order.id,
                    product_id=item_data["product"].id,
                    quantity=item_data["quantity"],
                    price_at_purchase=item_data["price"]
                )
                db.add(db_item)
            
            await db.commit()
            await db.refresh(new_order)
            
            # 4. Уведомляем админов (как обычный заказ)
            notify_data = {
                "id": new_order.id,
                "user_name": new_order.user_name,
                "user_phone": new_order.user_phone,
                "delivery_address": new_order.delivery_address,
                "total_amount": new_order.total_amount,
                "items": [
                    {
                        "product_id": i["product"].id,
                        "product_name": i["product"].name,
                        "quantity": i["quantity"],
                        "price_at_purchase": i["price"]
                    } for i in order_items_db
                ],
                "created_at": datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            # Запускаем в фоне (или await, т.к. мы в async)
            try:
                await notify_new_order(notify_data)
            except Exception as e:
                print(f"Notification warning: {e}")
                
            return f"✅ Заказ #{new_order.id} успешно создан! Сумма: {total_amount} руб. Менеджер скоро свяжется."

    except Exception as e:
        print(f"❌ Create Order Error: {e}")
        return f"Ошибка при создании заказа: {str(e)}"

async def notify_manager(message: str, contact_info: str = "Не указаны") -> str:
    """Отправляет уведомление в Telegram админу."""
    print(f"🔔 [AI Tool] Notifying manager: {message}")
    if not BOT_TOKEN:
        return "Ошибка: Бот не настроен."
    
    bot = Bot(token=BOT_TOKEN)
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
                    await bot.send_message(chat_id=cid, text=text, parse_mode="HTML")
                    sent_count += 1
                except:
                    pass
        await bot.session.close()
        return "Уведомление отправлено менеджерам." if sent_count > 0 else "Ошибка: нет админов."
    except Exception as e:
        await bot.session.close()
        return f"Ошибка отправки: {str(e)}"

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
                        return {"role": "assistant", "content": f"Операция выполнена: {tool_result}"}

                    data2 = await resp2.json()
                    final_msg = data2["choices"][0]["message"]["content"]
                    return {"role": "assistant", "content": final_msg}

        except Exception as e:
            print(f"❌ Chat Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))
