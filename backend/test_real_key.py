import asyncio
import aiohttp
import os

# Ключ из твоего скриншота
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-4o-mini"

async def test():
    print(f"🤖 Testing AI Key from screenshot: {API_KEY[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ram-us.com", 
        "X-Title": "RAM US Check",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Ты работаешь? Ответь ДА или НЕТ."}
        ]
    }

    async with aiohttp.ClientSession() as session:
        endpoint = f"{BASE_URL.rstrip('/')}/chat/completions"
        async with session.post(endpoint, headers=headers, json=payload) as resp:
            print(f"Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"✅ Success! Answer: {data['choices'][0]['message']['content']}")
            else:
                print(f"❌ Error: {await resp.text()}")

if __name__ == "__main__":
    asyncio.run(test())

