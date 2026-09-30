"""
Pydantic-схемы для FastAPI.
"""
from typing import List, Optional
from pydantic import BaseModel


class ProductOut(BaseModel):
    """Один товар в ответе API."""
    id: int
    category: str
    name: str
    price: float
    old_price: Optional[float] = None
    discount: str = ""
    link: str
    image_url: str = ""
    brand_name: str = ""
    brand_country: str = ""
    parsed_at: Optional[str] = None

    class Config:
        from_attributes = True


class CategoryStats(BaseModel):
    """Статистика по одной категории."""
    category: str
    total: int
    avg_price: float
    min_price: float
    max_price: float


class OverallStats(BaseModel):
    """Общая статистика по всей БД."""
    total_products: int
    avg_price: float
    max_price: float
    min_price: float
    categories: List[CategoryStats]