# Yves Rocher Parser → PostgreSQL → FastAPI

ETL-пайплайн для сбора данных о товарах с сайта Yves Rocher,
валидации через Pydantic, загрузки в PostgreSQL и предоставления
доступа через REST API.

## Что делает проект

1. **Extract** — Selenium открывает каталог «Тело и гигиена» и в цикле
   кликает «Показать ещё», пока не загрузит все товары (256 штук).
2. **Transform** — BeautifulSoup парсит HTML, Pydantic валидирует каждую
   запись: типы, ограничения, кастомные проверки. Записи делятся на
   `good` / `warning` / `bad`.
3. **Load** — валидные данные батч-вставкой уходят в PostgreSQL.
   Параллельно сохраняются Excel-файлы и JSON-логи.
4. **API** — поверх БД поднят FastAPI с 7 эндпоинтами.

## Стек

- Python 3.12
- Selenium 4 — браузерная автоматизация
- BeautifulSoup4 — парсинг HTML
- Pydantic 2 — валидация данных
- PostgreSQL — хранение
- FastAPI — REST API
- openpyxl — экспорт в Excel
- python-dotenv — хранение секретов

## Структура проекта

    parser_homework/
    ├── parser.py           # ETL-пайплайн: сбор и валидация данных
    ├── models.py           # Pydantic-модели (Product, Brand, CategoryEnum)
    ├── db.py               # работа с PostgreSQL (psycopg2)
    ├── api.py              # FastAPI-приложение
    ├── api_schemas.py      # Pydantic-схемы для API
    ├── test_db.py          # проверка подключения к БД
    ├── test_validation.py  # тесты валидации Pydantic
    ├── requirements.txt    # зависимости
    └── .env                # пароль от БД (не в репозитории)

## Установка

1. **Клонировать репозиторий:**

        git clone https://github.com/motyacode2006/yves-rocher-parser.git
        cd yves-rocher-parser

2. **Создать виртуальное окружение и активировать:**

        python -m venv .venv
        .venv\Scripts\Activate     # Windows
        source .venv/bin/activate  # Linux/Mac

3. **Установить зависимости:**

        pip install -r requirements.txt

4. **Создать базу данных в PostgreSQL:**

        CREATE DATABASE yves_rocher;

5. **Создать файл `.env` в корне проекта:**

        DB_PASSWORD=ваш_пароль_от_postgres

## Запуск

### Парсинг данных

    python parser.py

Скрипт:
- откроет каталог Yves Rocher,
- соберёт все товары,
- провалидирует через Pydantic,
- загрузит в PostgreSQL,
- сохранит `good.xlsx`, `bad.xlsx`, `warning.xlsx` и JSON-логи.

### REST API

    python -m uvicorn api:app --reload

Открыть Swagger UI:

    http://localhost:8000/docs

## Эндпоинты API

| Метод | URL | Описание |
|---|---|---|
| GET | `/products` | Список товаров с фильтрами |
| GET | `/products/{id}` | Один товар по id |
| GET | `/stats` | Общая статистика |
| GET | `/stats/category` | Статистика по категориям |
| GET | `/categories` | Список категорий |
| GET | `/search?q=...` | Поиск по названию |

Примеры:

    GET /products?limit=10
    GET /products?category=Тело и гигиена&min_price=1000
    GET /search?q=гель

## Валидация через Pydantic

Модель `Product` содержит:
- 9 типизированных полей (`str`, `float`, `Optional[float]`, `Enum`);
- ограничения через `Field` (`gt=0`, `le=5`, `min_length`, `max_length`);
- значения по умолчанию (`old_price=None`, `discount=""`);
- три `@field_validator` — проверки имени, ссылки, скидки;
- `@model_validator` — предупреждения (warning) о подозрительных данных;
- вложенную модель `Brand`.

Записи делятся на три уровня:
- **good** — прошло валидацию без замечаний;
- **warning** — прошло, но есть подозрительные поля;
- **bad** — не прошло, отбрасывается.

## Схема БД

Таблица `products`:

| Колонка | Тип | Описание |
|---|---|---|
| id | SERIAL PRIMARY KEY | Автоинкремент |
| category | VARCHAR(100) | Категория |
| name | TEXT | Название |
| price | NUMERIC(10,2) | Цена |
| old_price | NUMERIC(10,2) | Старая цена |
| discount | VARCHAR(20) | Скидка |
| link | TEXT | Ссылка на товар |
| image_url | TEXT | URL картинки |
| brand_name | VARCHAR(100) | Бренд |
| brand_country | VARCHAR(100) | Страна бренда |
| parsed_at | TIMESTAMP | Время парсинга |

## Лицензия

Учебный проект. Свободное использование.