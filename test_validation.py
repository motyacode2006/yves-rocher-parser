"""Тест валидации Pydantic на специально созданных плохих и хороших записях."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pydantic import ValidationError
from models import Product


bad_test_data = [
    {"category": "Лицо", "price": 1000, "link": "https://www.yves-rocher.ru/products/xxx"},
    {"category": "Лицо", "name": "Крем", "price": 1000, "link": "https://www.yves-rocher.ru/products/xxx"},
    {"category": "Лицо", "name": "Крем", "price": -100, "link": "https://www.yves-rocher.ru/products/xxx"},
    {"category": "Лицо", "name": "     ", "price": 1000, "link": "https://www.yves-rocher.ru/products/xxx"},
    {"category": "Лицо", "name": "Крем", "price": 1000, "link": "https://www.ozon.ru/products/xxx"},
    {"category": "Игрушки", "name": "Крем", "price": 1000, "link": "https://www.yves-rocher.ru/products/xxx"},
]

good_test_data = [
    {
        "category": "Лицо", "name": "Крем Hydra", "price": 1879,
        "old_price": 2360, "discount": "-20%",
        "link": "https://www.yves-rocher.ru/products/krem",
        "image_url": "https://img.yves-rocher.ru/krem.jpg",
    },
]


print("Тест 1. Некорректные данные (должны быть отбракованы)")

for i, raw in enumerate(bad_test_data, 1):
    try:
        Product(**raw)
        print(f"  {i}. [FAIL] запись прошла валидацию")
    except ValidationError as e:
        first_err = e.errors()[0]
        field = first_err["loc"][0] if first_err["loc"] else "?"
        print(f"  {i}. [OK]   отбраковано: [{field}] {first_err['msg']}")

print("\nТест 2. Корректные данные (должны пройти)")

for i, raw in enumerate(good_test_data, 1):
    try:
        p = Product(**raw)
        status = "[WARN]" if p.is_warning() else "[OK]  "
        print(f"  {i}. {status} {p.name} — {p.price} руб.")
        if p.is_warning():
            for w in p.warnings:
                print(f"       {w}")
    except ValidationError as e:
        print(f"  {i}. [FAIL] хорошая запись отбракована: {e.errors()[0]['msg']}")

print("\nТест завершён.")