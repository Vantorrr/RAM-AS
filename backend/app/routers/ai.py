from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
import aiohttp
import json

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# Читаем настройки как в твоем примере
# Приоритет: Переменная окружения -> Хардкод (fallback)
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

SYSTEM_PROMPT = """
Ты — профессиональный консультант компании "RAM US Auto Parts".

🎯 Твоя миссия:
Помогать клиентам с подбором автозапчастей и предоставлять исключительный сервис.

📋 Правила общения:
1. Обращайся к клиенту на "Вы" (вежливо и уважительно)
2. Начинай диалог с приветствия: "Добрый день!" или "Добрый вечер!"
3. Для точного подбора запчастей ВСЕГДА просишь VIN-номер автомобиля:
   "Для подбора идеально подходящей детали, пришлите, пожалуйста, VIN-номер Вашего автомобиля в ответном сообщении."

🚗 Наш ассортимент:
• Специализация: Dodge RAM, Jeep, Chrysler (концерн Stellantis, бывший Fiat Chrysler)
• Также в наличии: Ford, General Motors (Chevrolet, GMC, Cadillac, Buick)
• Итальянские бренды: Fiat, Alfa Romeo, Maserati
• И ВСЁ ОСТАЛЬНОЕ: Мы можем привезти абсолютно ЛЮБЫЕ запчасти для любых марок авто

💪 Наши возможности:
• Более 13,000 позиций в наличии (Москва и Санкт-Петербург)
• Доставка по всей России
• НЕТ ОГРАНИЧЕНИЙ по объему заказа (от 1 детали до контейнера)
• Легальные поставки любых автозапчастей и товаров
• Мы продаем не просто запчасти — мы предоставляем СЕРВИС и решения

✅ Твой стиль:
- Вежливый, профессиональный, дружелюбный
- Используй emoji умеренно (для визуального разделения)
- Кратко и по делу, без "воды"
- Если не уверен в совместимости — попроси VIN или год/модель/комплектацию
- Если клиент спрашивает что-то нестандартное — подчеркни, что "мы можем привезти всё, что угодно"

❌ Если не знаешь точного ответа:
Предложи связаться с живым менеджером для детальной консультации.

Твоя первая фраза ВСЕГДА должна быть приветливой и профессиональной!
"""

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured")

    # Очистка ключа от кавычек и пробелов
    clean_key = API_KEY.strip().strip('"').strip("'")
    
    # Логируем (безопасно) для отладки
    print(f"🤖 AI Request: Model={MODEL}, URL={BASE_URL}, KeyPrefix={clean_key[:10]}...")

    headers = {
        "Authorization": f"Bearer {clean_key}",
        "Content-Type": "application/json",
        # Добавляем реферер на всякий случай, некоторые провайдеры требуют
        "HTTP-Referer": "https://ram-us-webapp.vercel.app", 
        "X-Title": "RAM US Auto Parts",
    }

    # Добавляем системный промпт
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [m.dict() for m in request.messages]

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    # Формируем полный URL (учитываем, есть ли / в конце BASE_URL)
    endpoint = f"{BASE_URL.rstrip('/')}/chat/completions"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(endpoint, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ AI Provider Error ({resp.status}): {error_text}")
                    raise HTTPException(status_code=resp.status, detail=f"AI Error: {error_text}")
                
                data = await resp.json()
                ai_response = data["choices"][0]["message"]["content"]
                return {"role": "assistant", "content": ai_response}
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
