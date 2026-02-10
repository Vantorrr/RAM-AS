import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from dotenv import load_dotenv
import os

MSK = timezone(timedelta(hours=3))

# Путь к изображению
BOT_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "bot_image.jpg")

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
        # Формируем список товаров
        items_list = ""
        items = order_data.get('items', [])
        
        for item in items:
            # Обработка и словарей и Pydantic объектов
            if isinstance(item, dict):
                product_name = item.get('product_name', f"Товар #{item.get('product_id', '?')}")
                part_number = item.get('part_number', '')
                quantity = item.get('quantity', 1)
                price = item.get('price_at_purchase', 0)
                is_preorder = item.get('is_preorder', False)
            else:
                # Pydantic объект
                product_name = getattr(item, 'product_name', f"Товар #{getattr(item, 'product_id', '?')}")
                part_number = getattr(item, 'part_number', '')
                quantity = getattr(item, 'quantity', 1)
                price = getattr(item, 'price_at_purchase', 0)
                is_preorder = getattr(item, 'is_preorder', False)
            
            preorder_mark = " ⏱️ <b>ПОД ЗАКАЗ (4-6 нед)</b>" if is_preorder else ""
            article_str = f" (арт. {part_number})" if part_number else ""
            items_list += f"  • {product_name}{article_str} — {quantity} шт × {price:,.0f} ₽{preorder_mark}\n"
        
        # Если список товаров пустой, показываем только количество
        if not items_list:
            items_list = f"  {len(items)} товар(ов)\n"
        
        # Статус оплаты
        status = order_data.get('status', 'pending')
        if status == 'paid':
            payment_status = "✅ <b>Оплачено</b>"
        elif status == 'pending':
            payment_status = "⏳ Ожидает оплаты"
        else:
            payment_status = f"ℹ️ {status}"
        
        order_id = order_data['id']
        message = (
            "🔔 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
            f"📦 Заказ #{order_id}\n"
            f"👤 Клиент: {order_data.get('user_name', 'Не указано')}\n"
            f"📱 Телефон: {order_data.get('user_phone', 'Не указано')}\n"
            f"📍 Адрес: {order_data.get('delivery_address', 'Не указано')}\n\n"
            f"🛒 <b>Товары:</b>\n{items_list}\n"
            f"💰 <b>Итого:</b> {order_data['total_amount']:,.0f} ₽\n"
            f"💳 <b>Статус:</b> {payment_status}\n\n"
            f"⏰ Время: {datetime.now(MSK).strftime('%d.%m.%Y %H:%M')} (МСК)"
        )
        
        # Инлайн-кнопки управления заказом
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚚 Отправлен", callback_data=f"order_shipped_{order_id}"),
                InlineKeyboardButton(text="📬 Доставлен", callback_data=f"order_delivered_{order_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"order_cancel_{order_id}"),
            ]
        ])
        
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text=message, parse_mode="HTML", reply_markup=keyboard)
            except Exception as e:
                print(f"Error sending to {admin_id}: {e}")
    except Exception as e:
        print(f"Error sending notification: {e}")


async def notify_order_paid(order_data: dict):
    """Отправляет красивое уведомление админам об оплате заказа"""
    if not bot or not ADMIN_CHAT_IDS:
        return
    
    try:
        # Формируем список товаров с артикулами
        items_list = ""
        items = order_data.get('items', [])
        
        for item in items:
            if isinstance(item, dict):
                product_name = item.get('product_name', f"Товар #{item.get('product_id', '?')}")
                part_number = item.get('part_number', '')
                quantity = item.get('quantity', 1)
                price = item.get('price_at_purchase', 0)
                is_preorder = item.get('is_preorder', False)
            else:
                product_name = getattr(item, 'product_name', '?')
                part_number = getattr(item, 'part_number', '')
                quantity = getattr(item, 'quantity', 1)
                price = getattr(item, 'price_at_purchase', 0)
                is_preorder = getattr(item, 'is_preorder', False)
            
            preorder_mark = " ⏱️ <b>ПОД ЗАКАЗ</b>" if is_preorder else ""
            article_str = f"\n     📋 Арт: <code>{part_number}</code>" if part_number else ""
            items_list += f"  ✅ {product_name} — {quantity} шт × {price:,.0f} ₽{preorder_mark}{article_str}\n"
        
        if not items_list:
            items_list = f"  {len(items)} товар(ов)\n"
        
        # Определяем способ оплаты
        payment_method = order_data.get('payment_method', '')
        if payment_method:
            payment_method = f"\n💳 <b>Оплата:</b> {payment_method}"
        
        # Доставка
        delivery_info = ""
        delivery_type = order_data.get('delivery_type', '')
        if delivery_type == 'cdek_pvz':
            delivery_info = f"\n📍 <b>ПВЗ СДЭК:</b> {order_data.get('cdek_pvz_address', 'Не указан')}"
        elif delivery_type == 'cdek_door':
            delivery_info = f"\n🚚 <b>Курьер:</b> {order_data.get('delivery_address', 'Не указан')}"
        elif order_data.get('delivery_address'):
            delivery_info = f"\n📍 <b>Адрес:</b> {order_data.get('delivery_address', 'Не указан')}"

        cdek_info = ""
        if order_data.get('cdek_number'):
            cdek_info = f"\n📦 <b>Накладная СДЭК:</b> <code>{order_data['cdek_number']}</code>"
        
        order_id = order_data['id']
        message = (
            "💰 <b>ЗАКАЗ ОПЛАЧЕН!</b> ✅\n\n"
            f"📦 Заказ #{order_id}\n"
            f"👤 <b>Клиент:</b> {order_data.get('user_name', 'Не указано')}\n"
            f"📱 <b>Телефон:</b> {order_data.get('user_phone', 'Не указано')}"
            f"{delivery_info}{cdek_info}{payment_method}\n\n"
            f"🛒 <b>Товары:</b>\n{items_list}\n"
            f"💵 <b>Итого:</b> {order_data['total_amount']:,.0f} ₽\n\n"
            f"⏰ {datetime.now(MSK).strftime('%d.%m.%Y %H:%M')} (МСК)"
        )
        
        # Кнопки: оплачен → дальше отправить или отменить
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚚 Отправлен", callback_data=f"order_shipped_{order_id}"),
                InlineKeyboardButton(text="📬 Доставлен", callback_data=f"order_delivered_{order_id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"order_cancel_{order_id}"),
            ]
        ])
        
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text=message, parse_mode="HTML", reply_markup=keyboard)
            except Exception as e:
                print(f"Error sending paid notification to {admin_id}: {e}")
    except Exception as e:
        print(f"Error sending paid notification: {e}")


