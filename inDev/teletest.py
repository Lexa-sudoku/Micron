'''

import html
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправьте мне название товара, и я найду информацию.')


async def parse_platan(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link)

        try:
            results_text = await page.locator("h1.text-success sub").text_content()
            if results_text == '0':
                await browser.close()
                return {"Platan": []}
        except:
            pass

        rows = await page.locator("tr.border-bottom").all()
        products = []

        for row in rows:
            try:
                name_el = row.locator("td.w-35 a.link")
                name = (await name_el.text_content()).strip()
                href = await name_el.get_attribute("href")
                url = f"https://www.platan.ru{href}" if href else ""

                price_rows = await row.locator("td table tbody tr").all()
                prices = []
                for pr in price_rows:
                    price = await pr.locator("td:nth-child(1)").text_content()
                    qty = await pr.locator("td:nth-child(2)").text_content()
                    prices.append({"price": price.strip(), "quantity": qty.strip()})

                try:
                    availability = await row.locator("td:has-text('шт.'), td:has-text('под заказ'), td:has-text('раб.дня')").text_content()
                except:
                    availability = "Не указано"

                products.append({"name": name, "url": url, "availability": availability, "prices": prices})
            except:
                continue

        await browser.close()
        return {"Platan": products}

async def parse_dip8(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link)

        cards = await page.locator("div.list_item_wrapp.item_wrap").all()
        products = []

        for card in cards:
            try:
                name_el = card.locator("a.dark_link")
                name = await name_el.text_content()
                href = await name_el.get_attribute("href")
                url = f"https://dip8.ru{href}" if href else link

                try:
                    availability = await card.locator(".yellow").text_content()
                except:
                    availability = "Не указано"

                prices = []
                price_blocks = await card.locator(".price_wrapper_block").all()
                for block in price_blocks:
                    try:
                        price = await block.locator(".price_value").text_content()
                        qty = await block.locator(".price_interval").text_content()
                        prices.append({"price": price.strip(), "quantity": qty.strip()})
                    except:
                        continue

                products.append({"name": name.strip(), "url": url, "availability": availability, "prices": prices})
            except:
                continue

        await browser.close()
        return {"DIP8": products}

async def parse_MIREKOM(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(link, timeout=3000)
            await page.wait_for_selector(".search-container", timeout=2000)
        except:
            await browser.close()
            return {"MIRECOM": []}

        parsed = []
        try:
            lines = await page.locator(".search-container .line").all()

            for line in lines:
                try:
                    class_name = await line.get_attribute("class")
                    if "hdr" in class_name:
                        continue

                    name_el = line.locator(".std a")
                    name = await name_el.text_content()
                    url_part = await name_el.get_attribute("href")
                    url = f"https://mirekom.ru{url_part}"

                    try:
                        quantity = await line.locator(".qua").text_content()
                    except:
                        quantity = "Нет в наличии"

                    try:
                        price = await line.locator(".pri").text_content()
                        price = price.replace(" р.", "").strip()
                    except:
                        price = "N/A"

                    parsed.append({
                        "name": name.strip(),
                        "availability": quantity.strip(),
                        "price": price,
                        "url": url
                    })
                except:
                    continue
        except:
            pass

        await browser.close()
        return {"MIRECOM": parsed}

async def parse_RADIOCOMPLECT(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link, timeout=3000)

        try:
            await page.wait_for_selector("table.prds__item_tab", timeout=2000)
        except:
            await browser.close()
            return {"RADIOCOMPLECT": []}

        tables = await page.locator("table.prds__item_tab").all()
        parsed = []

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
            except:
                continue

        await browser.close()
        return {"RADIOCOMPLECT": parsed}

async def parse_ChipDip(link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link, timeout=3000)

        try:
            await page.wait_for_selector("#itemlist tbody tr.with-hover", timeout=2000)
            rows = await page.locator("#itemlist tbody tr.with-hover").all()
        except:
            await browser.close()
            return {"ChipDip": []}

        parsed = []

        for row in rows:
            try:
                title_el = row.locator("a.link[href]")
                title = await title_el.text_content()
                href = await title_el.get_attribute("href")
                url = f"https://www.chipdip.ru{href}" if href else ""

                price_el = row.locator("span.price-main")
                price = await price_el.text_content() if price_el else "Цена не указана"

                avail_el = row.locator("span.item__avail").first
                availability = await avail_el.text_content() if avail_el else "Нет информации"

                wholesale = []
                addprice_blocks = await row.locator("div.addprice-w div.addprice").all()
                for block in addprice_blocks:
                    price_text = await block.text_content()
                    parts = price_text.strip().split("—")
                    if len(parts) == 2:
                        wholesale.append({"quantity": parts[0].strip(), "price": parts[1].strip()})
                    else:
                        wholesale.append({"price": price_text.strip()})

                parsed.append({
                    "name": title.strip(),
                    "url": url,
                    "price": price.strip(),
                    "availability": availability.strip(),
                    "wholesale_prices": wholesale
                })
            except:
                continue

        await browser.close()
        return {"ChipDip": parsed}
    

async def handle_message(update: Update, context: CallbackContext) -> None:
    try:
        searching_message = await update.message.reply_text('🔍 Ищу данные...')

        product_name = update.message.text.strip()

        links = {
            "Platan": f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}",
            "DIP8": f"https://dip8.ru/shop/?q={product_name}",
            "MIRECOM": f"https://mirekom.ru/price/find.php?text={product_name}",
            "RADIOCOMPLECT": f"https://radiocomplect.ru/search/?searchstring={product_name}",
            "ChipDip": f"https://www.chipdip.ru/search?searchtext={product_name}"
        }

        parsers = {
            "Platan": parse_platan,
            "DIP8": parse_dip8,
            "MIRECOM": parse_MIREKOM,
            "RADIOCOMPLECT": parse_RADIOCOMPLECT,
            "ChipDip": parse_ChipDip
        }

        # Создаем задачи
        tasks = [parsers[site](links[site]) for site in parsers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        message_parts = []

        for site, result in zip(parsers.keys(), results):
            message_parts.append(f"<b>📡 Результаты для {html.escape(site)}:</b>")

            if isinstance(result, dict) and isinstance(result.get(site), list):
                products = result[site]
                if products:
                    for product in products:
                        name = html.escape(product.get("name", "Без названия"))
                        url = product.get("url", "")
                        name_link = f'<a href="{html.escape(url)}">{name}</a>' if url else name

                        availability = html.escape(product.get("availability", "—"))
                        price = product.get("price")
                        prices = product.get("prices") or product.get("wholesale_prices")

                        if isinstance(prices, list):
                            price_lines = "\n".join(
                                [f"   • {html.escape(p.get('quantity', ''))}: {html.escape(p.get('price', ''))}" for p in prices]
                            )
                            price_text = f"💰 Оптовые цены:\n{price_lines}"
                        elif isinstance(price, str):
                            price_text = f"💰 Цена: {html.escape(price)}"
                        else:
                            price_text = "💰 Цена: —"

                        message_parts.append(f"🔹 {name_link}\n📦 Наличие: {availability}\n{price_text}\n")
                else:
                    message_parts.append("⚠️ <i>Результатов не найдено</i>")
            else:
                message_parts.append(f"⚠️ <i>Ошибка при парсинге {site}</i>")

        # Отправка сообщения порциями
        full_message = "\n".join(message_parts)
        max_length = 4096
        for i in range(0, len(full_message), max_length):
            await update.message.reply_text(
                full_message[i:i + max_length],
                parse_mode="HTML",
                disable_web_page_preview=True
            )

        await searching_message.delete()
        await update.message.reply_text('Введите название следующего товара:', parse_mode="HTML")

    except Exception as e:
        logging.exception("Ошибка в боте")
        await update.message.reply_text(f'🚫 Ошибка: {html.escape(str(e))}', parse_mode="HTML")
        await update.message.reply_text('Введите название товара:', parse_mode="HTML")

def main():
    token = '7729099930:AAFveGDAgd6oBzzVtufJKbk2oMyNgbcnz3Q'
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()

'''