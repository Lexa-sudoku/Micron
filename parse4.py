import asyncio
import json
from typing import Any
import aiohttp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_stealth import stealth
import random


def configure_driver(proxy: str = None) -> WebDriver:
    chrome_driver = './chromedriver.exe'  # Путь к драйверу
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Rotate user-agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    user_agent = random.choice(user_agents)
    chrome_options.add_argument(f"user-agent={user_agent}")

    # Add proxy if provided
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')

    driver = webdriver.Chrome(service=Service(chrome_driver), options=chrome_options)

    # Apply stealth settings
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    return driver


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        return await response.text()


async def save_json(arr, filename):
    with open(f"{filename}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(arr, ensure_ascii=False))
        f.close()


async def parse_platan(link: str) -> list[Any] | dict[str, list[dict[str, str | None | Any]]]:
    driver = configure_driver()
    driver.get(link)

    try:
        results_text = driver.find_element(By.XPATH, "//h1[@class='text-success mb-5 pl-3 pl-md-0']/sub").text
        if not results_text:
            driver.quit()
            return {'ПЛАТАН': []}
    except Exception as e:
        print("Ошибка при поиске элемента с количеством результатов:", e)

    # Получаем все карточки товаров
    products = driver.find_elements(By.XPATH, "//tr[@class='border-bottom']")

    parsed_products = []

    for product in products:
        try:
            # Название товара
            name_element = product.find_element(By.XPATH, ".//td[@class='w-35']/a[@class='link']")
            name = name_element.text.strip()
            relative_url = name_element.get_attribute("href")
            base_url = "https://www.platan.ru"
            full_url = relative_url if relative_url.startswith("http") else base_url + relative_url

            # Таблица цен
            price_rows = product.find_elements(By.XPATH, ".//td/table/tbody/tr")
            price_list = []
            for row in price_rows:
                price = row.find_element(By.XPATH, ".//td[1]").text.strip(' /шт')
                quantity = row.find_element(By.XPATH, ".//td[2]").text
                price_list.append({"price": price, "quantity": quantity})
            price_string = ''
            for price_info in price_list:
                price_string += f"\n  {price_info['quantity']}. — {price_info['price']} руб./шт."

            # Количество на складе (обновленный XPath для большего покрытия)
            availability = ""
            try:
                availability = product.find_element(By.XPATH,
                                                    ".//td[contains(., 'шт.') or contains(., 'под заказ') or contains(., 'раб.дня')]").text
            except Exception as e:
                availability = "Не указано"
            availability_string = availability.split('\n')
            if availability == "Не указано":
                pass
            elif len(availability_string) == 1:
                availability = "Нет в наличии"
            else:
                availability_time = availability_string[1].strip(')').strip('(')
                availability_count = availability_string[0].strip().strip('.')
                availability = f"{availability_count}, {availability_time}"

            # Собираем информацию в словарь
            parsed_products.append({
                "name": name,
                "url": full_url,
                "price": price_string,
                "availability": availability
            })
        except Exception as e:
            print(f"Ошибка при парсинге товара: {e}")

    driver.quit()
    return {'ПЛАТАН': parsed_products}


async def parse_dip8(link: str, proxy: str = None) -> dict[str, list[dict[str, str | None | Any]]] | None:
    driver = configure_driver(proxy)
    driver.get(link)

    try:
        # Получаем все карточки товаров
        products = driver.find_elements(By.XPATH,
                                        "//div[contains(@class, 'list_item_wrapp') and contains(@class, 'item_wrap')]")

        parsed_products = []

        for product in products:
            try:
                try:
                    # Название товара
                    name = product.find_element(By.XPATH, ".//*[contains(@class, 'dark_link')]").text
                    relative_url = driver.find_element(By.XPATH, "//a[contains(@class, 'dark_link')]").get_attribute(
                        "href")  # Достаем ссылку
                    base_url = "https://dip8.ru"
                    full_url = base_url + relative_url if relative_url.startswith("/") else relative_url
                except:
                    name = product.find_element(By.XPATH, ".//*[contains(@class, 'offer_link')]").text
                    full_url = link
                try:
                    # Количество на складе
                    availability = product.find_element(By.XPATH, ".//*[contains(@class, 'yellow')]").text + '.'
                except:
                    availability = product.find_element(By.XPATH, ".//*[contains(@class, 'fa fa-check yellow')]").text + '.'
                if availability.endswith('0 шт'):
                    availability = 'Нет в наличии'

                # Таблица цен
                price_list = []
                try:
                    price_rows = product.find_elements(By.XPATH, ".//div[contains(@class, 'price_wrapper_block')]")
                    for row in price_rows:
                        try:
                            price = row.find_element(By.XPATH, ".//span[contains(@class, 'price_value')]").text
                            quantity = row.find_element(By.XPATH, ".//div[contains(@class, 'price_interval')]").text
                            price_list.append({"price": price, "quantity": quantity})
                        except Exception as e:
                            print(f"Ошибка при парсинге цены: {e}")
                            price_list.append({"price": "-", "quantity": "-"})
                except Exception as e:
                    print(f"Ошибка при поиске цен: {e}")
                    price_list.append({"price": "-", "quantity": "-"})
                price_string = ''
                for price_info in price_list:
                    price = price_info['price'].replace(' ', '')
                    if price_info["quantity"] == "от 1":
                        price_info['quantity'] = f"{price_info['quantity']} шт"
                    price_string += f"\n  {price_info['quantity']} шт. — {price} руб./шт."

                # Собираем информацию в словарь
                parsed_products.append({
                    "name": name,
                    "url": full_url,
                    "availability": availability,
                    "price": price_string
                })
            except Exception as e:
                print(f"Ошибка при парсинге товара: {e}")

        driver.quit()

        return {'DIP8': parsed_products}
    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        driver.quit()


async def parse_mirecom(link: str) -> dict[str, list[dict[str, str | list[str] | None]]] | None:
    driver = configure_driver()
    driver.get(link)

    try:
        # Expand all sections by clicking on the headers
        headers = driver.find_elements(By.XPATH, "//div[@class='search-item line shining']/h2")
        for header in headers[1:]:
            driver.execute_script("arguments[0].click();", header)
            await asyncio.sleep(0.5)  # Wait for the content to load

        # Получаем все карточки товаров
        products = driver.find_elements(By.XPATH, '//*[@class="line"]')

        parsed_products = []
        for product in products:
            try:
                # Получаем ссылку на товар
                url = product.find_element(By.TAG_NAME, 'a').get_attribute('href')

                product = product.text.split("\n")

                # Получаем наименование товара
                if len(product[0]) > 10:
                    name = product[0]
                else:
                    name = product[:2]

                # Получаем цену и количество товара
                if product[-1] == 'Нет в наличии':
                    availability = product[-1]
                    price = '-'
                else:
                    availability = product[-4]
                    price = f"\n  от 1 шт. — {product[-3].strip(' р.') + '.00'} руб./шт."

                # Собираем информацию в словарь
                parsed_products.append({
                    "name": name,
                    "availability": availability,
                    "price": price,
                    "url": url
                })
            except Exception as e:
                print(f"Ошибка при парсинге товара: {e}")

        driver.quit()
        return {'МИРЭКОМ': parsed_products}
    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        driver.quit()


async def parse_radiocomplect(link: str) -> dict[str, list[dict[str, str | None]]] | None:
    driver = configure_driver()
    driver.get(link)
    driver.set_window_size(1900, 1200)
    try:
        # Получаем все карточки товаров
        products = driver.find_elements(By.XPATH, "//table[contains(@class, 'prds__item_tab')]")

        parsed_products = []

        for product in products:
            try:
                # Название товара
                name = product.find_element(By.XPATH, ".//a[@class='prds__item_name']/span").text.strip()
                relative_url_element = product.find_element(By.XPATH, ".//a[contains(@class, 'prds__item_name')]")
                relative_url = relative_url_element.get_attribute("href")
                base_url = "https://radiocomplect.ru"
                full_url = base_url + relative_url if relative_url.startswith("/") else relative_url

                # Цена
                price = product.find_element(By.XPATH,
                                             ".//div[contains(@class, 'prd_form__price')]/span[contains(@class, 'prd_form__price_val')]").text.strip()
                price_string = f'\n  от 1 шт. — {price}.00 руб./шт.'

                # Наличие
                availability = product.find_element(By.XPATH,
                                                    ".//span[contains(@class, 'prd_form__q_ex')]").text.strip().title()

                # Собираем информацию в словарь
                parsed_products.append({
                    "name": name,
                    "url": full_url,
                    "price": price_string,
                    "availability": availability
                })
            except Exception as e:
                print(f"Ошибка при парсинге товара: {e}")

        driver.quit()
        return {'RADIOCOMPLECT': parsed_products}
    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        driver.quit()


async def parse_chipster(link: str) -> list[dict[str, str]] | None:
    driver = configure_driver()
    driver.get(link)

    try:
        # Получаем все карточки товаров
        products = driver.find_elements(By.XPATH, "//div[contains(@class, 'item-info-wrap')]")

        parsed_products = []

        for product in products:
            try:
                # Название товара
                name = product.find_element(By.XPATH, ".//h3/a").text.strip()

                # Артикул
                article = product.find_element(By.XPATH, ".//span[@class='articul']/b").text.strip()

                # Цена
                price = product.find_element(By.XPATH, ".//div[@class='price']/span[@class='price-num']").text.strip()

                # Наличие
                availability = product.find_element(By.XPATH, ".//span[@class='avl']/span").text.strip()

                # Собираем информацию в словарь
                parsed_products.append({
                    "name": name,
                    "article": article,
                    "price": price,
                    "availability": availability
                })
            except Exception as e:
                print(f"Ошибка при парсинге товара: {e}")

        driver.quit()

        return parsed_products
    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        driver.quit()


async def parse_chipdip(link: str) -> dict[str, list[dict[str, str | Any]]] | None:
    driver = configure_driver()
    driver.get(link)
    driver.refresh()
    try:
        # Get all product cards
        products = driver.find_elements(By.XPATH, "//table[@id='itemlist']/tbody/tr[not(@class='group-header-wrap')]")
        parsed_products = []
        for product in products:
            try:
                # Product id
                product_id = product.get_attribute("id").strip('item')
                if not product_id:
                    continue
                # Product name
                title = product.find_element(By.TAG_NAME, "a").text

                # Product URL
                url = f"https://www.chipdip.ru/product0/{product_id}"

                # Main price
                price_element = product.find_element(By.XPATH, f"//span[@id='price_{product_id}']")
                price = price_element.text.strip().replace(" ", "")
                if price[-3] != '.':
                    price += ".00"
                price_string = f'\n  от 1 шт. — {price} руб./шт.'
                try:
                    add_info_elements = product.find_elements(By.CSS_SELECTOR, 'div.addprice-w div.addprice')
                    for add_info_element in add_info_elements:
                        wholesale_prices = add_info_element.text.strip().split(" шт. — ")
                        wholesale_availability = wholesale_prices[0].strip("от ")
                        wholesale_price = wholesale_prices[1].strip(" руб.").replace(' ', '')
                        price_string += f'\n  от {wholesale_availability} шт. — {wholesale_price}'
                        if price_string[-3] != '.':
                            price_string += ".00 руб./шт."
                        else:
                            price_string += " руб./шт."
                except:
                    pass

                # Availability
                try:
                    availability = product.find_element(By.CSS_SELECTOR, 'span.item__avail').text.split(', ')
                    availability_count = availability[1].strip('.')
                    availability_time = availability[0]
                    availability = f"{availability_count}, {availability_time}"
                except:
                    availability = "Нет в наличии"

                # Wholesale prices

                # Collect information in a dictionary
                parsed_products.append({
                    "name": title,
                    "url": url,
                    "availability": availability,
                    "price": price_string,
                })
            except Exception as e:
                print(f"Ошибка при извлечении данных: {e}")

        driver.quit()
        return {'ChipDip': parsed_products}
    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        driver.quit()


async def main():
    # Получение ввода от пользователя
    product_name = input("Введите название товара: ")

    # Конструирование URL для каждой функции
    link_platan = f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}"
    link_dip8 = f"https://dip8.ru/shop/?q={product_name}"
    link_mirekom = f"https://mirekom.ru/price/find.php?text={product_name}"
    link_radiocomplect = f"https://radiocomplect.ru/search/?searchstring={product_name}"
    link_chipster = f"https://chipster.ru/search.html?q={product_name}"
    link_chipdip = f"https://www.chipdip.ru/search?searchtext={product_name}"

    # Создание сессии aiohttp
    async with aiohttp.ClientSession() as session:
        # Запуск всех функций параллельно
        results = await asyncio.gather(
            parse_platan(link_platan),
            parse_dip8(link_dip8),
            parse_mirecom(link_mirekom),
            parse_radiocomplect(link_radiocomplect),
            # parse_CHIPSTER(link_chipster),
            parse_chipdip(link_chipdip)
        )

        # Обработка результатов в json
        output_results = {}
        for elem in results:
            parse_site = list(elem.keys())[0]
            parse_result = list(elem.values())[0]
            output_results[parse_site] = parse_result

        # Вывод результатов
        for site, result in output_results.items():
            print(f"\n\nРезультаты для {site}:")
            if result:
                for product in result:
                    print(f"Название: {product['name']}")
                    print(f"Ссылка: {product['url']}")
                    print(f"Цена: {product['price']}")
                    print(f"Наличие: {product['availability']}")
                    print('-' * 40)
            else:
                print("Результатов не найдено")

        # Вызов функции parse_chipster
        # print("Результаты для CHIPSTER:")
        # if products_chipster:
        #     for product in products_chipster:
        #         print(f"Название: {product['name']}")
        #         print(f"Ссылка: {product['url']}")
        #         print(f"Артикул: {product['article']}")
        #         print(f"Цена: {product['price']} руб.")
        #         print(f"Наличие: {product['availability']}")
        #         print('-' * 40)
        # else:
        #     print("Результатов не найдено")


# Запуск основного асинхронного цикла
if __name__ == "__main__":
    asyncio.run(main())
