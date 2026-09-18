import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup
from tqdm import tqdm
import time

import db


CATEGORIES = {
    "Лицо": "https://www.yves-rocher.ru/collections/dlya-litsa",
}

CARD_SELECTOR       = ".product-card"
NAME_SELECTOR       = 'a[class*="titleContainer"] div'
PRICE_SELECTOR      = 'span[class*="PriceLabel_price"]:not([class*="oldPrice"])'
OLD_PRICE_SELECTOR  = 'span[class*="oldPrice"]'
DISCOUNT_SELECTOR   = 'div[class*="priceDiscount"]'
RATING_SELECTOR     = 'button[class*="RatingInput_active"]'
IMAGE_SELECTOR      = "img.picture__img"
LINK_SELECTOR       = 'a[href]'


def parse_price(price_str):
    if not price_str:
        return None
    cleaned = (price_str
               .replace("₽", "")
               .replace(" ", "")
               .replace("\xa0", "")
               .replace(",", ".")
               .strip())
    try:
        return float(cleaned)
    except ValueError:
        return None


def fix_url(link):
    if not link:
        return ""
    if link.startswith("/"):
        return "https://www.yves-rocher.ru" + link
    if not link.startswith("http"):
        return "https://www.yves-rocher.ru/" + link
    return link


def count_cards():
    return len(driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR))


def click_load_more():
    """Кликает по кнопке 'Показать ещё', пока она есть."""
    clicks = 0
    while True:
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Показать ещё')]")
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            time.sleep(0.5)

            before = count_cards()
            btn.click()
            clicks += 1

            try:
                WebDriverWait(driver, 10).until(
                    lambda d: count_cards() > before
                )
                print(f"  Клик {clicks}: карточек стало {count_cards()}")
            except TimeoutException:
                print(f"  Клик {clicks}: новых карточек не появилось, стоп")
                break

        except TimeoutException:
            print(f"  Кнопка 'Показать ещё' исчезла. Всего кликов: {clicks}")
            break

    return count_cards()


# --- Selenium ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Edge(options=options)
wait = WebDriverWait(driver, 15)


# --- Подготовка БД ---
print("🔧 Подготовка базы данных...")
db.create_table_if_not_exists()
db.clear_products()
print("✅ Таблица готова")


# --- Главный цикл ---
all_products = []

for category_name, url in CATEGORIES.items():
    print(f"\n{'=' * 50}")
    print(f"📦 Категория: {category_name}")
    print(f"🔗 {url}")
    print('=' * 50)

    driver.get(url)
    print("Открыл:", driver.title)

    try:
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, CARD_SELECTOR)
        ))
    except TimeoutException:
        print("❌ Карточки не появились. Пропускаю.")
        continue

    total = click_load_more()
    print(f"Всего карточек в DOM: {total}")

    soup = BeautifulSoup(driver.page_source, "lxml")
    cards = soup.select(CARD_SELECTOR)
    print(f"BeautifulSoup нашёл: {len(cards)} карточек")

    for card in tqdm(cards, desc=f"  Парсим {category_name}"):
        try:
            name_tag  = card.select_one(NAME_SELECTOR)
            price_tag = card.select_one(PRICE_SELECTOR)
            old_tag   = card.select_one(OLD_PRICE_SELECTOR)
            disc_tag  = card.select_one(DISCOUNT_SELECTOR)
            img_tag   = card.select_one(IMAGE_SELECTOR)
            link_tag  = card.select_one(LINK_SELECTOR)
            stars     = card.select(RATING_SELECTOR)

            product = {
                "category":  category_name,
                "name":      name_tag.get_text(strip=True)  if name_tag  else "",
                "price":     parse_price(price_tag.get_text(strip=True)) if price_tag else None,
                "old_price": parse_price(old_tag.get_text(strip=True))   if old_tag   else None,
                "discount":  disc_tag.get_text(strip=True) if disc_tag else "",
                "rating":    len(stars),
                "link":      fix_url(link_tag.get("href", "")) if link_tag else "",
                "image_url": img_tag.get("src", "") if img_tag else "",
            }

            if product["name"]:
                all_products.append(product)
        except Exception as e:
            print(f"\n  ⚠️ Ошибка: {e}")


# --- Заливка в БД ---
print(f"\n{'=' * 50}")
print(f"💾 Заливаю в PostgreSQL: {len(all_products)} товаров...")

inserted = db.insert_products(all_products)
print(f"✅ Вставлено строк: {inserted}")

driver.quit()
print("\n🎉 Готово!")