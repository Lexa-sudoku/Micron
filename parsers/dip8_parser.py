async def parse_dip8(page):
    products = []
    try:
        cards = await page.locator("div.list_item.item_info").all()
        for card in cards:
            try:
                # Название и ссылка
                name_el = card.locator("a.dark_link").first
                name = await name_el.text_content() if name_el else "N/A"
                href = await name_el.get_attribute("href") if name_el else ""
                url = f"https://dip8.ru{href}" if href else ""

                # Цены и количества
                price_blocks = await card.locator(".price_wrapper_block").all()
                prices = []
                for block in price_blocks:
                    price_val = await block.locator(".price_value").text_content()
                    qty_text = await block.locator(".price_interval").text_content()
                    prices.append({
                        "price": price_val.strip(),
                        "quantity": qty_text.strip().replace('\n', ' ').replace('\t', '')
                    })

                # Наличие
                availability_el = card.locator(".wrapp_stockers .yellow").first
                availability = await availability_el.text_content() if availability_el else "—"

                # Добавляем в результат
                products.append({
                    "name": name.strip(),
                    "url": url,
                    "availability": availability.strip(),
                    "prices": prices
                })

            except Exception as e:
                print(f"DIP8 parse error (item): {e}")
                continue

    except Exception as e:
        print(f"DIP8 parse error (outer): {e}")

    return products
