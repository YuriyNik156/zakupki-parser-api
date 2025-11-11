import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def get_purchases_selenium(
    fz="44",
    max_pages=10,
    region=None,
    price_min=None,
    price_max=None,
    date_from=None,
    date_to=None
):
    """
    Парсинг закупок с zakupki.gov.ru через Selenium.
    fz — "44" или "223"
    max_pages — сколько страниц обойти
    region — код региона (например, 5277340 — Москва)
    price_min / price_max — диапазон цен
    date_from / date_to — даты публикации (в формате ДД.ММ.ГГГГ)
    """
    if fz not in ("44", "223"):
        raise ValueError("fz должно быть '44' или '223'")

    base_url = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=&"
    filters = [f"fz{fz}=on"]

    if region:
        filters.append(f"regions={region}")
    if price_min:
        filters.append(f"priceFrom={price_min}")
    if price_max:
        filters.append(f"priceTo={price_max}")
    if date_from:
        filters.append(f"publishDateFrom={date_from}")
    if date_to:
        filters.append(f"publishDateTo={date_to}")

    url_base = base_url + "&".join(filters)

    print(f"\n🚀 Запуск парсинга закупок по {fz}-ФЗ (до {max_pages} страниц)...")
    print(f"Фильтры: {filters}")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    purchases = []

    for page in range(1, max_pages + 1):
        url = f"{url_base}&pageNumber={page}"
        print(f"\n📄 Парсинг страницы {page}: {url}")
        driver.get(url)

        try:
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search-registry-entry-block"))
            )
        except Exception as e:
            print(f"⚠️ Не удалось загрузить страницу {page}: {e}")
            break

        time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, ".search-registry-entry-block")
        count = len(cards)
        print(f"Найдено {count} закупок на странице {page}")

        if count == 0:
            print("❌ Похоже, больше страниц нет или сайт ограничил показ.")
            break

        for card in cards:
            try:
                number_el = card.find_element(By.CSS_SELECTOR, ".registry-entry__header-mid__number a")
                number = number_el.text.strip()
                link = number_el.get_attribute("href")

                customer = card.find_element(By.CSS_SELECTOR, ".registry-entry__body-href").text.strip()
                subject = card.find_element(By.CSS_SELECTOR, ".registry-entry__body-value").text.strip()
                amount_el = card.find_element(By.CSS_SELECTOR, ".price-block__value")
                amount = amount_el.text.strip() if amount_el else "—"

                date_blocks = card.find_elements(By.CSS_SELECTOR, ".data-block__value")
                dates = ", ".join([d.text.strip() for d in date_blocks]) if date_blocks else "—"

                status_el = card.find_elements(By.CSS_SELECTOR, ".registry-entry__header-top__title")
                status = status_el[0].text.strip() if status_el else "—"

                purchases.append({
                    "Номер закупки": number,
                    "Заказчик": customer,
                    "Предмет": subject,
                    "Сумма": amount,
                    "Даты": dates,
                    "Статус": status,
                    "Ссылка": link
                })
            except Exception:
                continue

        # Увеличим паузу между страницами, чтобы избежать блокировок
        time.sleep(3)

    driver.quit()
    print(f"\n✅ Парсинг по {fz}-ФЗ завершён. Всего собрано: {len(purchases)} записей.")
    return purchases


def save_to_excel(data, fz="44"):
    """Сохранение данных в Excel"""
    filename = f"zakupki_{fz}.xlsx"
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"💾 Сохранено {len(data)} записей в {filename}")


if __name__ == "__main__":
    # === Парсинг по 44-ФЗ ===
    purchases_44 = get_purchases_selenium(
        fz="44",
        max_pages=10,
        region="5277340",        # Москва
        price_min=1000000,
        price_max=10000000,
        date_from="01.09.2025",
        date_to="10.11.2025"
    )
    if purchases_44:
        save_to_excel(purchases_44, fz="44")

    # === Парсинг по 223-ФЗ ===
    purchases_223 = get_purchases_selenium(
        fz="223",
        max_pages=10,
        region="5277340",        # Москва
        price_min=1000000,
        price_max=10000000,
        date_from="01.09.2025",
        date_to="10.11.2025"
    )
    if purchases_223:
        save_to_excel(purchases_223, fz="223")
