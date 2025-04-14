async def parse_chipdip(page):
    parsed = []
    try:
        await page.reload()
        rows = await page.locator("tbody tr.with-hover").all()
        for row in rows:
            try:
                title_el = row.locator("a.link")
                title = await title_el.text_content()
                href = await title_el.get_attribute("href")
                url = f"https://www.chipdip.ru{href}" if href else ""
                product_id = await row.get_attribute("id")
                if product_id:
                    product_id = product_id.replace("item", "")
                else:
                    product_id = ""
                price = await row.locator(f"#price_{product_id}").text_content()
                availability = await row.locator("td.h_av span.item__avail").text_content()
                wholesale = [await block.inner_text() for block in await row.locator("div.addprice-w div.addprice").all()]
                parsed.append({
                    "name": title.strip(),
                    "url": url,
                    "price": price.strip(),
                    "availability": availability.strip(),
                    "wholesale_prices": wholesale
                })
            except Exception as e:
                print(f"ChipDip parse error: {e}")
    except Exception as e:
        print(f"ChipDip parse error (outer): {e}")
    return parsed