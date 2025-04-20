async def parse_mirekom(page):
    result = []
    try:
        products = await page.locator("div.itemslist div.itemslist .line").all()
        for prod in products[1:]:
            try:
                if 'Номер' in await prod.inner_text():
                    break
                text = await prod.inner_text()
                lines = text.strip().split("\n")

                # Наименование товара
                name = lines[0] if len(lines[0]) > 10 else ' '.join(lines[:2])
                name = ' '.join(name.split('\\')[1:]).strip()

                # Ссылка на товар
                href = await prod.locator('.ima a').get_attribute("href")
                url = f"https://mirekom.ru{href}"

                # Наличие товара
                availability = lines[-1] if 'Нет в наличии' in lines[-1] else "В наличии " + lines[-4]
                availability = availability.strip()

                # Цены на товар
                price = '-' if 'Нет в наличии' in lines[-1] else lines[-3].strip(" р.").split()[-1]
                price = price.strip()
                if price != '-':
                    price += '.00'
                prices = [{
                    "price": price,
                    "quantity": "1"
                }]

                # Добавляем в результаты
                result.append({
                    "name": name,
                    "url": url,
                    "availability": availability,
                    "price_info": prices
                })
            except Exception as e:
                print(f"MIREKOM parse error: {e}")
    except Exception as e:
        print(f"MIREKOM parse error (outer): {e}")
    return result
