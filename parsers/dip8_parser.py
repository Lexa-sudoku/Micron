async def parse_dip8(page):
    result = []
    try:
        cards = await page.locator("div.list_item.item_info").all()
        for card in cards:
            try:
                # Наименование товара
                name_el = card.locator("a.dark_link").first
                name = await name_el.text_content() if name_el else "N/A"
                name = name.strip()

                # Ссылка на товар
                href = await name_el.get_attribute("href") if name_el else ""
                url = f"https://dip8.ru{href}" if href else ""

                # Наличие товара
                availability_el = card.locator(".wrapp_stockers .yellow").first
                availability = await availability_el.text_content() if availability_el else "—"
                availability = ' '.join(availability.strip().split())

                # Цены на товар
                price_blocks = await card.locator(".price_wrapper_block").all()
                prices = []
                for block in price_blocks:
                    price = await block.locator(".price_value").text_content()
                    price = price.strip()
                    if price[-3] != '.':
                        price += '.00'
                    quantity = await block.locator(".price_interval").text_content()
                    quantity = quantity.strip().replace('\n', ' ').replace('\t', '').strip(' шт').split(' до')[0].strip('от ')
                    prices.append({
                        "price": price,
                        "quantity": quantity
                    })

                # Добавляем в результаты
                result.append({
                    "name": name,
                    "url": url,
                    "availability": availability,
                    "price_info": prices
                })
            except Exception as e:
                print(f"DIP8 parse error (item): {e}")
                continue
    except Exception as e:
        print(f"DIP8 parse error (outer): {e}")
    return result
