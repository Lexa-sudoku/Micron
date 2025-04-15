async def parse_platan(page):
    results = []
    print(page.url)
    try:
        if await page.locator("h1.text-success sub").text_content() == '0':
            return results

        rows = await page.locator("tr.border-bottom").all()
        for row in rows:
            try:
                # Извлечение названия и ссылки
                name_el = row.locator("td.w-35 a.link")
                name = await name_el.text_content()
                href = await name_el.get_attribute("href")
                url = f"https://www.platan.ru{href}" if href else ""

                # Извлечение цен и количеств
                prices = []
                price_rows = await row.locator("td table tbody tr").all()
                for pr in price_rows:
                    price = await pr.locator("td:nth-child(1)").text_content()
                    quantity = await pr.locator("td:nth-child(2)").text_content()
                    prices.append({"price": price.strip(), "quantity": quantity.strip()})

                # Извлечение доступности
                availability = await row.locator(
                    "td:has-text('шт.'), td:has-text('под заказ'), td:has-text('раб.дня')"
                ).text_content()

                # Добавление результата в список
                results.append({
                    "name": name.strip(),
                    "url": url,
                    "prices": prices,
                    "availability": availability.strip()
                })
            except Exception as e:
                print(f"Platan parse error: {e}")
    except Exception as e:
        print(f"Platan parse error (outer): {e}")
    return results
