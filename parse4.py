import asyncio
import aiohttp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
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

async def parse_platan(link: str) -> list:
    driver = configure_driver()
    driver.get(link)
    
    try:
        results_text = driver.find_element(By.XPATH, "//h1[@class='text-success mb-5 pl-3 pl-md-0']/sub").text
        if results_text == '0':
            driver.quit()
            return []
    except Exception as e:
        print("Ошибка при поиске элемента с количеством результатов:", e)
    
    # Получаем все карточки товаров
    products = driver.find_elements(By.XPATH, "//tr[@class='border-bottom']")

    parsed_products = []
    
    for product in products:
        try:
            # Название товара
            name = product.find_element(By.XPATH, ".//td/a").text
            
            # Таблица цен
            price_rows = product.find_elements(By.XPATH, ".//td/table/tbody/tr")
            price_list = []
            for row in price_rows:
                price = row.find_element(By.XPATH, ".//td[1]").text
                quantity = row.find_element(By.XPATH, ".//td[2]").text
                price_list.append({"price": price, "quantity": quantity})
            
            # Количество на складе (обновленный XPath для большего покрытия)
            availability = ""
            try:
                availability = product.find_element(By.XPATH, ".//td[contains(., 'шт.') or contains(., 'под заказ') or contains(., 'раб.дня')]").text
            except Exception as e:
                availability = "Не указано"
            
            # Собираем информацию в словарь
            parsed_products.append({
                "name": name,
                "prices": price_list,
                "availability": availability
            })
        except Exception as e:
            print(f"Ошибка при парсинге товара: {e}")
    
    driver.quit()
    return parsed_products

async def parse_dip8(link: str, proxy: str = None) -> list:
    driver = configure_driver(proxy)
    driver.get(link)
    
    try:
        # Получаем все карточки товаров
        products = driver.find_elements(By.XPATH, "//div[contains(@class, 'list_item_wrapp') and contains(@class, 'item_wrap')]")
        
        parsed_products = []
        
        for product in products:
            try:
                # Название товара
                name = product.find_element(By.XPATH, ".//*[contains(@class, 'dark_link')]").text
                                
                # Количество на складе
                availability = product.find_element(By.XPATH, ".//*[contains(@class, 'yellow')]").text
                
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
                            price_list.append({"price": "N/A", "quantity": "N/A"})
                except Exception as e:
                    print(f"Ошибка при поиске цен: {e}")
                    price_list.append({"price": "N/A", "quantity": "N/A"})
                
                # Собираем информацию в словарь
                parsed_products.append({
                    "name": name,
                    "availability": availability,
                    "prices": price_list
                })
            except Exception as e:
                print(f"Ошибка при парсинге товара: {e}")
            
        
        driver.quit()
        
        return parsed_products
    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        driver.quit()

async def parse_MIREKOM(link: str) -> list:
    driver = configure_driver()
    driver.get(link)
    
    try:
        # Expand all sections by clicking on the headers
        headers = driver.find_elements(By.XPATH, "//div[@class='search-item line shining']/h2")
        for header in headers:
            driver.execute_script("arguments[0].click();", header)
            await asyncio.sleep(0.5)  # Wait for the content to load

        # Получаем все карточки товаров
        products = driver.find_elements(By.XPATH, "//div[@class='preview']")
        
        parsed_products = []
        
        for product in products:
            try:
                # Название товара
                name = product.find_element(By.XPATH, ".//div[@class='preview__title']/p[@class='preview__descr']").text.strip()
                                
                # Количество на складе
                availability = product.find_element(By.XPATH, ".//span[@class='preview__quantity']").text.strip()
                
                # Цена
                price = product.find_element(By.XPATH, ".//div[@class='preview__price']").text.strip()

                # Собираем информацию в словарь
                parsed_products.append({
                    "name": name,
                    "availability": availability,
                    "price": price
                })
            except Exception as e:
                print(f"Ошибка при парсинге товара: {e}")
        
        driver.quit()

        return parsed_products
    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        driver.quit()
  
async def parse_RADIOCOMPLECT(link: str) -> list:
    driver = configure_driver()
    driver.get(link)
    
    try:
        # Получаем все карточки товаров
        products = driver.find_elements(By.XPATH, "//table[contains(@class, 'prds__item_tab')]")
        
        parsed_products = []
        
        for product in products:
            try:
                # Название товара
                name = product.find_element(By.XPATH, ".//a[@class='prds__item_name']/span").text.strip()
                
                # Артикул
                article = product.find_element(By.XPATH, ".//tr[contains(@class, 'prd_attrs__tr--code')]/td[contains(@class, 'prd_attrs__td--val')]/span").text.strip()
                
                # Цена
                price = product.find_element(By.XPATH, ".//div[contains(@class, 'prd_form__price')]/span[contains(@class, 'prd_form__price_val')]").text.strip()
                
                # Наличие
                availability = product.find_element(By.XPATH, ".//span[contains(@class, 'prd_form__q_ex')]").text.strip()
                
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

async def parse_CHIPSTER(link: str) -> list:
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

