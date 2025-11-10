import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def get_purchases_selenium(fz="44", max_pages=10):
    """
    Парсинг закупок с сайта zakupki.gov.ru через Selenium.
    fz — "44" или "223"
    max_pages — сколько страниц обойти (по 10 закупок на страницу примерно)
    """
    if fz not in ("44", "223"):
        raise ValueError("fz должно быть '44' или '223'")

    base_url = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=&"
    url_base = base_url + (f"fz44=on" if fz == "44" else "fz223=on")

    print(f"🚀 Запуск парсинга закупок по {fz}-ФЗ (до {max_pages} страниц)...")

    options = Options()
    options.add_argument("--headless")  # без открытия окна браузера
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
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search-registry-entry-block"))
            )
        except Exception as e:
            print(f"⚠️ Не удалось загрузить страницу {page}: {e}")
            break

        time.sleep(1)

        cards = driver.find_elements(By.CSS_SELECTOR, ".search-registry-entry-block")
        print(f"Найдено {len(cards)} закупок на странице {page}")

        if not cards:
            print("❌ Больше страниц нет или сайт ограничил доступ.")
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

        # Чтобы не нагружать сайт
        time.sleep(2)

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
    # Пример: 10 страниц по каждому ФЗ
    purchases_44 = get_purchases_selenium(fz="44", max_pages=10)
    if purchases_44:
        save_to_excel(purchases_44, fz="44")

    purchases_223 = get_purchases_selenium(fz="223", max_pages=10)
    if purchases_223:
        save_to_excel(purchases_223, fz="223")
