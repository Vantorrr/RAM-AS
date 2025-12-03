import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-webapp-url.vercel.app")
ADMIN_WEBAPP_URL = os.getenv("ADMIN_WEBAPP_URL", WEBAPP_URL.replace("vercel.app", "vercel.app/admin") if WEBAPP_URL else "https://your-webapp-url.vercel.app/admin")
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_IDS", "").split(",")

# Также поддержка одного ID для обратной совместимости
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if ADMIN_CHAT_ID:
    ADMIN_CHAT_IDS.append(ADMIN_CHAT_ID)

# Удаляем пустые строки
ADMIN_CHAT_IDS = [x.strip() for x in ADMIN_CHAT_IDS if x.strip()]

if not TOKEN:
    print("WARNING: No BOT_TOKEN provided in .env file")
    TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"

bot = Bot(token=TOKEN) if TOKEN and TOKEN != "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz" else None
dp = Dispatcher()

# Реквизиты компании
COMPANY_REQUISITES = """
🏢 <b>ИП Решетникова Кристина Евгеньевна</b>

📋 <b>Реквизиты для оплаты:</b>

▫️ ИНН: <code>519090741487</code>
▫️ ОГРНИП: <code>325784700406601</code>
▫️ Р/с: <code>40802810300008948074</code>

🏦 <b>Банк:</b> АО «ТБанк»
▫️ БИК: <code>044525974</code>
▫️ Корр. счёт: <code>30101810145250000974</code>

📍 Адрес: г. Санкт-Петербург
"""

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь админом"""
    return str(user_id) in ADMIN_CHAT_IDS

async def notify_new_order(order_data: dict):
    """Отправляет уведомление админам о новом заказе"""
    if not bot or not ADMIN_CHAT_IDS:
        print("WARNING: Bot not configured or no admins set")
        return
    
    try:
        message = (
            "🔔 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
            f"📦 Заказ #{order_data['id']}\n"
            f"👤 Клиент: {order_data.get('user_name', 'Не указано')}\n"
            f"📱 Телефон: {order_data.get('user_phone', 'Не указано')}\n"
            f"📍 Адрес: {order_data.get('delivery_address', 'Не указано')}\n\n"
            f"💰 Сумма: {order_data['total_amount']:,.0f} ₽\n"
            f"📋 Товаров: {len(order_data.get('items', []))}\n\n"
            f"⏰ Время: {order_data.get('created_at', 'сейчас')}"
        )
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text=message, parse_mode="HTML")
            except Exception as e:
                print(f"Error sending to {admin_id}: {e}")
    except Exception as e:
        print(f"Error sending notification: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Проверяем, личный ли это чат
    if message.chat.type != "private":
        return
    
    user_id = message.from_user.id
    
    # Формируем клавиатуру в зависимости от того, админ или нет
    if is_admin(user_id):
        # Клавиатура для АДМИНА
        kb = [
            [types.KeyboardButton(text="🔥 ОТКРЫТЬ КАТАЛОГ 🔥", web_app=WebAppInfo(url=WEBAPP_URL))],
            [types.KeyboardButton(text="🔧 АДМИН-ПАНЕЛЬ", web_app=WebAppInfo(url=ADMIN_WEBAPP_URL))],
            [types.KeyboardButton(text="📦 Мои заказы"), types.KeyboardButton(text="📞 Поддержка")]
        ]
        extra_text = "\n\n🔐 <b>Ты админ!</b> Нажми 🔧 для управления товарами."
    else:
        # Клавиатура для обычного пользователя
        kb = [
            [types.KeyboardButton(text="🔥 ОТКРЫТЬ КАТАЛОГ 🔥", web_app=WebAppInfo(url=WEBAPP_URL))],
            [types.KeyboardButton(text="📦 Мои заказы"), types.KeyboardButton(text="📞 Поддержка")]
        ]
        extra_text = ""
    
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer_photo(
        photo="https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Ram_trucks_logo.png/640px-Ram_trucks_logo.png",
        caption=(
            f"👋 <b>Салют, {message.from_user.first_name}!</b>\n\n"
            "Добро пожаловать в <b>RAM US Auto Parts</b> — место, где твоя тачка получит лучшее.\n\n"
            "🛠 <b>Что у нас есть:</b>\n"
            "— Оригинальные запчасти из США\n"
            "— Амортизаторы, тормоза, подвеска\n"
            "— Цены, которые не кусаются (по курсу)\n\n"
            f"👇 <b>Жми кнопку ниже и выбирай детали по-мужски!</b>{extra_text}"
        ),
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.message(F.text == "📦 Мои заказы")
async def my_orders(message: types.Message):
    if message.chat.type != "private":
        return
    await message.answer("📦 История твоих заказов пока пуста.\n\nСделай первый заказ в каталоге! 🛒")

@dp.message(F.text == "📞 Поддержка")
async def support(message: types.Message):
    if message.chat.type != "private":
        return
    
    # Инлайн кнопки
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Реквизиты для оплаты", callback_data="requisites")],
        [InlineKeyboardButton(text="📍 О компании", callback_data="about")],
        [InlineKeyboardButton(text="📞 Связаться с менеджером", url="https://t.me/manager_username")]
    ])
    
    await message.answer(
        "📞 <b>Поддержка RAM US</b>\n\n"
        "Выбери нужный раздел:\n\n"
        "💳 <b>Реквизиты</b> — для оплаты по счёту\n"
        "📍 <b>О компании</b> — информация о нас\n"
        "📞 <b>Менеджер</b> — задать вопрос\n",
        parse_mode="HTML",
        reply_markup=inline_kb
    )

@dp.callback_query(F.data == "requisites")
async def show_requisites(callback: types.CallbackQuery):
    """Показать реквизиты компании"""
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_support")]
    ])
    
    await callback.message.edit_text(
        COMPANY_REQUISITES,
        parse_mode="HTML",
        reply_markup=inline_kb
    )
    await callback.answer()

@dp.callback_query(F.data == "about")
async def show_about(callback: types.CallbackQuery):
    """Показать информацию о компании"""
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Реквизиты", callback_data="requisites")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_support")]
    ])
    
    about_text = """
