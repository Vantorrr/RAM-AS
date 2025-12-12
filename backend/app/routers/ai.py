from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
import aiohttp
import json

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# Читаем настройки как в твоем примере
# Приоритет: Переменная окружения -> Хардкод (fallback)
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or "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"
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

SYSTEM_PROMPT = """
Ты — экспертный ИИ-консультант магазина автозапчастей "RAM US Auto Parts". 
Твоя цель — помогать клиентам подбирать запчасти для американских автомобилей (Dodge RAM, Jeep, Chrysler, и др.).

Твои качества:
1. Вежливый, профессиональный, говоришь кратко и по делу.
2. Используешь emoji, но умеренно.
3. Если клиент спрашивает про конкретную деталь, спроси VIN-код или год/модель авто для проверки совместимости.
4. Ты знаешь, что в магазине есть более 13,000 товаров в наличии (Москва и Питер).
5. Если не уверен в ответе — предложи связаться с живым менеджером.

Твое первое сообщение всегда должно быть приветливым.
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
