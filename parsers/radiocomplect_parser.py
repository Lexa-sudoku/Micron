async def parse_radiocomplect(page):
    result = []
    try:
        await page.wait_for_selector("table.prds__item_tab", timeout=10000)
        tables = await page.locator("table.prds__item_tab").all()
        for table in tables:
            try:
                # Наименование товара
                name = await table.locator("a.prds__item_name span.prds__item_name_in").first.text_content()
                name = name.strip()

                # Ссылка на товар
                href = await table.locator("a.prds__item_name").first.get_attribute("href")
                url = f"https://radiocomplect.ru{href}"

                # Наличие товара
                availability = await table.locator(".prd_form__q_ex").first.text_content()
                availability = availability.strip()

                # Цены на товар
                price = await table.locator(".prd_form__price_val").first.text_content()
                price = price.strip()
                if price[-1].isdigit():
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
                print(f"Radiocomplect parse error: {e}")
    except Exception as e:
        print(f"Radiocomplect parse error (outer): {e}")
    return result