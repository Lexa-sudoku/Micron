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
        await page.goto(link, timeout=5000)
        return await parser(page)
    except Exception as e:
        print(f"Ошибка при обработке {link}: {e}")
        return []
    finally:
        await page.close()
