import asyncio
import aiohttp
import json

KEY = "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"

async def test():
    print(f"🔑 Testing key: {KEY[:10]}...")
    
    headers = {
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://test.com", 
        "X-Title": "Test Script",
    }
    
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello! Are you working?"}]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload) as resp:
            print(f"Status: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}")

if __name__ == "__main__":
    asyncio.run(test())

