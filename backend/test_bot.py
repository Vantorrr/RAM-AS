import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = "8222860429:AAH7mehGFmkSoNlOYbJlkSG3yTuyX4d54H4"
WEBAPP_URL = "https://alert-joy-production.up.railway.app"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    print(f'✅ Got /start from {message.from_user.id} ({message.from_user.username})')
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "🚗 Добро пожаловать в RAM US Auto Parts!\n\n"
        "👇 Нажми кнопку ниже:",
        reply_markup=keyboard
    )

async def main():
    print('🤖 Bot starting...')
    print(f'📱 WebApp URL: {WEBAPP_URL}')
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())

