from playwright.async_api import async_playwright
import asyncio
import json

def build_urls(product_name):
    return {
        "radiocomplect": f"https://radiocomplect.ru/search/?searchstring={product_name}"
    }

async def parse_RADIOCOMPLECT(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link, timeout=30000)

        try:
            # Ждем, пока загрузится таблица с продуктами
            await page.wait_for_selector("table.prds__item_tab", timeout=5000)  # Увеличили тайм-аут до 5 секунд
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


async def main():
    product = input("Введите название товара: ")
    urls = build_urls(product)

    results = await asyncio.gather(    
        parse_RADIOCOMPLECT(urls['radiocomplect']),       
    )

    site_names = ["radiocomplect"]
    for name, res in zip(site_names, results):
        print(f"\nРезультаты для {name}:")
        if res:
            for r in res:
                print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            print("Результатов не найдено")


if __name__ == "__main__":
    asyncio.run(main())