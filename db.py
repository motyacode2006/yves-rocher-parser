import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "user":     "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "dbname":   "yves_rocher",
    "client_encoding": "utf8",
}


def get_connection():
    """Открывает соединение с PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)


def create_table_if_not_exists():
    """Создаёт таблицу products (без колонки rating)."""
    sql = """
    CREATE TABLE IF NOT EXISTS products (
        id              SERIAL PRIMARY KEY,
        category        VARCHAR(100),
        name            TEXT NOT NULL,
        price           NUMERIC(10, 2),
        old_price       NUMERIC(10, 2),
        discount        VARCHAR(20),
        link            TEXT,
        image_url       TEXT,
        brand_name      VARCHAR(100),
        brand_country   VARCHAR(100),
        parsed_at       TIMESTAMP DEFAULT NOW()
    );
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def clear_products():
    """Очищает таблицу перед новым парсингом."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE products RESTART IDENTITY;")
        conn.commit()


def insert_products(products):
    """Вставляет список товаров одной пачкой."""
    if not products:
        return 0

    sql = """
    INSERT INTO products
        (category, name, price, old_price, discount,
         link, image_url, brand_name, brand_country)
    VALUES %s
    """

    values = [
        (p["category"], p["name"], p["price"], p["old_price"],
         p["discount"], p["link"], p["image_url"],
         p.get("brand_name", ""), p.get("brand_country", ""))
        for p in products
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, values)
        conn.commit()

    return len(values)