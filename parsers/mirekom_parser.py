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