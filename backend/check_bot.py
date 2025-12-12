import asyncio
import aiohttp
import os

TOKEN = "8222860429:AAH7mehGFmkSoNlOYbJlkSG3yTuyX4d54H4"

async def check():
    async with aiohttp.ClientSession() as session:
        # 1. Get Me
        print("🔍 Checking bot info...")
        async with session.get(f"https://api.telegram.org/bot{TOKEN}/getMe") as resp:
            print(f"getMe: {await resp.text()}")

        # 2. Get Webhook Info
        print("\n🔍 Checking webhook status...")
        async with session.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo") as resp:
            print(f"getWebhookInfo: {await resp.text()}")
            
        # 3. Get Updates
        print("\n🔍 Checking updates (messages)...")
        async with session.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1") as resp:
            print(f"getUpdates: {await resp.text()}")

asyncio.run(check())

