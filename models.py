"""
Pydantic-модели для валидации данных о товарах Yves Rocher.
"""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================
# ENUM ДЛЯ КАТЕГОРИЙ
# ============================================================
class CategoryEnum(str, Enum):
    """Только разрешённые категории."""
    FACE = "Лицо"
    HAIR = "Волосы"
    BODY = "Тело и гигиена"
    OTHER = "Другое"


# ============================================================
# ВЛОЖЕННАЯ МОДЕЛЬ: БРЕНД
# ============================================================
class Brand(BaseModel):
    """Бренд товара."""
    name: str = Field(..., min_length=1, max_length=100)
    country: str = Field(default="France", max_length=100)
    is_organic: bool = Field(default=False)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Название бренда не может быть пустым")
        return v.strip()


# ============================================================
# ОСНОВНАЯ МОДЕЛЬ: ТОВАР
# ============================================================
class Product(BaseModel):
    """Один товар Yves Rocher с валидацией."""

    # --- обязательные поля с ограничениями ---
    category: CategoryEnum = Field(
        ...,
        description="Категория: Лицо / Волосы / Тело и гигиена / Другое"
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Название товара"
    )
    price: float = Field(
        ...,
        gt=0,
        le=100000,
        description="Цена в рублях (> 0 и ≤ 100000)"
    )
    link: str = Field(
        ...,
        min_length=10,
        description="Ссылка на товар"
    )

    # --- необязательные поля с дефолтами ---
    old_price: Optional[float] = Field(
        default=None,
        gt=0,
        le=100000,
        description="Старая цена"
    )
    discount: str = Field(
        default="",
        max_length=20,
        description="Скидка: '-20%' или пустая строка"
    )
    image_url: str = Field(
        default="",
        description="URL картинки"
    )
    brand: Brand = Field(
        default_factory=lambda: Brand(name="Yves Rocher"),
        description="Вложенная модель бренда"
    )

    # --- служебное поле для предупреждений ---
    _warnings: List[str] = []

    # ============================================================
    # FIELD VALIDATORS
    # ============================================================
    @field_validator("name")
    @classmethod
    def name_not_only_spaces(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Название не может состоять только из пробелов")
        return stripped

    @field_validator("link")
    @classmethod
    def link_must_be_yves(cls, v: str) -> str:
        if not v.startswith("https://www.yves-rocher.ru"):
            raise ValueError("Ссылка должна начинаться с https://www.yves-rocher.ru")
        return v

    @field_validator("discount")
    @classmethod
    def discount_format(cls, v: str) -> str:
        if v and not v.startswith("-"):
            raise ValueError("Скидка должна начинаться с '-'")
        return v

    # ============================================================
    # MODEL VALIDATOR
    # ============================================================
    @model_validator(mode="after")
    def check_warnings(self):
        self._warnings = []

        if self.price < 50:
            self._warnings.append(f"Очень низкая цена: {self.price}₽")

        if self.old_price is not None and self.old_price < self.price:
            self._warnings.append(
                f"Старая цена ({self.old_price}) меньше новой ({self.price})"
            )

        if self.discount and not self.old_price:
            self._warnings.append("Есть скидка, но нет старой цены")

        return self

    @property
    def warnings(self) -> List[str]:
        return self._warnings

    def is_warning(self) -> bool:
        return len(self._warnings) > 0