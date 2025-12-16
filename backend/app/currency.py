import httpx
from datetime import datetime, timedelta
from typing import Optional

# Cache для курса валют
_currency_cache = {
    "rate": None,
    "updated_at": None
}

CACHE_DURATION = timedelta(hours=1)  # Обновляем курс раз в час

async def get_usd_rate() -> float:
    """
    Получает курс USD/RUB из API ЦБ РФ.
    Кэширует результат на 1 час.
    """
    global _currency_cache
    
    # Проверяем кэш
    if (_currency_cache["rate"] is not None and 
        _currency_cache["updated_at"] is not None and
        datetime.now() - _currency_cache["updated_at"] < CACHE_DURATION):
        return _currency_cache["rate"]
    
    # Запрашиваем курс из API ЦБ РФ
    try:
        async with httpx.AsyncClient() as client:
            # API ЦБ РФ: https://www.cbr-xml-daily.ru/daily_json.js
            response = await client.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Курс USD
            rate = data["Valute"]["USD"]["Value"]
            
            # Обновляем кэш
            _currency_cache["rate"] = rate
            _currency_cache["updated_at"] = datetime.now()
            
            return rate
    except Exception as e:
        print(f"Error fetching USD rate: {e}")
        # Возвращаем дефолтный курс, если API недоступен
        return 100.0

async def convert_usd_to_rub(usd_amount: float) -> float:
    """Конвертирует USD в RUB по текущему курсу"""
    rate = await get_usd_rate()
    return usd_amount * rate

async def convert_rub_to_usd(rub_amount: float) -> float:
    """Конвертирует RUB в USD по текущему курсу"""
    rate = await get_usd_rate()
    return rub_amount / rate






