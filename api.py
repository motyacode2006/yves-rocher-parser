"""
FastAPI-приложение поверх PostgreSQL.
"""
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from psycopg2.extras import RealDictCursor

import db
from api_schemas import ProductOut, CategoryStats, OverallStats


app = FastAPI(
    title="Yves Rocher Parser API",
    description="API для доступа к данным парсера Yves Rocher",
    version="1.0.0",
)


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
def query_all(sql: str, params: tuple = ()) -> List[dict]:
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def query_one(sql: str, params: tuple = ()) -> Optional[dict]:
    with db.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None


def normalize_row(row: dict) -> dict:
    """Приводим Decimal → float, datetime → str для Pydantic."""
    if not row:
        return row
    result = dict(row)
    if result.get("price") is not None:
        result["price"] = float(result["price"])
    if result.get("old_price") is not None:
        result["old_price"] = float(result["old_price"])
    if result.get("parsed_at") is not None:
        result["parsed_at"] = str(result["parsed_at"])
    return result


# ============================================================
# ЭНДПОИНТ 1. Корень
# ============================================================
@app.get("/")
def root():
    return {
        "message": "Yves Rocher Parser API",
        "docs": "/docs",
        "endpoints": [
            "/products",
            "/products/{id}",
            "/stats",
            "/stats/category",
            "/categories",
            "/search?q=...",
        ],
    }


# ============================================================
# ЭНДПОИНТ 2. Все товары (с фильтрами)
# ============================================================
@app.get("/products", response_model=List[ProductOut])
def get_products(
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    sql = "SELECT * FROM products WHERE 1=1"
    params = []

    if category:
        sql += " AND category = %s"
        params.append(category)
    if min_price is not None:
        sql += " AND price >= %s"
        params.append(min_price)
    if max_price is not None:
        sql += " AND price <= %s"
        params.append(max_price)

    sql += " ORDER BY id LIMIT %s"
    params.append(limit)

    rows = query_all(sql, tuple(params))
    return [normalize_row(r) for r in rows]


# ============================================================
# ЭНДПОИНТ 3. Один товар по id
# ============================================================
@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    row = query_one("SELECT * FROM products WHERE id = %s", (product_id,))
    if not row:
        raise HTTPException(status_code=404, detail=f"Товар с id={product_id} не найден")
    return normalize_row(row)


# ============================================================
# ЭНДПОИНТ 4. Общая статистика
# ============================================================
@app.get("/stats", response_model=OverallStats)
def get_stats():
    overall = query_one("""
        SELECT 
            COUNT(*) AS total_products,
            COALESCE(AVG(price), 0) AS avg_price,
            COALESCE(MAX(price), 0) AS max_price,
            COALESCE(MIN(price), 0) AS min_price
        FROM products;
    """)

    categories = query_all("""
        SELECT 
            category,
            COUNT(*) AS total,
            COALESCE(AVG(price), 0) AS avg_price,
            COALESCE(MIN(price), 0) AS min_price,
            COALESCE(MAX(price), 0) AS max_price
        FROM products
        GROUP BY category
        ORDER BY total DESC;
    """)

    return {
        "total_products": overall["total_products"],
        "avg_price": round(float(overall["avg_price"]), 2),
        "max_price": float(overall["max_price"]),
        "min_price": float(overall["min_price"]),
        "categories": [
            {
                "category": c["category"],
                "total": c["total"],
                "avg_price": round(float(c["avg_price"]), 2),
                "min_price": float(c["min_price"]),
                "max_price": float(c["max_price"]),
            }
            for c in categories
        ],
    }


# ============================================================
# ЭНДПОИНТ 5. Статистика по категориям
# ============================================================
@app.get("/stats/category", response_model=List[CategoryStats])
def get_stats_by_category():
    rows = query_all("""
        SELECT 
            category,
            COUNT(*) AS total,
            AVG(price) AS avg_price,
            MIN(price) AS min_price,
            MAX(price) AS max_price
        FROM products
        GROUP BY category
        ORDER BY total DESC;
    """)
    return [
        {
            "category": r["category"],
            "total": r["total"],
            "avg_price": round(float(r["avg_price"]), 2),
            "min_price": float(r["min_price"]),
            "max_price": float(r["max_price"]),
        }
        for r in rows
    ]


# ============================================================
# ЭНДПОИНТ 6. Список категорий
# ============================================================
@app.get("/categories")
def get_categories():
    rows = query_all("""
        SELECT category, COUNT(*) AS count
        FROM products
        GROUP BY category
        ORDER BY count DESC;
    """)
    return {"categories": rows}


# ============================================================
# ЭНДПОИНТ 7. Поиск по названию
# ============================================================
@app.get("/search", response_model=List[ProductOut])
def search_products(
    q: str = Query(..., min_length=2, description="Поисковый запрос"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Поиск товаров по подстроке в названии (регистронезависимо).
    
    Пример: /search?q=гель
    """
    sql = """
        SELECT * FROM products
        WHERE name ILIKE %s
        ORDER BY id
        LIMIT %s;
    """
    rows = query_all(sql, (f"%{q}%", limit))
    return [normalize_row(r) for r in rows]