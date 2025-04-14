async def parse_radiocomplect(page):
    parsed = []
    try:
        await page.wait_for_selector("table.prds__item_tab", timeout=10000)
        tables = await page.locator("table.prds__item_tab").all()
        for table in tables:
            try:
                name = await table.locator("a.prds__item_name span.prds__item_name_in").first.text_content()
                href = await table.locator("a.prds__item_name").first.get_attribute("href")
                url = f"https://radiocomplect.ru{href}"
                price = await table.locator(".prd_form__price_val").first.text_content()
                availability = await table.locator(".prd_form__q_ex").first.text_content()
                parsed.append({
                    "name": name.strip(),
                    "url": url,
                    "price": price.strip(),
                    "availability": availability.strip()
                })
            except Exception as e:
                print(f"Radiocomplect parse error: {e}")
    except Exception as e:
        print(f"Radiocomplect parse error (outer): {e}")
    return parsed