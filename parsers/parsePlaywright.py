from playwright.async_api import async_playwright
import asyncio
import json


def build_urls(product_name):
    return {
        "platan": f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}",
        "dip8": f"https://dip8.ru/shop/?q={product_name}",
        "mirekom": f"https://mirekom.ru/price/find.php?text={product_name}",
        "radiocomplect": f"https://radiocomplect.ru/search/?searchstring={product_name}",
        "chipdip": f"https://www.chipdip.ru/search?searchtext={product_name}"
    }


async def parse_platan(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(link)
        try:
            results_text = await page.locator("h1.text-success sub").text_content()
            if results_text == '0':
                await browser.close()
                return []
        except:
            pass

        rows = await page.locator("tr.border-bottom").all()
        products = []

        for row in rows:
            try:
                name_el = row.locator("td.w-35 a.link")
                name = (await name_el.text_content()).strip()
                href = await name_el.get_attribute("href")
                url = f"https://www.platan.ru{href}" if href else ""

                prices = []
                price_rows = await row.locator("td table tbody tr").all()
                for pr in price_rows:
                    price = await pr.locator("td:nth-child(1)").text_content()
                    qty = await pr.locator("td:nth-child(2)").text_content()
                    prices.append({"price": price.strip(), "quantity": qty.strip()})

                try:
                    availability = await row.locator("td:has-text('шт.'), td:has-text('под заказ'), td:has-text('раб.дня')").text_content()
                except:
                    availability = "Не указано"

                products.append({"name": name, "url": url, "prices": prices, "availability": availability})
            except Exception as e:
                print(f"Platan parse error: {e}")

        await browser.close()
        return products


async def parse_dip8(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link)

        cards = await page.locator("div.list_item_wrapp.item_wrap").all()
        products = []

        for card in cards:
            try:
                name_el = card.locator("a.dark_link")
                name = await name_el.text_content()
                href = await name_el.get_attribute("href")
                url = f"https://dip8.ru{href}" if href else link

                try:
                    availability = await card.locator(".yellow").text_content()
                except:
                    availability = "Не указано"

                prices = []
                price_blocks = await card.locator(".price_wrapper_block").all()
                for block in price_blocks:
                    try:
                        price = await block.locator(".price_value").text_content()
                        qty = await block.locator(".price_interval").text_content()
                        prices.append({"price": price.strip(), "quantity": qty.strip()})
                    except:
                        pass

                products.append({"name": name.strip(), "url": url, "availability": availability, "prices": prices})
            except Exception as e:
                print(f"DIP8 parse error: {e}")

        await browser.close()
        return products


async def parse_MIREKOM(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link)

        await asyncio.sleep(1)
        products = await page.locator(".line").all()
        parsed = []

        for prod in products:
            try:
                text = await prod.inner_text()
                lines = text.strip().split("\n")
                name = lines[0] if len(lines[0]) > 10 else ' '.join(lines[:2])
                url = await prod.locator("a").get_attribute("href")
                url = f"https://mirekom.ru{url}"

                availability = lines[-1] if 'Нет в наличии' in lines[-1] else lines[-4]
                price = 'N/A' if 'Нет в наличии' in lines[-1] else lines[-3].strip(" р.")

                parsed.append({"name": name, "availability": availability, "price": price, "url": url})
            except Exception as e:
                print(f"MIREKOM parse error: {e}")

        await browser.close()
        return parsed


async def parse_RADIOCOMPLECT(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link, timeout=30000)

        # Ждём таблицы, если они есть
        await page.wait_for_selector("table.prds__item_tab", timeout=10000)
        tables = await page.locator("table.prds__item_tab").all()
        parsed = []

        for table in tables:
            try:
                # Избегаем ошибки strict mode, уточняя класс span
                name = await table.locator("a.prds__item_name span.prds__item_name_in").first.text_content(timeout=5000)
                href = await table.locator("a.prds__item_name").first.get_attribute("href")
                url = f"https://radiocomplect.ru{href}"

                price = await table.locator(".prd_form__price_val").first.text_content(timeout=5000)
                availability = await table.locator(".prd_form__q_ex").first.text_content(timeout=5000)

                parsed.append({
                    "name": name.strip(),
                    "url": url,
                    "price": price.strip(),
                    "availability": availability.strip()
                })
            except Exception as e:
                print(f"Radiocomplect parse error: {e}")

        await browser.close()
        return parsed

async def parse_ChipDip(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link, timeout=60000)

        try:
            # Ожидаем загрузки таблицы с товарами
            await page.wait_for_selector("#itemlist tbody tr:not(.group-header-wrap)", timeout=15000)
            rows = await page.locator("#itemlist tbody tr:not(.group-header-wrap)").all()
        except Exception as e:
            print(f"ChipDip: rows not found — {e}")
            await browser.close()
            return []

        parsed = []

        # Обрабатываем строки таблицы
        for row in rows:
            try:
                # Получаем название товара и ссылку
                title_el = row.locator("a.link")
                title = await title_el.text_content()
                href = await title_el.get_attribute("href")
                url = f"https://www.chipdip.ru{href}" if href else ""

                # Получаем ID товара и цену
                product_id = await row.get_attribute("id")
                product_id = product_id.replace("item", "") if product_id else ""
                price_el = row.locator(f"#price_{product_id}")
                price = await price_el.text_content() if price_el else "Цена не указана"

                # Получаем наличие товара
                avail_el = row.locator("td.h_av span.item__avail")
                availability = await avail_el.text_content() if avail_el else "Нет информации"

                # Получаем оптовые цены
                wholesale = []
                addprice_blocks = await row.locator("div.addprice-w div.addprice").all()
                for block in addprice_blocks:
                    price_text = await block.inner_text()
                    wholesale.append(price_text.strip())

                parsed.append({
                    "name": title.strip() if title else "",
                    "url": url,
                    "price": price.strip() if price else "",
                    "availability": availability.strip(),
                    "wholesale_prices": wholesale
                })
            except Exception as e:
                print(f"ChipDip parse error: {e}")

        await browser.close()
        return parsed
    
async def main():
    product = input("Введите название товара: ")
    urls = build_urls(product)

    results = await asyncio.gather(
        parse_platan(urls['platan']),
        parse_dip8(urls['dip8']),
        parse_MIREKOM(urls['mirekom']),
        parse_RADIOCOMPLECT(urls['radiocomplect']),
        parse_ChipDip(urls['chipdip'])
    )

    site_names = ["Platan", "DIP8", "MIREKOM", "RADIOCOMPLECT", "ChipDip"]
    for name, res in zip(site_names, results):
        print(f"\nРезультаты для {name}:")
        if res:
            for r in res:
                print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            print("Результатов не найдено")

if __name__ == "__main__":
    asyncio.run(main())