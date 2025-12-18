import os
import json
import aiohttp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from sqlalchemy import select, or_
from app.database import SessionLocal
from app import models
from aiogram import Bot

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
Помогать клиентам находить автозапчасти, проверять наличие и связывать с менеджерами.

🛠️ ТВОИ ИНСТРУМЕНТЫ (Tools):
1. `search_auto_parts`: ОБЯЗАТЕЛЬНО вызывай эту функцию, если клиент ищет запчасть (по названию, артикулу и т.д.). Не отвечай наугад! Сначала проверь базу.
2. `notify_manager`: Вызывай эту функцию, если:
   - Клиент явно просит связаться с менеджером.
   - Клиент хочет оформить заказ.
   - Ты не нашел деталь, но клиент хочет её заказать ("под заказ").
   - Клиент предоставил VIN и ждет подбора (которого нет в базе).

📋 Алгоритм работы:
1. Клиент: "Нужен фильтр" -> Ты: "Понял, ищу..." -> Вызов `search_auto_parts`.
2. Если `search_auto_parts` вернул товары -> Покажи их клиенту с ценами.
3. Если `search_auto_parts` ничего не нашел -> Скажи: "В наличии сейчас не вижу, но можем привезти. Передать заявку менеджеру?"
4. Если клиент согласен или сразу пишет VIN -> Вызов `notify_manager`.

ВАЖНО: Если вызываешь `notify_manager`, обязательно скажи клиенту: "Я передал информацию менеджеру, он скоро свяжется с вами."
"""

# --- Tools Definitions ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_auto_parts",
            "description": "Поиск автозапчастей в БД магазина. Использовать при любых запросах о наличии или цене.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос: название детали, артикул или описание."
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
            "name": "notify_manager",
            "description": "Отправка уведомления живому менеджеру в Telegram. Использовать для заказов или сложных вопросов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Суть обращения (что клиент хочет, какую деталь ищет)."
                    },
                    "contact_info": {
                        "type": "string",
                        "description": "VIN, телефон или юзернейм клиента."
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
            # Ищем по названию, артикулу или описанию
            # Разбиваем запрос на слова для лучшего поиска (если несколько слов)
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
                return "Поиск по базе данных не дал результатов. Рекомендуется предложить 'notify_manager' для подбора под заказ."
            
            res = f"Найдено {len(products)} товаров:\n"
            for p in products:
                price = f"{p.price_rub} ₽" if p.price_rub else "Цена по запросу"
                stock = "В наличии" if p.is_in_stock else "Под заказ"
                res += f"- {p.name} (Арт: {p.part_number}) — {price} ({stock})\n"
            return res
    except Exception as e:
        print(f"❌ DB Search Error: {e}")
        return "Ошибка при поиске в базе данных."

async def notify_manager(message: str, contact_info: str = "Не указаны") -> str:
    """Отправляет уведомление в Telegram админу."""
    print(f"🔔 [AI Tool] Notifying manager: {message}")
    if not BOT_TOKEN:
        return "Ошибка: Бот не настроен (нет токена)."
    
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
                except Exception as ex:
                    print(f"Failed to send to {cid}: {ex}")
        
        await bot.session.close()
        
        if sent_count > 0:
            return "Успешно: Уведомление отправлено менеджерам."
        else:
            return "Ошибка: Не удалось отправить уведомление (нет доступных админов)."
            
    except Exception as e:
        await bot.session.close()
        print(f"❌ Notify Error: {e}")
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
    
    # Гарантируем наличие System Prompt
    system_content = SYSTEM_PROMPT_CONTENT
    
    # Если есть инфо о юзере, добавляем в контекст
    if request.user_info:
        user_details = []
        if request.user_info.first_name:
            user_details.append(f"Имя: {request.user_info.first_name}")
        if request.user_info.username:
            user_details.append(f"Telegram: @{request.user_info.username}")
        if request.user_info.id:
            user_details.append(f"ID: {request.user_info.id}")
            
        if user_details:
            system_content += f"\n\n👤 ИНФОРМАЦИЯ О КЛИЕНТЕ:\n" + "\n".join(user_details) + "\n(Используй эти данные при вызове notify_manager)"

    if not any(m['role'] == 'system' for m in messages):
        messages.insert(0, {"role": "system", "content": system_content})
    else:
        # Если system уже есть (например, от клиента?), обновляем его
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
            # 1. Первый запрос (LLM думает, нужны ли тулы)
            async with session.post(endpoint, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"AI Error ({resp.status}): {text}")
                    raise HTTPException(status_code=resp.status, detail=f"AI Provider Error: {text}")
                
                data = await resp.json()
                choice = data["choices"][0]
                ai_msg = choice["message"]
                
                # Если LLM не хочет вызывать тулы, просто отдаем ответ
                if not ai_msg.get("tool_calls"):
                    return {"role": "assistant", "content": ai_msg["content"]}
                
                # 2. Обработка Tool Calls
                tool_calls = ai_msg["tool_calls"]
                messages.append(ai_msg) # Добавляем "мысль" модели в историю
                
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
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(tool_result)
                    })
                
                # 3. Второй запрос (LLM формирует финальный ответ на основе результатов тулов)
                payload["messages"] = messages
                payload.pop("tool_choice", None) # Больше не форсим тулы (хотя auto и так ок)
                
                async with session.post(endpoint, headers=headers, json=payload) as resp2:
                    if resp2.status != 200:
                         # Если второй запрос упал, вернем хотя бы то, что есть, или ошибку
                        text = await resp2.text()
                        print(f"AI Round 2 Error: {text}")
                        # Fallback: просто скажем, что сделали
                        return {"role": "assistant", "content": f"Я выполнил запрос, но произошла ошибка при формировании ответа. Результат операции: {tool_result}"}

                    data2 = await resp2.json()
                    final_msg = data2["choices"][0]["message"]["content"]
                    return {"role": "assistant", "content": final_msg}

        except Exception as e:
            print(f"❌ Chat Exception: {e}")
            raise HTTPException(status_code=500, detail=str(e))