🚗 <b>RAM US Auto Parts</b>

🇺🇸 <b>Прямые поставки из США</b>
Оригинальные запчасти для американских автомобилей.

📅 <b>12+ лет на рынке</b>
Работаем с 2012 года. Тысячи довольных клиентов.

📦 <b>13,000+ товаров</b>
Огромный ассортимент в наличии и под заказ.

🚚 <b>Доставка по всей России</b>
СДЭК, Почта России, до двери.

💯 <b>Гарантия качества</b>
Только оригинальные детали с документами.
"""
    
    await callback.message.edit_text(
        about_text,
        parse_mode="HTML",
        reply_markup=inline_kb
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_support")
async def back_to_support(callback: types.CallbackQuery):
    """Вернуться в меню поддержки"""
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Реквизиты для оплаты", callback_data="requisites")],
        [InlineKeyboardButton(text="📍 О компании", callback_data="about")],
        [InlineKeyboardButton(text="📞 Связаться с менеджером", url="https://t.me/manager_username")]
    ])
    
    await callback.message.edit_text(
        "📞 <b>Поддержка RAM US</b>\n\n"
        "Выбери нужный раздел:\n\n"
        "💳 <b>Реквизиты</b> — для оплаты по счёту\n"
        "📍 <b>О компании</b> — информация о нас\n"
        "📞 <b>Менеджер</b> — задать вопрос\n",
        parse_mode="HTML",
        reply_markup=inline_kb
    )
    await callback.answer()

@dp.message(Command("requisites"))
async def cmd_requisites(message: types.Message):
    """Команда /requisites - показать реквизиты"""
    if message.chat.type != "private":
        return
    
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 О компании", callback_data="about")],
        [InlineKeyboardButton(text="🛒 Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await message.answer(
        COMPANY_REQUISITES,
        parse_mode="HTML",
        reply_markup=inline_kb
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Команда /admin для быстрого доступа к админке"""
    if message.chat.type != "private":
        return
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет доступа к админ-панели.")
        return
    
    kb = [[types.KeyboardButton(text="🔧 ОТКРЫТЬ АДМИНКУ", web_app=WebAppInfo(url=ADMIN_WEBAPP_URL))]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    await message.answer("👆 Нажми кнопку для входа в админ-панель:", reply_markup=keyboard)

@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    """Команда /myid - показывает ID пользователя для настройки админов"""
    await message.answer(
        f"🆔 <b>Твой Telegram ID:</b>\n<code>{message.from_user.id}</code>\n\n"
        "Отправь этот ID разработчику для добавления в админы.",
        parse_mode="HTML"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Bot is starting... STAY TOP!")
    print(f"📋 Admin IDs configured: {ADMIN_CHAT_IDS}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
