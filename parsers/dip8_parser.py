async def parse_dip8(page):
    products = []
    try:
        cards = await page.locator("div.list_item_wrapp.item_wrap").all()
        for card in cards:
            try:
                name = await card.locator("a.dark_link").text_content()
                href = await card.locator("a.dark_link").get_attribute("href")
                url = f"https://dip8.ru{href}" if href else ""
                prices = [
                    {"price": await block.locator(".price_value").text_content(),
                     "quantity": str(await block.locator(".price_interval").text_content()).replace('\n', '').replace('\t', '')}
                    for block in await card.locator(".price_wrapper_block").all()
                ]
                availability = await card.locator(".yellow").first.text_content()  # Уточнение селектора
                products.append({
                    "name": name.strip(),
                    "url": url,
                    "availability": availability.strip(),
                    "prices": prices
                })
            except Exception as e:
                print(f"DIP8 parse error: {e}")
                return products
    except Exception as e:
        print(f"DIP8 parse error (outer): {e}")
        return products
    return products