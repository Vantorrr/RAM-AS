"""
СДЭК API Integration
Расчёт доставки, выбор ПВЗ, создание заказов
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

router = APIRouter(prefix="/cdek", tags=["CDEK Delivery"])

# API Credentials
CDEK_CLIENT_ID = os.getenv("CDEK_CLIENT_ID", "SDX33BbkxoquuQ2jHHynJR5coIiuQ12j")
CDEK_CLIENT_SECRET = os.getenv("CDEK_CLIENT_SECRET", "JlrbEnumAm1SRXqxHwdQSuFjlC3Ky8Ta")
CDEK_API_URL = "https://api.cdek.ru/v2"  # Боевой
# CDEK_TEST_URL = "https://api.edu.cdek.ru/v2"  # Тестовый

# Город отправления (склад RAM-US)
FROM_CITY_CODE = 44  # Москва (можно изменить)

# Кэш токена
_token_cache = {
    "token": None,
    "expires_at": None
}


async def get_cdek_token() -> str:
    """Получить токен авторизации СДЭК"""
    # Проверяем кэш
    if _token_cache["token"] and _token_cache["expires_at"]:
        if datetime.now() < _token_cache["expires_at"]:
            return _token_cache["token"]
    
    # Получаем новый токен
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CDEK_API_URL}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": CDEK_CLIENT_ID,
                "client_secret": CDEK_CLIENT_SECRET
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Ошибка авторизации СДЭК")
        
        data = response.json()
        _token_cache["token"] = data["access_token"]
        _token_cache["expires_at"] = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        
        return _token_cache["token"]


class DeliveryCalculateRequest(BaseModel):
    to_city_code: int  # Код города получателя
    weight: int = 1000  # Вес в граммах (по умолчанию 1 кг)
    length: int = 20  # Длина в см
    width: int = 15  # Ширина в см
    height: int = 10  # Высота в см


class DeliveryOption(BaseModel):
    tariff_code: int
    tariff_name: str
    delivery_sum: float
    period_min: int
    period_max: int


@router.post("/calculate", response_model=List[DeliveryOption])
async def calculate_delivery(request: DeliveryCalculateRequest):
    """Рассчитать стоимость доставки"""
    token = await get_cdek_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CDEK_API_URL}/calculator/tarifflist",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "from_location": {"code": FROM_CITY_CODE},
                "to_location": {"code": request.to_city_code},
                "packages": [{
                    "weight": request.weight,
                    "length": request.length,
                    "width": request.width,
                    "height": request.height
                }]
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Ошибка расчёта СДЭК")
        
        data = response.json()
        
        if "tariff_codes" not in data:
            return []
        
        options = []
        for tariff in data["tariff_codes"]:
            options.append(DeliveryOption(
                tariff_code=tariff["tariff_code"],
                tariff_name=tariff["tariff_name"],
                delivery_sum=tariff["delivery_sum"],
                period_min=tariff["period_min"],
                period_max=tariff["period_max"]
            ))
        
        return options


@router.get("/cities")
async def search_cities(query: str):
    """Поиск городов СДЭК"""
    token = await get_cdek_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CDEK_API_URL}/location/cities",
            headers={"Authorization": f"Bearer {token}"},
            params={"city": query, "size": 20}
        )
        
        if response.status_code != 200:
            return []
        
        return response.json()


@router.get("/pvz")
async def get_pickup_points(city_code: int):
    """Получить список ПВЗ в городе"""
    token = await get_cdek_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CDEK_API_URL}/deliverypoints",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "city_code": city_code,
                "type": "PVZ",  # Только пункты выдачи
                "is_handout": True
            }
        )
        
        if response.status_code != 200:
            return []
        
        points = response.json()
        
        # Форматируем для фронтенда
        result = []
        for p in points:
            result.append({
                "code": p.get("code"),
                "name": p.get("name"),
                "address": p.get("location", {}).get("address_full"),
                "work_time": p.get("work_time"),
                "phone": p.get("phones", [{}])[0].get("number") if p.get("phones") else None,
                "lat": p.get("location", {}).get("latitude"),
                "lon": p.get("location", {}).get("longitude"),
            })
        
        return result


class CreateOrderRequest(BaseModel):
    recipient_name: str
    recipient_phone: str
    recipient_email: Optional[str] = None
    to_city_code: int
    delivery_point: Optional[str] = None  # Код ПВЗ (для самовывоза)
    address: Optional[str] = None  # Адрес (для курьера)
    tariff_code: int
    items: List[dict]  # [{name, sku, payment_value, weight, amount}]
    order_number: str  # Номер заказа в нашей системе


@router.post("/orders")
async def create_cdek_order(request: CreateOrderRequest):
    """Создать заказ на доставку в СДЭК"""
    token = await get_cdek_token()
    
    # Формируем данные заказа
    order_data = {
        "number": request.order_number,
        "tariff_code": request.tariff_code,
        "sender": {
            "name": "RAM-US Auto Parts"
        },
        "recipient": {
            "name": request.recipient_name,
            "phones": [{"number": request.recipient_phone}]
        },
        "from_location": {
            "code": FROM_CITY_CODE
        },
        "to_location": {
            "code": request.to_city_code
        },
        "packages": [{
            "number": f"{request.order_number}-1",
            "weight": sum(item.get("weight", 500) * item.get("amount", 1) for item in request.items),
            "items": [{
                "name": item["name"],
                "ware_key": item.get("sku", str(i)),
                "payment": {"value": 0},  # Предоплачено
                "cost": item.get("payment_value", 0),
                "weight": item.get("weight", 500),
                "amount": item.get("amount", 1)
            } for i, item in enumerate(request.items)]
        }]
    }
    
    # Добавляем точку доставки
    if request.delivery_point:
        order_data["delivery_point"] = request.delivery_point
    elif request.address:
        order_data["to_location"]["address"] = request.address
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CDEK_API_URL}/orders",
            headers={"Authorization": f"Bearer {token}"},
            json=order_data
        )
        
        data = response.json()
        
        if "error" in data or response.status_code >= 400:
            raise HTTPException(
                status_code=400, 
                detail=data.get("error", {}).get("message", "Ошибка создания заказа СДЭК")
            )
        
        return {
            "uuid": data.get("entity", {}).get("uuid"),
            "cdek_number": data.get("entity", {}).get("cdek_number"),
            "status": "created"
        }


@router.get("/orders/{uuid}")
async def get_order_status(uuid: str):
    """Получить статус заказа СДЭК"""
    token = await get_cdek_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CDEK_API_URL}/orders/{uuid}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        data = response.json()
        entity = data.get("entity", {})
        
        return {
            "uuid": entity.get("uuid"),
            "cdek_number": entity.get("cdek_number"),
            "status_code": entity.get("statuses", [{}])[-1].get("code") if entity.get("statuses") else None,
            "status_name": entity.get("statuses", [{}])[-1].get("name") if entity.get("statuses") else None,
        }