async def notify_order_status_changed(order_data: dict, old_status: str, new_status: str):
    """Уведомляет админов и клиента о смене статуса заказа"""
    if not bot or not ADMIN_CHAT_IDS:
        return
    
    STATUS_LABELS = {
        "pending": "⏳ Ожидает оплаты",
        "paid": "✅ Оплачено",
        "processing": "🔧 В обработке",
        "shipped": "🚚 Отправлен",
        "delivered": "📬 Доставлен",
        "cancelled": "❌ Отменён",
    }
    
    old_label = STATUS_LABELS.get(old_status, old_status)
    new_label = STATUS_LABELS.get(new_status, new_status)
    
    try:
        # Уведомление админам
        admin_msg = (
            f"🔄 <b>Статус заказа изменён</b>\n\n"
            f"📦 Заказ #{order_data['id']}\n"
            f"👤 {order_data.get('user_name', 'Не указано')}\n"
            f"📱 {order_data.get('user_phone', 'Не указано')}\n\n"
            f"📊 {old_label} → {new_label}\n\n"
            f"⏰ {datetime.now(MSK).strftime('%d.%m.%Y %H:%M')} (МСК)"
        )
        
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text=admin_msg, parse_mode="HTML")
            except Exception as e:
                print(f"Error sending status notification to {admin_id}: {e}")
        
        # Уведомление клиенту
        user_tg_id = order_data.get('user_telegram_id')
        if user_tg_id:
            user_msg = (
                f"📦 <b>Обновление по заказу #{order_data['id']}</b>\n\n"
                f"📊 Статус: {new_label}\n"
            )
            
            if new_status == "shipped":
                user_msg += f"\n🚚 Ваш заказ отправлен! Ожидайте доставку."
            elif new_status == "delivered":
                user_msg += f"\n📬 Ваш заказ доставлен! Спасибо за покупку! 🙏"
            elif new_status == "cancelled":
                user_msg += f"\n❌ Заказ отменён. Если есть вопросы — свяжитесь с нами."
            
            try:
                await bot.send_message(chat_id=user_tg_id, text=user_msg, parse_mode="HTML")
            except Exception as e:
                print(f"Error sending status notification to user {user_tg_id}: {e}")
    except Exception as e:
        print(f"Error sending status notification: {e}")


