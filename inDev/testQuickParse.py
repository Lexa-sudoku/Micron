import asyncio
from playwright.async_api import async_playwright
import json


# Генерация URL-адресов для всех сайтов
def build_urls(product_name):
    return {
        "platan": f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}",
        "dip8": f"https://dip8.ru/shop/?q={product_name}",
        "mirekom": f"https://mirekom.ru/price/find.php?text={product_name}",
        "radiocomplect": f"https://radiocomplect.ru/search/?searchstring={product_name}",
        "chipdip": f"https://www.chipdip.ru/search?searchtext={product_name}"
    }


# Общая функция для обработки страницы
async def fetch_page_data(browser, link, parser):
    page = await browser.new_page()
    try:
        await page.goto(link, timeout=60000)
        return await parser(page)
    except Exception as e:
        print(f"Ошибка при обработке {link}: {e}")
        return []
    finally:
        await page.close()

# Парсер для сайта Platan
async def parse_platan(page):
    results = []
    print(page.url)
    try:
        if await page.locator("h1.text-success sub").text_content() == '0':
            return results

        rows = await page.locator("tr.border-bottom").all()
        for row in rows:
            try:
                name_el = row.locator("td.w-35 a.link")
                name = await name_el.text_content()
                href = await name_el.get_attribute("href")
                url = f"https://www.platan.ru{href}" if href else ""
                prices = [
                    {"price": await pr.locator("td:nth-child(1)").text_content(),
                     "quantity": await pr.locator("td:nth-child(2)").text_content()}
                    for pr in await row.locator("td table tbody tr").all()
                ]
                availability = await row.locator(
                    "td:has-text('шт.'), td:has-text('под заказ'), td:has-text('раб.дня')"
                ).text_content()
                results.append({
                    "name": name.strip(),
                    "url": url,
                    "prices": [{"price": price.strip(), "quantity": qty.strip()} for price, qty in prices],
                    "availability": availability.strip()
                })
            except Exception as e:
                print(f"Platan parse error: {e}")
    except Exception as e:
        print(f"Platan parse error (outer): {e}")
    return results

# Парсер для сайта Dip8
async def parse_dip8(page):
    products = []
    try:
        cards = await page.locator("div.list_item_wrapp.item_wrap").all()
        for card in cards:
            try:
                name = await card.locator("a.dark_link").text_content()
                href = await card.locator("a.dark_link").get_attribute("href")
                url = f"https://dip8.ru{href}" if href else ""
                prices = [
                    {"price": await block.locator(".price_value").text_content(),
                     "quantity": str(await block.locator(".price_interval").text_content()).replace('\n', '').replace('\t', '')}
                    for block in await card.locator(".price_wrapper_block").all()
                ]
                availability = await card.locator(".yellow").first.text_content()  # Уточнение селектора
                products.append({
                    "name": name.strip(),
                    "url": url,
                    "availability": availability.strip(),
                    "prices": prices
                })
            except Exception as e:
                print(f"DIP8 parse error: {e}")
                return products
    except Exception as e:
        print(f"DIP8 parse error (outer): {e}")
        return products
    return products


# Парсер для сайта MIREKOM
async def parse_mirekom(page):
    parsed = []
    try:
        products = await page.locator("div.itemslist div.itemslist .line").all()
        for prod in products[1:]:
            try:
                if 'Номер' in await prod.inner_text():
                    break
                text = await prod.inner_text()
                lines = text.strip().split("\n")
                name = lines[0] if len(lines[0]) > 10 else ' '.join(lines[:2])
                href = await prod.locator('.ima a').get_attribute("href")
                url = f"https://mirekom.ru{href}"
                availability = lines[-1] if 'Нет в наличии' in lines[-1] else "В наличии " + lines[-4]
                price = 'N/A' if 'Нет в наличии' in lines[-1] else lines[-3].strip(" р.").split()[-1]
                name = ' '.join(name.split('\\')[1:])
                parsed.append({
                    "name": name.strip(),
                    "url": url,
                    "availability": availability.strip(),
                    "price": price.strip()
                })
            except Exception as e:
                print(f"MIREKOM parse error: {e}")
    except Exception as e:
        print(f"MIREKOM parse error (outer): {e}")
    return parsed


# Парсер для сайта RADIOCOMPLECT
async def parse_radiocomplect(page):
    parsed = []
    try:
        await page.wait_for_selector("table.prds__item_tab", timeout=10000)
        tables = await page.locator("table.prds__item_tab").all()
        for table in tables:
            try:
                name = await table.locator("a.prds__item_name span.prds__item_name_in").first.text_content()
                href = await table.locator("a.prds__item_name").first.get_attribute("href")
                url = f"https://radiocomplect.ru{href}"
                price = await table.locator(".prd_form__price_val").first.text_content()
                availability = await table.locator(".prd_form__q_ex").first.text_content()
                parsed.append({
                    "name": name.strip(),
                    "url": url,
                    "price": price.strip(),
                    "availability": availability.strip()
                })
            except Exception as e:
                print(f"Radiocomplect parse error: {e}")
    except Exception as e:
        print(f"Radiocomplect parse error (outer): {e}")
    return parsed


# Парсер для сайта ChipDip
async def parse_chipdip(page):
    parsed = []
    try:
        await page.reload()
        rows = await page.locator("tbody tr.with-hover").all()
        for row in rows:
            try:
                title_el = row.locator("a.link")
                title = await title_el.text_content()
                href = await title_el.get_attribute("href")
                url = f"https://www.chipdip.ru{href}" if href else ""
                product_id = await row.get_attribute("id")
                if product_id:
                    product_id = product_id.replace("item", "")
                else:
                    product_id = ""
                price = await row.locator(f"#price_{product_id}").text_content()
                availability = await row.locator("td.h_av span.item__avail").text_content()
                wholesale = [await block.inner_text() for block in await row.locator("div.addprice-w div.addprice").all()]
                parsed.append({
                    "name": title.strip(),
                    "url": url,
                    "price": price.strip(),
                    "availability": availability.strip(),
                    "wholesale_prices": wholesale
                })
            except Exception as e:
                print(f"ChipDip parse error: {e}")
    except Exception as e:
        print(f"ChipDip parse error (outer): {e}")
    return parsed

# Основная программа
async def main():
    product = input("Введите название товара: ")
    urls = build_urls(product)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        tasks = [
            fetch_page_data(browser, urls["platan"], parse_platan),
            fetch_page_data(browser, urls["dip8"], parse_dip8),
            fetch_page_data(browser, urls["mirekom"], parse_mirekom),
            fetch_page_data(browser, urls["radiocomplect"], parse_radiocomplect),
            fetch_page_data(browser, urls["chipdip"], parse_chipdip)
        ]

        results = await asyncio.gather(*tasks)
        site_names = ["Platan", "DIP8", "MIREKOM", "RADIOCOMPLECT", "ChipDip"]
        to_file = {}
        for name, res in zip(site_names, results):
            print(f"\nРезультаты для {name}:")
            print(json.dumps(res, indent=2, ensure_ascii=False))
            to_file[name] = res
        with open('data.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(to_file, ensure_ascii=False))

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
