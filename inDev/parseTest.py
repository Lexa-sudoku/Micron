from playwright.async_api import async_playwright
import asyncio
import json

def build_urls(product_name):
    return {
        "mirekom": f"https://mirekom.ru/price/find.php?text={product_name}",
    }

async def parse_MIREKOM(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(link, timeout=10000)
            await page.wait_for_selector(".search-container", timeout=5000)
        except Exception as e:
            print(f"Ошибка загрузки страницы: {e}")
            await browser.close()
            return []

        parsed = []

        try:
            container = page.locator(".search-container").first
            await container.wait_for(timeout=3000)

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
        return parsed

async def main():
    product = input("Введите название товара: ")
    urls = build_urls(product)

    results = await asyncio.gather(    
        parse_MIREKOM(urls['mirekom']),       
    )

    site_names = ["MIREKOM"]
    for name, res in zip(site_names, results):
        print(f"\nРезультаты для {name}:")
        if res:
            for r in res:
                print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            print("Результатов не найдено")


if __name__ == "__main__":
    asyncio.run(main())