def get_main_keyboard(is_admin_user: bool = False):
    """Красивые инлайн кнопки"""
    buttons = [
        [InlineKeyboardButton(text="🛒 Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))],
        [
            InlineKeyboardButton(text="💳 Реквизиты", callback_data="requisites"),
            InlineKeyboardButton(text="📍 О нас", callback_data="about")
        ],
        [InlineKeyboardButton(text="📞 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="📢 Подписаться на канал", url="https://t.me/ramus_official")],
    ]
    
    if is_admin_user:
        buttons.append([InlineKeyboardButton(text="🔧 Админ-панель", web_app=WebAppInfo(url=ADMIN_WEBAPP_URL))])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функция для редактирования сообщения (текст или подпись к фото)
async def edit_message_smart(message: types.Message, text: str, reply_markup: InlineKeyboardMarkup):
    try:
        # Если есть фото, меняем caption
        if message.photo:
            await message.edit_caption(
                caption=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        # Иначе меняем текст
        else:
            await message.edit_text(
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
    except Exception as e:
        print(f"Error editing message: {e}")
        # Если не получилось отредактировать, отправляем новое (на всякий случай)
        # Но это крайний случай, обычно не нужно

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    print(f"🚀 cmd_start called for user {message.from_user.id}")
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
    
    # Отправляем просто текст для надежности
    try:
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard(is_admin_user)
        )
    except Exception as e:
        print(f"❌ Error sending start message: {e}")

# === ОБРАБОТЧИКИ КНОПОК УПРАВЛЕНИЯ ЗАКАЗАМИ ===

@dp.callback_query(F.data.startswith("order_shipped_"))
async def handle_order_shipped(callback: types.CallbackQuery):
    """Кнопка 🚚 Отправлен"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[-1])
    await _change_order_status(callback, order_id, "shipped", "🚚 Отправлен")


@dp.callback_query(F.data.startswith("order_delivered_"))
async def handle_order_delivered(callback: types.CallbackQuery):
    """Кнопка 📬 Доставлен"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[-1])
    await _change_order_status(callback, order_id, "delivered", "📬 Доставлен")


@dp.callback_query(F.data.startswith("order_cancel_"))
async def handle_order_cancel(callback: types.CallbackQuery):
    """Кнопка ❌ Отмена"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[-1])
    await _change_order_status(callback, order_id, "cancelled", "❌ Отменён")


async def _change_order_status(callback: types.CallbackQuery, order_id: int, new_status: str, status_label: str):
    """Общая логика смены статуса заказа через кнопку"""
    from .database import SessionLocal
    from . import models
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload
    
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(models.Order)
                .where(models.Order.id == order_id)
                .options(
                    selectinload(models.Order.items)
                    .selectinload(models.OrderItem.product)
                )
            )
            order = result.scalar_one_or_none()
            
            if not order:
                await callback.answer(f"❌ Заказ #{order_id} не найден", show_alert=True)
                return
            
            old_status = order.status
            
            if old_status == new_status:
                await callback.answer(f"Заказ уже в статусе: {status_label}", show_alert=True)
                return
            
            # Сохраняем данные ДО коммита
            order_data = {
                "id": order.id,
                "user_name": order.user_name,
                "user_phone": order.user_phone,
                "user_telegram_id": order.user_telegram_id,
                "total_amount": order.total_amount,
                "delivery_address": order.delivery_address,
            }
            
            # Меняем статус
            order.status = new_status
            await db.commit()
        
        # Уведомляем клиента
        await notify_order_status_changed(order_data, old_status, new_status)
        
        # Обновляем сообщение — убираем кнопки и показываем новый статус
        STATUS_LABELS = {
            "pending": "⏳ Ожидает оплаты",
            "paid": "✅ Оплачено",
            "processing": "🔧 В обработке",
            "shipped": "🚚 Отправлен",
            "delivered": "📬 Доставлен",
            "cancelled": "❌ Отменён",
        }
        
        # Добавляем строку со статусом к оригинальному сообщению
        old_text = callback.message.text or callback.message.caption or ""
        updated_text = callback.message.html_text or old_text
        
        # Убираем старые кнопки, добавляем статус
        new_text = updated_text + f"\n\n✅ <b>Статус обновлён:</b> {STATUS_LABELS.get(new_status, new_status)}"
        
        try:
            await callback.message.edit_text(
                text=new_text,
                parse_mode="HTML",
                reply_markup=None  # Убираем кнопки
            )
        except Exception as e:
            print(f"Error editing message: {e}")
        
        await callback.answer(f"✅ Заказ #{order_id}: {status_label}", show_alert=True)
        
    except Exception as e:
        print(f"❌ Error changing order status: {e}")
        import traceback
        traceback.print_exc()
        await callback.answer(f"❌ Ошибка: {str(e)[:100]}", show_alert=True)


@dp.callback_query(F.data == "requisites")
async def show_requisites(callback: types.CallbackQuery):
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    
    await edit_message_smart(callback.message, COMPANY_REQUISITES, back_kb)
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
    
    await edit_message_smart(callback.message, about_text, back_kb)
    await callback.answer()

@dp.callback_query(F.data == "support")
async def show_support(callback: types.CallbackQuery):
    support_text = """
📞 <b>Поддержка RAM US</b>

Есть вопросы? Мы на связи!

📱 <b>Telegram:</b> @RAMUS_PARTS
📞 <b>Телефон:</b> +7 933 566 8777

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
    
    await edit_message_smart(callback.message, support_text, back_kb)
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
    
    await edit_message_smart(callback.message, welcome_text, get_main_keyboard(is_admin_user))
    await callback.answer()

@dp.message(Command("requisites"))
async def cmd_requisites(message: types.Message):
    if message.chat.type != "private":
        return
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Открыть каталог", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    
    # Для команды requisites отправляем фото тоже, или просто текст
    # Лучше фото для консистентности
    try:
        await message.answer_photo(
            photo=FSInputFile(BOT_IMAGE_PATH),
            caption=COMPANY_REQUISITES,
            parse_mode="HTML",
            reply_markup=back_kb
        )
    except:
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
