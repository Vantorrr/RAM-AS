from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
import aiohttp
import json

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

# Ключ OpenRouter (лучше вынести в .env в продакшене)
# Пока используем переданный тобой ключ для теста
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

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
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="AI API Key not configured")

    # Clean key just in case
    clean_key = OPENROUTER_API_KEY.strip().strip('"').strip("'")
    print(f"🔑 Using AI Key: {clean_key[:10]}... (len: {len(clean_key)})")

    headers = {
        "Authorization": f"Bearer {clean_key}",
        "Content-Type": "application/json",
    }

    # Добавляем системный промпт в начало
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [m.dict() for m in request.messages]

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ OpenRouter Error ({resp.status}): {error_text}")
                    raise HTTPException(status_code=resp.status, detail=f"AI Error: {error_text}")
                
                data = await resp.json()
                ai_response = data["choices"][0]["message"]["content"]
                return {"role": "assistant", "content": ai_response}
        except Exception as e:
            print(f"AI Error: {e}")
            raise HTTPException(status_code=500, detail="Ошибка соединения с AI")

