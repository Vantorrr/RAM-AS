"""
PayMaster Payment Integration
API v2 Documentation: https://paymaster.ru/docs/ru/api
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
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
from ..bot import bot

router = APIRouter(prefix="/payments", tags=["Payments"])

# PayMaster Configuration
PAYMASTER_MERCHANT_ID = "5cad3313-7c95-416a-bbe8-6fb95c52ec7a"
PAYMASTER_BEARER_TOKEN = "e82d0df805d69ebcadf379d366f2cfc662fb825f368e3c246f606f1ca643d16402f68ce0cdc2c9e37bf81d4ba99be61644cb"
PAYMASTER_API_URL = "https://paymaster.ru/api/v2"
BASE_URL = os.getenv("BASE_URL", "https://alert-joy-production.up.railway.app")

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
            "callbackUrl": f"{BASE_URL}/api/v1/payments/webhook",
            "returnUrl": f"https://t.me/ramus_autobot/app?startapp=payment_success"
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
        invoice_id=invoice_data["id"],
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
            "callbackUrl": f"{BASE_URL}/api/v1/payments/webhook",
            "returnUrl": f"https://t.me/ramus_autobot/app?startapp=order_success_{order.id}"
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
    
    return InvoiceResponse(
        invoice_id=invoice_data["id"],
        payment_url=invoice_data["url"],
        amount=order.total_amount,
        order_id=order.id
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
        
        payment_type = params.get("type", "subscription")  # "order" or "subscription"
        
        # Обработка оплаты ЗАКАЗА
        if payment_type == "order":
            order_id = params.get("order_id")
            if not order_id:
                print("❌ Missing order_id in webhook")
                return {"status": "error", "message": "Missing order_id"}
            
            if status == "Settled":
                # Обновляем статус заказа
                result = await db.execute(
                    select(models.Order).where(models.Order.id == int(order_id))
                )
                order = result.scalar_one_or_none()
                
                if order:
                    order.status = "paid"
                    await db.commit()
                    
                    # Уведомляем пользователя
                    try:
                        await bot.send_message(
                            chat_id=order.user_telegram_id,
                            text=f"✅ <b>Оплата подтверждена!</b>\n\n"
                                 f"📦 Заказ #{order.id} оплачен\n"
                                 f"💰 Сумма: {order.total_amount} ₽\n\n"
                                 f"Скоро свяжемся с вами для подтверждения доставки!",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"❌ Failed to notify user: {e}")
                    
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

