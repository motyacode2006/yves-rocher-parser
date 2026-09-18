import db

try:
    db.create_table_if_not_exists()
    print("✅ Подключение работает, таблица products создана")
    
    # Проверим, что таблица реально есть
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM products;")
            count = cur.fetchone()[0]
            print(f"Строк в таблице: {count}")
except Exception as e:
    print(f"❌ Ошибка: {e}")