async def parse_ChipDip(link: str) -> list:
    driver = configure_driver()
    driver.get(link)
    driver.refresh()
    try:
        # Get all product cards
        products = driver.find_elements(By.XPATH, "//table[@id='itemlist']/tbody/tr[not(@class='group-header-wrap')]")
        print(f"Found {len(products)} products")  # Debugging statement

        parsed_products = []
        for product in products:
            try:
                if product.text and "в группе" not in product.text:
                    # Product id
                    product_id = product.get_attribute("id").strip('item')
                    
                    # Product name
                    title = product.find_element(By.XPATH, "//a[@class='link']").text
                    print(f"Product name: {title}")  # Debugging statement

                    # Main price
                    price_element = product.find_element(By.XPATH, f"//span[@id='price_{product_id}']")
                    price = price_element.text
                    print(f"Price: {price}")  # Debugging statement

                    # Availability
                    try:
                        availability = product.find_element(By.CSS_SELECTOR, 'span.item__avail').text
                    except:
                        availability = "Нет информации"
                    print(f"Availability: {availability}")  # Debugging statement

                    # Wholesale prices
                    wholesale_prices = []
                    try:
                        add_info_elements = product.find_elements(By.CSS_SELECTOR, 'div.addprice-w div.addprice')
                        for add_info_element in add_info_elements:
                            wholesale_prices.append(add_info_element.text.strip())
                    except:
                        wholesale_prices = ["Нет данных"]
                    print(f"Wholesale prices: {wholesale_prices}")  # Debugging statement

                    # Collect information in a dictionary
                    parsed_products.append({
                        "name": title,
                        "availability": availability,
                        "price": price,
                        "wholesale_prices": wholesale_prices
                    })
            except Exception as e:
                print(f"Ошибка при извлечении данных: {e}")
        
        driver.quit()
        return parsed_products
    except Exception as e:
        print(f"Ошибка при обработке страницы: {e}")
        driver.quit()


async def main():
    # Получение ввода от пользователя
    product_name = input("Введите название товара: ")

    # Конструирование URL для каждой функции
    link_platan = f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}"
    link_dip8 = f"https://dip8.ru/shop/?q={product_name}"
    #link_mirekom = f"https://mirekom.ru/price/find.php?text={product_name}"
    link_radiocomplect = f"https://radiocomplect.ru/search/?searchstring={product_name}"
    link_chipster = f"https://chipster.ru/search.html?q={product_name}"
    link_chipdip = f"https://www.chipdip.ru/search?searchtext={product_name}"

    # Создание сессии aiohttp
    async with aiohttp.ClientSession() as session:
        # Запуск всех функций параллельно
        results = await asyncio.gather(
            parse_platan(link_platan),
            parse_dip8(link_dip8),
            #parse_MIREKOM(link_mirekom),
            parse_RADIOCOMPLECT(link_radiocomplect),
            parse_CHIPSTER(link_chipster),
            parse_ChipDip(link_chipdip)
        )

        # Обработка результатов
        products_platan, products_dip8, products_radiocomplect, products_chipster, products_chipdip = results

        # Вызов функции parse_platan
        print("Результаты для Platan:")
        if products_platan:
            for product in products_platan:
                print(f"Название: {product['name']}")
                for price_info in product['prices']:
                    print(f"Цена: {price_info['price']}, Количество: {price_info['quantity']}")
                print(f"Наличие: {product['availability']}")
                print('-' * 40)
        else:
            print("Результатов не найдено")

        # Вызов функции parse_dip8
        print("Результаты для DIP8:")
        if products_dip8:
            for product in products_dip8:
                print(f"Название: {product['name']}")
                for price_info in product['prices']:
                    print(f"Цена: {price_info['price']}, Количество: {price_info['quantity']}")
                print(f"Наличие: {product['availability']}")
                print('-' * 40)
        else:
            print("Результатов не найдено")

        # Вызов функции parse_MIREKOM
        
        '''print("Результаты для MIREKOM:")
        if products_mirekom:
            for product in products_mirekom:
                print(f"Название: {product['name']}")
                print(f"Цена: {product['price']}")
                print(f"Наличие: {product['availability']}")
                print('-' * 40)
        else:
            print("Результатов не найдено")
'''
        # Вызов функции parse_radiocomplect
        print("Результаты для RADIOCOMPLECT:")
        if products_radiocomplect:
            for product in products_radiocomplect:
                print(f"Название: {product['name']}")
                print(f"Артикул: {product['article']}")
                print(f"Цена: {product['price']} руб.")
                print(f"Наличие: {product['availability']}")
                print('-' * 40)
        else:
            print("Результатов не найдено")

        # Вызов функции parse_chipster
        print("Результаты для CHIPSTER:")
        if products_chipster:
            for product in products_chipster:
                print(f"Название: {product['name']}")
                print(f"Артикул: {product['article']}")
                print(f"Цена: {product['price']} руб.")
                print(f"Наличие: {product['availability']}")
                print('-' * 40)
        else:
            print("Результатов не найдено")

        print("Результаты для ChipDip:")
    if products_chipdip:
        for product in products_chipdip:
            print(f"Название: {product['name']}")
            print(f"Цена: {product['price']}")
            print(f"Наличие: {product['availability']}")
            if product['wholesale_prices']:
                print("Оптовые цены:")
                for wholesale_price in product['wholesale_prices']:
                    print(f"  {wholesale_price}")
            print('-' * 40)
    else:
        print("Результатов не найдено")


# Запуск основного асинхронного цикла
if __name__ == "__main__":
    asyncio.run(main())
