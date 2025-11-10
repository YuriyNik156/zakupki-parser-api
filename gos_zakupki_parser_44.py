import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_purchases_selenium(url="https://zakupki.gov.ru/epz/order/extendedsearch/results.html?searchString=&fz44=on"):
    """Парсинг закупок с сайта zakupki.gov.ru через Selenium"""
    options = Options()
    options.add_argument("--headless")  # без открытия окна браузера
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)

    print("Ожидание загрузки таблицы закупок...")
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".search-registry-entry-block"))
        )
    except Exception as e:
        print("Не удалось загрузить таблицу:", e)
        driver.quit()
        return []

    purchases = []

    # Прокрутка страницы, чтобы подгрузились все элементы
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    cards = driver.find_elements(By.CSS_SELECTOR, ".search-registry-entry-block")
    print(f"Найдено {len(cards)} закупок на странице")

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

    driver.quit()
    return purchases


def save_to_excel(data, filename="zakupki_44.xlsx"):
    """Сохранение данных в Excel"""
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"✅ Сохранено {len(data)} записей в {filename}")


if __name__ == "__main__":
    purchases = get_purchases_selenium()
    if purchases:
        save_to_excel(purchases)
    else:
        print("Данные не найдены.")
