async def parse_platan(page):
    results = []
    try:
        if await page.locator("h1.text-success sub").text_content() == '0':
            return results

        rows = await page.locator("tr.border-bottom").all()
        for row in rows:
            try:
                # Наименование товара
                name_el = row.locator("td.w-35 a.link")
                name = await name_el.text_content()
                name = name.strip()

                # Ссылка на товар
                href = await name_el.get_attribute("href")
                url = f"https://www.platan.ru{href}" if href else ""

                # Наличие товара
                availability = await row.locator(
                    "td:has-text('шт.'), td:has-text('под заказ'), td:has-text('раб.дня')"
                ).text_content()
                availability = availability.replace('(', '').replace(')', '').replace('.', '. ').replace('  ', ' ').strip()
                if availability == 'под заказ':
                    availability = 'Под заказ'

                # Извлечение цен и количеств
                prices = []
                price_rows = await row.locator("td table tbody tr").all()
                for pr in price_rows:
                    price = await pr.locator("td:nth-child(1)").text_content()
                    price = price.strip().strip(' /шт')
                    quantity = await pr.locator("td:nth-child(2)").text_content()
                    quantity = quantity.strip().strip('от ').strip(' шт')
                    prices.append({
                        "price": price,
                        "quantity": quantity
                    })
                prices = sorted(prices, key=lambda x: int(x['quantity']))

                # Извлечение доступности

                # Добавление результата в список
                results.append({
                    "name": name,
                    "url": url,
                    "availability": availability,
                    "price_info": prices,
                })
            except Exception as e:
                print(f"Platan parse error: {e}")
    except Exception as e:
        print(f"Platan parse error (outer): {e}")
    return results
