from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import distinct
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

# 🇺🇸 ТОЛЬКО АМЕРИКАНСКИЕ МАРКИ (RAM-US специализация)
AMERICAN_MAKES = [
    "RAM", 
    "Dodge", 
    "Jeep", 
    "Chrysler",
    "Hummer",
    "Cadillac", 
    "Chevrolet",
    "GMC",
    "Lincoln"
]

@router.get("/config")
async def get_vehicles_config(db: AsyncSession = Depends(get_db)):
    """
    Получить дерево конфигурации автомобилей для фильтра:
    Make -> Model -> Year -> Engine
    ТОЛЬКО АМЕРИКАНСКИЕ МАРКИ: RAM, Dodge, Jeep, Chrysler
    """
    # Запрашиваем только американские авто
    result = await db.execute(
        select(models.Vehicle).where(models.Vehicle.make.in_(AMERICAN_MAKES))
    )
    vehicles = result.scalars().all()
    
    # Строим структуру:
    # {
    #   "RAM": {
    #     "1500": {
    #       "years": [2019, 2020, ...],
    #       "engines": ["5.7L HEMI", ...]
    #     }
    #   }
    # }
    
    config = {}
    
    for v in vehicles:
        if v.make not in config:
            config[v.make] = {}
        
        if v.model not in config[v.make]:
            config[v.make][v.model] = {
                "years": set(),
                "engines": set(),
                "generations": set()
            }
            
        # Генерация годов
        end_year = v.year_to if v.year_to else 2025 # Текущий год + 1
        for year in range(v.year_from, end_year + 1):
            config[v.make][v.model]["years"].add(year)
            
        if v.engine:
            config[v.make][v.model]["engines"].add(v.engine)
            
        if v.generation:
            config[v.make][v.model]["generations"].add(v.generation)
            
    # Преобразуем сеты в списки для JSON
    final_config = []
    
    for make, models_dict in config.items():
        models_list = []
        for model_name, data in models_dict.items():
            models_list.append({
                "name": model_name,
                "years": sorted(list(data["years"])),
                "engines": sorted(list(data["engines"])),
                "generations": sorted(list(data["generations"]))
            })
        final_config.append({
            "make": make,
            "models": models_list
        })
        
    return final_config

@router.post("/", response_model=schemas.Vehicle)
async def create_vehicle(
    vehicle: schemas.VehicleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать автомобиль (для админки)"""
    db_vehicle = models.Vehicle(**vehicle.dict())
    db.add(db_vehicle)
    await db.commit()
    await db.refresh(db_vehicle)
    return db_vehicle

@router.get("/", response_model=List[schemas.Vehicle])
async def get_vehicles(db: AsyncSession = Depends(get_db)):
    """Получить список всех авто"""
    result = await db.execute(select(models.Vehicle))
    return result.scalars().all()

