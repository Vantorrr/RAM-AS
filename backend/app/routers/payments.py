"""
Payment Integration: PayMaster & T-Bank
- PayMaster API v2: https://paymaster.ru/docs/ru/api
- T-Bank API v2: https://www.tbank.ru/kassa/develop/api/
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
import httpx
import hashlib
import hmac
import json
from datetime import datetime, timedelta
import os

from .. import models, schemas
from ..database import get_db
from ..bot import bot, ADMIN_CHAT_IDS

router = APIRouter(prefix="/payments", tags=["Payments"])

# PayMaster Configuration - ВАЖНО: используем переменные окружения!
PAYMASTER_MERCHANT_ID = os.getenv("PAYMASTER_MERCHANT_ID", "")
PAYMASTER_BEARER_TOKEN = os.getenv("PAYMASTER_BEARER_TOKEN", "")
PAYMASTER_API_URL = "https://paymaster.ru/api/v2"
# ВАЖНО: callbackUrl должен идти на БЭКЕНД, не на фронтенд!
BACKEND_URL = os.getenv("BACKEND_URL", "https://ram-as-production.up.railway.app")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://alert-joy-production.up.railway.app")

# Проверка конфигурации при старте
if not PAYMASTER_MERCHANT_ID or not PAYMASTER_BEARER_TOKEN:
    print("⚠️ WARNING: PAYMASTER_MERCHANT_ID or PAYMASTER_BEARER_TOKEN not set!")

# T-Bank Configuration (PRODUCTION)
TBANK_TERMINAL_KEY = os.getenv("TBANK_TERMINAL_KEY", "1766825321741")
TBANK_PASSWORD = os.getenv("TBANK_PASSWORD", "0W0qq&IxbbRu*LeL")
TBANK_API_URL = "https://securepay.tinkoff.ru/v2"

if not TBANK_TERMINAL_KEY or not TBANK_PASSWORD:
    print("⚠️ WARNING: TBANK_TERMINAL_KEY or TBANK_PASSWORD not set!")

# Subscription Plans Pricing (in RUB)
SUBSCRIPTION_PRICES = {
    "start": 990,    # Start: 990₽/месяц
    "pro": 2990,     # Pro: 2990₽/месяц
    "magnate": 9990  # Magnate: 9990₽/месяц
}

SUBSCRIPTION_LIMITS = {
    "free": 5,
    "start": 50,
    "pro": 200,
    "magnate": 999999
}


# === PYDANTIC SCHEMAS ===

class CreateInvoiceRequest(BaseModel):
    seller_id: int
    subscription_tier: str  # "start", "pro", "magnate"
    test_mode: bool = True  # По умолчанию тестовый режим


class CreateOrderInvoiceRequest(BaseModel):
    order_id: int
    test_mode: bool = True  # По умолчанию тестовый режим


class CreateListingInvoiceRequest(BaseModel):
    listing_id: int
    test_mode: bool = True  # По умолчанию тестовый режим


# Стоимость размещения объявления в барахолке
LISTING_PRICE = 200  # 200 рублей


class InvoiceResponse(BaseModel):
    invoice_id: str
    payment_url: str
    amount: float
    subscription_tier: Optional[str] = None
    order_id: Optional[int] = None


class PayMasterWebhook(BaseModel):
    """Webhook от PayMaster о статусе платежа"""
    id: str
    status: str  # "Settled", "Authorized", "Cancelled", "Rejected"
    amount: dict
    invoice: dict
    created: str
    updated: Optional[str] = None


# === PAYMENT FUNCTIONS ===

async def create_paymaster_invoice(
    seller_id: int,
    subscription_tier: str,
    test_mode: bool = True
) -> dict:
    """
    Создает счет на оплату через PayMaster API v2
    """
    
    if subscription_tier not in SUBSCRIPTION_PRICES:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    amount = SUBSCRIPTION_PRICES[subscription_tier]
    
    # Формируем payload для PayMaster API
    payload = {
        "merchantId": PAYMASTER_MERCHANT_ID,
        "testMode": test_mode,
        "invoice": {
            "description": f"Подписка {subscription_tier.upper()} — RAM-US",
            "orderNo": f"seller_{seller_id}_{subscription_tier}_{int(datetime.now().timestamp())}",
            "params": {
                "seller_id": str(seller_id),
                "subscription_tier": subscription_tier
            }
        },
        "amount": {
            "value": float(amount),
            "currency": "RUB"
        },
        "protocol": {
            "callbackUrl": f"{BACKEND_URL}/payments/webhook",
            "returnUrl": f"https://t.me/ram_us_bot/app?startapp=payment_success"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {PAYMASTER_BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMASTER_API_URL}/invoices",
            json=payload,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"❌ PayMaster API Error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"PayMaster API Error: {response.text}"
            )
        
        return response.json()


async def update_seller_subscription(
    db: AsyncSession,
    seller_id: int,
    subscription_tier: str,
    payment_id: str
):
    """
    Обновляет подписку партнера после успешной оплаты
    """
    result = await db.execute(
        select(models.Seller).where(models.Seller.id == seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        print(f"❌ Seller {seller_id} not found")
        return
    
    # Обновляем тариф и лимиты
    seller.subscription_tier = subscription_tier
    seller.max_products = SUBSCRIPTION_LIMITS[subscription_tier]
    seller.subscription_expires = datetime.now() + timedelta(days=30)
    
    await db.commit()
    await db.refresh(seller)
    
    # Отправляем уведомление партнеру
    try:
        await bot.send_message(
            chat_id=seller.telegram_id,
            text=f"✅ <b>Подписка активирована!</b>\n\n"
                 f"📦 Тариф: <b>{subscription_tier.upper()}</b>\n"
                 f"📊 Лимит товаров: <b>{SUBSCRIPTION_LIMITS[subscription_tier]}</b>\n"
                 f"📅 Действует до: <b>{seller.subscription_expires.strftime('%d.%m.%Y')}</b>\n\n"
                 f"💳 ID платежа: <code>{payment_id}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"❌ Failed to send notification to seller {seller_id}: {e}")
    
    print(f"✅ Subscription updated for seller {seller_id}: {subscription_tier}")


# === API ENDPOINTS ===

@router.post("/create-invoice", response_model=InvoiceResponse)
async def create_invoice(
    request: CreateInvoiceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Создает счет на оплату подписки для партнера
    """
    
    # Проверяем, существует ли партнер
    result = await db.execute(
        select(models.Seller).where(models.Seller.id == request.seller_id)
    )
    seller = result.scalar_one_or_none()
    
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    
    # Создаем счет через PayMaster
    invoice_data = await create_paymaster_invoice(
        seller_id=request.seller_id,
        subscription_tier=request.subscription_tier,
        test_mode=request.test_mode
    )
    
    return InvoiceResponse(
        invoice_id=invoice_data["paymentId"],
        payment_url=invoice_data["url"],
        amount=SUBSCRIPTION_PRICES[request.subscription_tier],
        subscription_tier=request.subscription_tier
    )


