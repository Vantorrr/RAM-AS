import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://alert-joy-production.up.railway.app")
ADMIN_WEBAPP_URL = os.getenv("ADMIN_WEBAPP_URL", "https://alert-joy-production.up.railway.app/admin")
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

def get_main_keyboard(is_admin_user: bool = False):
    """Красивые инлайн кнопки"""
    buttons = [
        [InlineKeyboardButton(text="🛒 Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))],
        [
            InlineKeyboardButton(text="💳 Реквизиты", callback_data="requisites"),
            InlineKeyboardButton(text="📍 О нас", callback_data="about")
        ],
        [InlineKeyboardButton(text="📞 Поддержка", callback_data="support")],
    ]
    
    if is_admin_user:
        buttons.append([InlineKeyboardButton(text="🔧 Админ-панель", web_app=WebAppInfo(url=ADMIN_WEBAPP_URL))])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.chat.type != "private":
        return
    
    user_id = message.from_user.id
    is_admin_user = is_admin(user_id)
    
    welcome_text = (
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        "🚗 Добро пожаловать в <b>RAM US Auto Parts</b>\n\n"
        "🇺🇸 Оригинальные запчасти из США\n"
        "📦 13,000+ товаров в каталоге\n"
        "🚚 Доставка по всей России\n"
        "💳 Оплата картой или по реквизитам\n\n"
        "👇 <b>Выбери действие:</b>"
    )
    
    if is_admin_user:
        welcome_text += "\n\n🔐 <i>Ты админ! Доступна панель управления.</i>"
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(is_admin_user)
    )

@dp.callback_query(F.data == "requisites")
async def show_requisites(callback: types.CallbackQuery):
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        COMPANY_REQUISITES,
        parse_mode="HTML",
        reply_markup=back_kb
    )
    await callback.answer()

@dp.callback_query(F.data == "about")
async def show_about(callback: types.CallbackQuery):
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
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        about_text,
        parse_mode="HTML",
        reply_markup=back_kb
    )
    await callback.answer()

@dp.callback_query(F.data == "support")
async def show_support(callback: types.CallbackQuery):
    support_text = """
📞 <b>Поддержка RAM US</b>

Есть вопросы? Мы на связи!

📱 <b>Telegram:</b> @ram_us_support
📧 <b>Email:</b> info@ram-us.ru
📞 <b>Телефон:</b> +7 (812) XXX-XX-XX

⏰ <b>Режим работы:</b>
Пн-Пт: 9:00 - 20:00
Сб: 10:00 - 18:00
Вс: выходной

Ответим в течение часа! 💪
"""
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Реквизиты", callback_data="requisites")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        support_text,
        parse_mode="HTML",
        reply_markup=back_kb
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_admin_user = is_admin(user_id)
    
    welcome_text = (
        f"👋 <b>Привет, {callback.from_user.first_name}!</b>\n\n"
        "🚗 Добро пожаловать в <b>RAM US Auto Parts</b>\n\n"
        "🇺🇸 Оригинальные запчасти из США\n"
        "📦 13,000+ товаров в каталоге\n"
        "🚚 Доставка по всей России\n"
        "💳 Оплата картой или по реквизитам\n\n"
        "👇 <b>Выбери действие:</b>"
    )
    
    if is_admin_user:
        welcome_text += "\n\n🔐 <i>Ты админ! Доступна панель управления.</i>"
    
    await callback.message.edit_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(is_admin_user)
    )
    await callback.answer()

@dp.message(Command("requisites"))
async def cmd_requisites(message: types.Message):
    if message.chat.type != "private":
        return
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    
    await message.answer(
        COMPANY_REQUISITES,
        parse_mode="HTML",
        reply_markup=back_kb
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.chat.type != "private":
        return
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет доступа к админ-панели.")
        return
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Открыть админ-панель", web_app=WebAppInfo(url=ADMIN_WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    
    await message.answer(
        "🔧 <b>Админ-панель RAM US</b>\n\n"
        "Здесь ты можешь:\n"
        "• Редактировать товары\n"
        "• Менять цены\n"
        "• Добавлять фото\n"
        "• Управлять рассрочкой\n\n"
        "👇 Нажми кнопку:",
        parse_mode="HTML",
        reply_markup=admin_kb
    )

@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    await message.answer(
        f"🆔 <b>Твой Telegram ID:</b>\n<code>{message.from_user.id}</code>\n\n"
        "Отправь этот ID разработчику для добавления в админы.",
        parse_mode="HTML"
    )

async def start_bot():
    """Запуск бота"""
    if not bot:
        print("❌ Bot not configured (no token)")
        return
    
    logging.basicConfig(level=logging.INFO)
    print("🚀 Bot is starting... STAY TOP!")
    print(f"📋 Admin IDs: {ADMIN_CHAT_IDS}")
    print(f"🌐 WebApp URL: {WEBAPP_URL}")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Bot error: {e}")

async def main():
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())
