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
        except Exception:
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
                except Exception:
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
                except Exception:
                    availability = "Не указано"

                prices = []
                price_blocks = await card.locator(".price_wrapper_block").all()
                for block in price_blocks:
                    try:
                        price = await block.locator(".price_value").text_content()
                        qty = await block.locator(".price_interval").text_content()
                        prices.append({"price": price.strip(), "quantity": qty.strip()})
                    except Exception:
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
        try:
            await page.goto(link, timeout=1000)
            await page.wait_for_selector(".search-container", timeout=1000)
        except Exception as e:
            print(f"Ошибка загрузки страницы: {e}")
            await browser.close()
            return None

        parsed = []

        try:
            container = page.locator(".search-container").first
            await container.wait_for(timeout=1000)

            lines = await container.locator(".line").all()

            for line in lines:
                try:
                    class_name = await line.get_attribute("class")
                    if "hdr" in class_name:
                        continue

                    name_el = line.locator(".std a")
                    name = await name_el.inner_text()
                    url_part = await name_el.get_attribute("href")
                    url = f"https://mirekom.ru{url_part}"

                    # Наличие
                    try:
                        quantity = await line.locator(".qua").inner_text()
                    except Exception:
                        try:
                            quantity = await line.locator(".un3").inner_text()
                        except Exception:
                            quantity = "Нет в наличии"

                    # Цена
                    try:
                        price = await line.locator(".pri").inner_text()
                        price = price.strip().replace(" р.", "")
                    except Exception:
                        price = "N/A"

                    parsed.append({
                        "name": name,
                        "availability": quantity,
                        "price": price,
                        "url": url,
                    })

                except Exception as e:
                    print(f"Ошибка при разборе товара: {e}")

        except Exception as e:
            print(f"Ошибка при парсинге первой категории: {e}")

        await browser.close()
        return parsed if parsed else None


async def parse_RADIOCOMPLECT(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link, timeout=1000)

        try:
            # Ждем, пока загрузится таблица с продуктами
            await page.wait_for_selector("table.prds__item_tab", timeout=1000)  # Увеличили тайм-аут до 5 секунд
        except Exception as e:
            print(f"Ошибка при ожидании элемента: {e}")
            await browser.close()
            return []  # Если элемент не найден, возвращаем пустой список

        tables = await page.locator("table.prds__item_tab").all()
        parsed = []

        if not tables:
            print("Не найдено таблиц с продуктами.")
            await browser.close()
            return []  # Если таблиц нет, возвращаем пустой список

        for table in tables:
            try:
                name = await table.locator("a.prds__item_name span.prds__item_name_in").first.text_content(timeout=1000)
                href = await table.locator("a.prds__item_name").first.get_attribute("href")
                url = f"https://radiocomplect.ru{href}"

                price = await table.locator(".prd_form__price_val").first.text_content(timeout=1000)
                availability = await table.locator(".prd_form__q_ex").first.text_content(timeout=1000)

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
        await page.goto(link, timeout=1000)  # Уменьшаем таймаут для перехода

        try:
            await page.wait_for_selector("#itemlist tbody tr.with-hover", timeout=1000)  # Увеличиваем таймаут для элементов
            rows = await page.locator("#itemlist tbody tr.with-hover").all()
        except Exception as e:
            print(f"ChipDip: rows not found — {e}")
            await browser.close()
            return []

        parsed = []

        for row in rows:
            try:
                title_el = row.locator("a.link[href]")
                title = await title_el.text_content()
                href = await title_el.get_attribute("href")
                url = f"https://www.chipdip.ru{href}" if href else ""

                price_el = row.locator("span.price-main")
                price = await price_el.text_content() if price_el else "Цена не указана"

                # Получаем первый элемент доступности, если их несколько
                avail_el = row.locator("span.item__avail").first  # Здесь используем `.first()` для выбора первого элемента
                availability = await avail_el.text_content() if avail_el else "Нет информации"

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