@router.post("/create-order-invoice", response_model=InvoiceResponse)
async def create_order_invoice(
    request: CreateOrderInvoiceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Создает счет на оплату заказа
    """
    
    # Проверяем, существует ли заказ
    result = await db.execute(
        select(models.Order).where(models.Order.id == request.order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Формируем payload для PayMaster API
    payload = {
        "merchantId": PAYMASTER_MERCHANT_ID,
        "testMode": request.test_mode,
        "invoice": {
            "description": f"Заказ #{order.id} — RAM-US Auto Parts",
            "orderNo": f"order_{order.id}_{int(datetime.now().timestamp())}",
            "params": {
                "order_id": str(order.id),
                "type": "order"
            }
        },
        "amount": {
            "value": float(order.total_amount),
            "currency": "RUB"
        },
        "protocol": {
            "callbackUrl": f"{BACKEND_URL}/payments/webhook",
            "returnUrl": f"https://t.me/ram_us_bot/app?startapp=order_success_{order.id}"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {PAYMASTER_BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMASTER_API_URL}/invoices",
            json=payload,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"❌ PayMaster API Error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"PayMaster API Error: {response.text}"
            )
        
        invoice_data = response.json()
        print(f"✅ PayMaster Response: {json.dumps(invoice_data, indent=2, ensure_ascii=False)}")
        
        # Проверяем наличие обязательных полей (PayMaster возвращает paymentId, не id!)
        if "paymentId" not in invoice_data or "url" not in invoice_data:
            print(f"❌ Missing 'paymentId' or 'url' in PayMaster response: {invoice_data}")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid PayMaster response: {invoice_data}"
            )
    
    return InvoiceResponse(
        invoice_id=invoice_data["paymentId"],
        payment_url=invoice_data["url"],
        amount=order.total_amount,
        order_id=order.id
    )


@router.post("/create-listing-invoice", response_model=InvoiceResponse)
async def create_listing_invoice(
    request: CreateListingInvoiceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Создает счет на оплату размещения объявления в барахолке
    """
    
    # Проверяем, существует ли объявление
    result = await db.execute(
        select(models.Listing).where(models.Listing.id == request.listing_id)
    )
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Формируем payload для PayMaster API
    payload = {
        "merchantId": PAYMASTER_MERCHANT_ID,
        "testMode": request.test_mode,
        "invoice": {
            "description": f"Размещение объявления — Барахолка RAM-US",
            "orderNo": f"listing_{listing.id}_{int(datetime.now().timestamp())}",
            "params": {
                "listing_id": str(listing.id),
                "type": "listing"
            }
        },
        "amount": {
            "value": float(LISTING_PRICE),
            "currency": "RUB"
        },
        "protocol": {
            "callbackUrl": f"{BACKEND_URL}/payments/webhook",
            "returnUrl": f"https://t.me/ram_us_bot/app?startapp=listing_success_{listing.id}"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {PAYMASTER_BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMASTER_API_URL}/invoices",
            json=payload,
            headers=headers,
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"❌ PayMaster API Error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"PayMaster API Error: {response.text}"
            )
        
        invoice_data = response.json()
        print(f"✅ PayMaster Response: {json.dumps(invoice_data, indent=2, ensure_ascii=False)}")
        
        if "paymentId" not in invoice_data or "url" not in invoice_data:
            print(f"❌ Missing 'paymentId' or 'url' in PayMaster response: {invoice_data}")
            raise HTTPException(
                status_code=500,
                detail=f"Invalid PayMaster response: {invoice_data}"
            )
    
    return InvoiceResponse(
        invoice_id=invoice_data["paymentId"],
        payment_url=invoice_data["url"],
        amount=LISTING_PRICE
    )


@router.post("/webhook")
async def paymaster_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook для обработки уведомлений от PayMaster
    """
    
    try:
        body = await request.json()
        print(f"📥 PayMaster Webhook: {json.dumps(body, indent=2, ensure_ascii=False)}")
        
        payment_id = body.get("id")
        status = body.get("status")
        invoice = body.get("invoice", {})
        params = invoice.get("params", {})
        
        payment_type = params.get("type", "subscription")  # "order", "listing" or "subscription"
        
        # Обработка оплаты ОБЪЯВЛЕНИЯ (Барахолка)
        if payment_type == "listing":
            listing_id = params.get("listing_id")
            if not listing_id:
                print("❌ Missing listing_id in webhook")
                return {"status": "error", "message": "Missing listing_id"}
            
            if status == "Settled":
                # Обновляем статус объявления
                result = await db.execute(
                    select(models.Listing).where(models.Listing.id == int(listing_id))
                )
                listing = result.scalar_one_or_none()
                
                if listing:
                    # Сохраняем данные ДО commit
                    listing_data = {
                        "id": listing.id,
                        "title": listing.title,
                        "seller_telegram_id": listing.seller_telegram_id
                    }
                    
                    listing.is_paid = True
                    listing.status = "pending"  # Отправляем на модерацию
                    await db.commit()
                    print(f"✅ Listing {listing_id} marked as paid and sent to moderation")
                    
                    # Уведомляем пользователя (используем сохранённые данные)
                    try:
                        await bot.send_message(
                            chat_id=listing_data["seller_telegram_id"],
                            text=f"✅ <b>Оплата подтверждена!</b>\n\n"
                                 f"📋 Объявление: {listing_data['title']}\n"
                                 f"💰 Сумма: 200 ₽\n\n"
                                 f"⏳ Объявление отправлено на модерацию.\n"
                                 f"После проверки оно появится в ленте барахолки!",
                            parse_mode="HTML"
                        )
                        print(f"✅ User {listing_data['seller_telegram_id']} notified")
                    except Exception as e:
                        print(f"❌ Failed to notify user: {e}")
                    
                    # Уведомляем админов о новом объявлении
                    try:
                        for admin_id in ADMIN_CHAT_IDS:
                            await bot.send_message(
                                chat_id=admin_id,
                                text=f"📋 <b>Новое объявление на модерацию!</b>\n\n"
                                     f"📦 {listing_data['title']}\n"
                                     f"🆔 ID: {listing_data['id']}\n\n"
                                     f"Проверьте в админке: /admin → Барахолка",
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        print(f"❌ Failed to notify admins: {e}")
                    return {"status": "ok", "message": "Listing payment confirmed"}
                else:
                    print(f"❌ Listing {listing_id} not found")
                    return {"status": "error", "message": "Listing not found"}
            
            elif status in ["Cancelled", "Rejected"]:
                print(f"⚠️ Listing payment {payment_id} failed with status: {status}")
                return {"status": "ok", "message": "Listing payment failed"}
        
        # Обработка оплаты ЗАКАЗА
        elif payment_type == "order":
            order_id = params.get("order_id")
            if not order_id:
                print("❌ Missing order_id in webhook")
                return {"status": "error", "message": "Missing order_id"}
            
            if status == "Settled":
                # Обновляем статус заказа (загружаем вместе с items)
                result = await db.execute(
                    select(models.Order)
                    .where(models.Order.id == int(order_id))
                    .options(selectinload(models.Order.items))
                )
                order = result.scalar_one_or_none()
                
                if order:
                    # Сохраняем ВСЕ данные в простые Python объекты ДО коммита
                    order_items_data = [{
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "price_at_purchase": item.price_at_purchase
                    } for item in order.items]
                    
                    order_data = {
                        "id": order.id,
                        "user_name": order.user_name,
                        "user_phone": order.user_phone,
                        "user_telegram_id": order.user_telegram_id,
                        "total_amount": order.total_amount,
                        "delivery_type": order.delivery_type,
                        "delivery_address": order.delivery_address,
                        "cdek_tariff_code": order.cdek_tariff_code,
                        "cdek_city_code": order.cdek_city_code,
                        "cdek_city_name": order.cdek_city_name,
                        "cdek_pvz_code": order.cdek_pvz_code,
                        "cdek_pvz_address": order.cdek_pvz_address,
                    }
                    
                    order.status = "paid"
                    await db.commit()
                    
                    # Создаём заказ в СДЭК если указаны данные доставки
                    cdek_info = ""
                    if order_data["cdek_tariff_code"] and order_data["cdek_city_code"]:
                        try:
                            # Вызываем свой же API для создания заказа СДЭК
                            cdek_request = {
                                "order_number": f"RAM-{order_data['id']}",
                                "recipient_name": order_data["user_name"] or "Покупатель",
                                "recipient_phone": order_data["user_phone"] or "",
                                "to_city_code": order_data["cdek_city_code"],
                                "tariff_code": order_data["cdek_tariff_code"],
                                "items": [{
                                    "name": f"Товар #{item['product_id']}",
                                    "sku": str(item["product_id"]),
                                    "payment_value": item["price_at_purchase"],
                                    "weight": 500,
                                    "amount": item["quantity"]
                                } for item in order_items_data]
                            }
                            
                            # СДЭК требует ИЛИ delivery_point ИЛИ address
                            if order_data["cdek_pvz_code"]:
                                cdek_request["delivery_point"] = order_data["cdek_pvz_code"]
                            else:
                                cdek_request["address"] = order_data["delivery_address"] or "Адрес уточняется"
                            
                            async with httpx.AsyncClient(timeout=30) as client:
                                resp = await client.post(
                                    f"{BACKEND_URL}/cdek/orders",
                                    json=cdek_request
                                )
                                
                                if resp.status_code == 200:
                                    cdek_result = resp.json()
                                    cdek_uuid = cdek_result.get("uuid")
                                    cdek_number = cdek_result.get("cdek_number")
                                    
                                    # Обновляем заказ в БД через новую сессию
                                    from ..database import SessionLocal
                                    async with SessionLocal() as new_db:
                                        await new_db.execute(
                                            models.Order.__table__.update()
                                            .where(models.Order.id == order_data["id"])
                                            .values(cdek_uuid=cdek_uuid, cdek_number=cdek_number)
                                        )
                                        await new_db.commit()
                                    
                                    cdek_info = f"\n📦 Накладная СДЭК: {cdek_number or 'создаётся...'}"
                                    print(f"✅ CDEK order created: {cdek_uuid}")
                                else:
                                    print(f"❌ CDEK API error: {resp.status_code} - {resp.text}")
                        except Exception as e:
                            print(f"❌ Failed to create CDEK order: {e}")
                    
                    # Уведомляем пользователя
                    try:
                        delivery_text = ""
                        if order_data["delivery_type"] == "cdek_pvz":
                            delivery_text = f"📍 ПВЗ: {order_data['cdek_pvz_address']}"
                        elif order_data["delivery_type"] == "cdek_door":
                            delivery_text = f"🚚 Курьер: {order_data['delivery_address']}"
                        else:
                            delivery_text = "🏪 Самовывоз"
                        
                        await bot.send_message(
                            chat_id=order_data["user_telegram_id"],
                            text=f"✅ <b>Оплата подтверждена!</b>\n\n"
                                 f"📦 Заказ #{order_data['id']}\n"
                                 f"💰 Сумма: {order_data['total_amount']:,.0f} ₽\n"
                                 f"{delivery_text}{cdek_info}\n\n"
                                 f"Спасибо за покупку! 🙏",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"❌ Failed to notify user: {e}")
                    
                    # Уведомляем менеджеров
                    try:
                        for admin_id in ADMIN_CHAT_IDS:
                            await bot.send_message(
                                chat_id=admin_id,
                                text=f"🎉 <b>НОВЫЙ ОПЛАЧЕННЫЙ ЗАКАЗ!</b>\n\n"
                                     f"📦 Заказ #{order_data['id']}\n"
                                     f"👤 {order_data['user_name']} ({order_data['user_phone']})\n"
                                     f"💰 {order_data['total_amount']:,.0f} ₽\n"
                                     f"🚚 {order_data['cdek_city_name'] or 'Самовывоз'}{cdek_info}",
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        print(f"❌ Failed to notify admins: {e}")
                    
                    print(f"✅ Order {order_id} marked as paid")
                    return {"status": "ok", "message": "Order payment confirmed"}
                else:
                    print(f"❌ Order {order_id} not found")
                    return {"status": "error", "message": "Order not found"}
            
            elif status in ["Cancelled", "Rejected"]:
                print(f"⚠️ Order payment {payment_id} failed with status: {status}")
                return {"status": "ok", "message": "Order payment failed"}
        
        # Обработка оплаты ПОДПИСКИ
        else:
            seller_id = params.get("seller_id")
            subscription_tier = params.get("subscription_tier")
            
            if not seller_id or not subscription_tier:
                print("❌ Missing seller_id or subscription_tier in webhook")
                return {"status": "error", "message": "Missing required params"}
            
            if status == "Settled":
                background_tasks.add_task(
                    update_seller_subscription,
                    db,
                    int(seller_id),
                    subscription_tier,
                    payment_id
                )
                return {"status": "ok", "message": "Subscription updated"}
            
            elif status in ["Cancelled", "Rejected"]:
                print(f"⚠️ Subscription payment {payment_id} failed with status: {status}")
                return {"status": "ok", "message": "Subscription payment failed"}
        
        return {"status": "ok", "message": f"Status {status} received"}
    
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"status": "error", "message": str(e)}


# === T-BANK PAYMENT INTEGRATION ===

def calculate_tbank_token(params: dict, password: str) -> str:
    """
    Генерирует токен для T-Bank API
    Token = SHA-256(отсортированные_параметры + Password_в_конце)
    
    Алгоритм по документации T-Bank:
    1. Отсортировать параметры по ключу (БЕЗ Password)
    2. Конкатенировать значения
    3. Добавить Password В КОНЕЦ
    4. SHA-256
    """
    # Сортируем параметры по ключу
    sorted_keys = sorted(params.keys())
    values = [str(params[k]) for k in sorted_keys]
    
    # Добавляем Password В КОНЕЦ (не сортируем!)
    values.append(password)
    
    concatenated = "".join(values)
    token = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()
    
    print(f"🔐 Token params (sorted): {sorted_keys} + Password")
    print(f"🔐 Token string: {concatenated}")
    print(f"🔐 Token hash: {token}")
    
    return token


class TBankPaymentRequest(BaseModel):
    order_id: int


class TBankPaymentResponse(BaseModel):
    payment_id: str
    payment_url: str
    amount: float


@router.post("/tbank/init", response_model=TBankPaymentResponse)
async def create_tbank_payment(
    request: TBankPaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Создаёт платеж через T-Bank эквайринг
    """
    
    # Получаем заказ
    result = await db.execute(
        select(models.Order).where(models.Order.id == request.order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Формируем параметры для T-Bank API
    amount_kopecks = int(order.total_amount * 100)  # в копейках!
    order_id = f"order_{order.id}_{int(datetime.now().timestamp())}"
    
    # Параметры для токена (по документации T-Bank - БЕЗ Description!)
    token_params = {
        "Amount": amount_kopecks,
        "OrderId": order_id,
        "TerminalKey": TBANK_TERMINAL_KEY
    }
    
    # Генерируем токен
    token = calculate_tbank_token(token_params, TBANK_PASSWORD)
    
    # Полные параметры запроса
    params = {
        "TerminalKey": TBANK_TERMINAL_KEY,
        "Amount": amount_kopecks,
        "OrderId": order_id,
        "Description": f"Оплата заказа #{order.id}",
        "Token": token,
        "DATA": {
            "order_id": str(order.id)
        }
    }
    
    # Отправляем запрос в T-Bank
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TBANK_API_URL}/Init",
            json=params,
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"❌ T-Bank API Error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"T-Bank API Error: {response.text}"
            )
        
        result = response.json()
        print(f"✅ T-Bank Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # Проверяем ответ
        if not result.get("Success"):
            error_code = result.get("ErrorCode", "Unknown")
            error_message = result.get("Message", "Unknown error")
            print(f"❌ T-Bank Error: {error_code} - {error_message}")
            raise HTTPException(
                status_code=400,
                detail=f"T-Bank Error: {error_message}"
            )
        
        payment_id = result.get("PaymentId")
        payment_url = result.get("PaymentURL")
        
        if not payment_id or not payment_url:
            print(f"❌ Missing PaymentId or PaymentURL in response: {result}")
            raise HTTPException(
                status_code=500,
                detail="Invalid T-Bank response"
            )
    
    return TBankPaymentResponse(
        payment_id=str(payment_id),
        payment_url=payment_url,
        amount=order.total_amount
    )


@router.post("/tbank/notification")
async def tbank_notification(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook для обработки уведомлений от T-Bank
    """
    
    try:
        body = await request.json()
        print(f"📥 T-Bank Notification: {json.dumps(body, indent=2, ensure_ascii=False)}")
        
        # Проверяем токен
        received_token = body.get("Token")
        params_for_token = {k: v for k, v in body.items() if k != "Token"}
        expected_token = calculate_tbank_token(params_for_token, TBANK_PASSWORD)
        
        if received_token != expected_token:
            print("❌ Invalid token in T-Bank notification!")
            return {"status": "error", "message": "Invalid token"}
        
        status = body.get("Status")
        order_id_str = body.get("OrderId", "")
        
        # Извлекаем ID заказа из OrderId (order_123_timestamp)
        try:
            order_id = int(order_id_str.split("_")[1])
        except:
            print(f"❌ Cannot parse order_id from: {order_id_str}")
            return {"status": "error", "message": "Invalid OrderId"}
        
        # Обрабатываем успешную оплату
        if status == "CONFIRMED":
            result = await db.execute(
                select(models.Order)
                .where(models.Order.id == order_id)
                .options(selectinload(models.Order.items))
            )
            order = result.scalar_one_or_none()
            
            if order:
                # Сохраняем данные
                order_data = {
                    "id": order.id,
                    "user_name": order.user_name,
                    "user_phone": order.user_phone,
                    "user_telegram_id": order.user_telegram_id,
                    "total_amount": order.total_amount,
                    "delivery_address": order.delivery_address
                }
                
                order.status = "paid"
                await db.commit()
                
                # Уведомляем пользователя
                try:
                    await bot.send_message(
                        chat_id=order_data["user_telegram_id"],
                        text=f"✅ <b>Оплата подтверждена!</b>\n\n"
                             f"📦 Заказ #{order_data['id']}\n"
                             f"💰 Сумма: {order_data['total_amount']:,.0f} ₽\n\n"
                             f"Спасибо за покупку! 🙏",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"❌ Failed to notify user: {e}")
                
                # Уведомляем админов
                try:
                    for admin_id in ADMIN_CHAT_IDS:
                        await bot.send_message(
                            chat_id=admin_id,
                            text=f"🎉 <b>НОВЫЙ ОПЛАЧЕННЫЙ ЗАКАЗ (T-Bank)!</b>\n\n"
                                 f"📦 Заказ #{order_data['id']}\n"
                                 f"👤 {order_data['user_name']} ({order_data['user_phone']})\n"
                                 f"💰 {order_data['total_amount']:,.0f} ₽",
                            parse_mode="HTML"
                        )
                except Exception as e:
                    print(f"❌ Failed to notify admins: {e}")
                
                print(f"✅ Order {order_id} marked as paid (T-Bank)")
                return {"status": "ok"}
            else:
                print(f"❌ Order {order_id} not found")
                return {"status": "error", "message": "Order not found"}
        
        elif status in ["CANCELED", "REJECTED"]:
            print(f"⚠️ T-Bank payment for order {order_id} failed with status: {status}")
            return {"status": "ok"}
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"❌ T-Bank Webhook Error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/subscription-plans")
async def get_subscription_plans():
    """
    Возвращает список доступных тарифов подписки
    """
    return {
        "plans": [
            {
                "tier": "start",
                "name": "Start",
                "price": SUBSCRIPTION_PRICES["start"],
                "limit": SUBSCRIPTION_LIMITS["start"],
                "description": "Для начинающих продавцов"
            },
            {
                "tier": "pro",
                "name": "Pro",
                "price": SUBSCRIPTION_PRICES["pro"],
                "limit": SUBSCRIPTION_LIMITS["pro"],
                "description": "Для активных продавцов"
            },
            {
                "tier": "magnate",
                "name": "Magnate",
                "price": SUBSCRIPTION_PRICES["magnate"],
                "limit": SUBSCRIPTION_LIMITS["magnate"],
                "description": "Безлимитный план"
            }
        ]
    }

