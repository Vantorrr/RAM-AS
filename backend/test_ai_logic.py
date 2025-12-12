import asyncio
import aiohttp
import os

# Имитируем настройки как в коде
API_KEY = os.getenv("OPENAI_API_KEY") or "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"
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

SYSTEM_PROMPT = """
Ты — экспертный ИИ-консультант магазина автозапчастей "RAM US Auto Parts". 
Твоя цель — помогать клиентам подбирать запчасти для американских автомобилей.
"""

async def test():
    print(f"🤖 Testing AI: Model={MODEL}, URL={BASE_URL}, Key={API_KEY[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://test.local", 
        "X-Title": "Test Script",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Что такое RAM US?"}
        ]
    }

    async with aiohttp.ClientSession() as session:
        endpoint = f"{BASE_URL.rstrip('/')}/chat/completions"
        async with session.post(endpoint, headers=headers, json=payload) as resp:
            print(f"Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"Answer: {data['choices'][0]['message']['content']}")
            else:
                print(f"Error: {await resp.text()}")

if __name__ == "__main__":
    asyncio.run(test())

