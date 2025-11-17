import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def create_driver():
    """Создание ChromeDriver в отдельной функции — удобно для FastAPI."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def get_purchases_selenium(
        fz="44",
        max_pages=10,
        region=None,
        price_min=None,
        price_max=None,
        date_from=None,
        date_to=None
):
    """Универсальный парсер — работает в консоли и FastAPI."""

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

    driver = create_driver()
    purchases = []

    for page in range(1, max_pages + 1):
        url = f"{url_base}&pageNumber={page}"
        driver.get(url)

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".search-registry-entry-block")
                )
            )
        except Exception:
            break

        cards = driver.find_elements(By.CSS_SELECTOR, ".search-registry-entry-block")
        if not cards:
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
                dates = ", ".join(d.text.strip() for d in date_blocks)

                status_el = card.find_elements(By.CSS_SELECTOR, ".registry-entry__header-top__title")
                status = status_el[0].text.strip() if status_el else "—"

                purchases.append({
                    "number": number,
                    "customer": customer,
                    "subject": subject,
                    "amount": amount,
                    "dates": dates,
                    "status": status,
                    "link": link,
                })
            except Exception:
                continue

        time.sleep(2)

    driver.quit()
    return purchases


def save_to_excel(data, fz="44"):
    df = pd.DataFrame(data)
    filename = f"zakupki_{fz}.xlsx"
    df.to_excel(filename, index=False)
    print(f"💾 Сохранено {len(data)} записей в {filename}")


# === CLI режим ===

if __name__ == "__main__":
    fz = "44"
    data = get_purchases_selenium(
        fz=fz,
        max_pages=5,
        region="5277340",
        price_min=1000000,
        price_max=10000000,
        date_from="01.09.2025",
        date_to="10.11.2025"
    )

    print(f"Собрано записей: {len(data)}")
    if data:
        save_to_excel(data, fz)
