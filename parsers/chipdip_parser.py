async def parse_chipdip(page):
    result = []
    try:
        await page.reload()
        rows = await page.locator("tbody tr.with-hover").all()
        for row in rows:
            try:
                # Наименование товара
                name_el = row.locator("a.link")
                name = await name_el.text_content()
                name = name.strip()

                # Ссылка на товар
                href = await name_el.get_attribute("href")
                url = f"https://www.chipdip.ru{href}" if href else ""

                # Наличие товара
                availability = await row.locator("td.h_av span.item__avail").text_content()
                availability = availability.strip()
                availability_list = availability.split(',')
                if len(availability_list) == 2:
                    availability = f'{availability_list[1]} {availability_list[0]}'
                else:
                    availability = availability_list[0]

                # Цены на товар
                prices = []
                product_id = await row.get_attribute("id")
                if product_id:
                    product_id = product_id.replace("item", "")
                else:
                    product_id = ""
                price = await row.locator(f"#price_{product_id}").text_content()
                price = price.strip().replace(" ", "")
                if price[-3] != '.':
                    price += '.00'
                prices.append({
                    "price": price,
                    "quantity": '1'
                })
                wholesale = [await block.inner_text() for block in await row.locator("div.addprice-w div.addprice").all()]
                for info in wholesale:
                    lst = info.split(' шт. — ')
                    quantity = lst[0].strip('от ')
                    price = lst[1].strip(' руб.').replace('\xa0', '')
                    if price[-3] != '.':
                        price += '.00'
                    prices.append({
                        "price": price,
                        "quantity": quantity
                    })

                # Добавляем в результат
                result.append({
                    "name": name,
                    "url": url,
                    "availability": availability,
                    "price_info": prices
                })
            except Exception as e:
                print(f"ChipDip parse error: {e}")
    except Exception as e:
        print(f"ChipDip parse error (outer): {e}")
    return result