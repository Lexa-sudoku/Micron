from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import parse4
import asyncio

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправьте мне название товара, и я найду информацию.')

async def handle_message(update: Update, context: CallbackContext) -> None:
    product_name = update.message.text

    try:
        await update.message.reply_text('Ищу данные...')

        links = {
            "Platan": f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}",
            "DIP8": f"https://dip8.ru/shop/?q={product_name}",
            "RADIOCOMPLECT": f"https://radiocomplect.ru/search/?searchstring={product_name}",
            "CHIPSTER": f"https://chipster.ru/search.html?q={product_name}",
            "ChipDip": f"https://www.chipdip.ru/search?searchtext={product_name}"
        }

        parsers = {
            "Platan": parse4.parse_platan,
            "DIP8": parse4.parse_dip8,
            "RADIOCOMPLECT": parse4.parse_RADIOCOMPLECT,
            "CHIPSTER": parse4.parse_CHIPSTER,
            "ChipDip": parse4.parse_ChipDip
        }

        results = []
        tasks = {name: parsers[name](link) for name, link in links.items()}
        parsed_data = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for name, result in zip(tasks.keys(), parsed_data):
            results.append(f"<b>Результаты для {name}:</b>")
            
            if isinstance(result, Exception):
                results.append(f"❌ Ошибка: {result}")
            elif result:
                for product in result:
                    # Формируем гиперссылку, если есть URL
                    if "full_url" in product and product["full_url"]:
                        name_with_link = f'<a href="{product["full_url"]}">{product["name"]}</a>'
                    else:
                        name_with_link = product["name"]
                    
                    details = [
                        f"🔹 {name_with_link}",
                        f"📦 Наличие: {product.get('availability', 'N/A')}"
                    ]
                    if "article" in product:
                        details.append(f"🆔 Артикул: {product['article']}")
                    if "prices" in product:
                        prices = "\n".join([f"💰 Цена: {p['price']}, Количество: {p['quantity']}" for p in product['prices']])
                        details.append(f"💵 Цены:\n{prices}")
                    else:
                        details.append(f"💵 Цена: {product.get('price', 'N/A')}")

                    results.append("\n".join(details) + "\n")
            else:
                results.append("⚠️ Результатов не найдено")

        # Ограничение Telegram (макс. длина сообщения — 4096 символов)
        max_message_length = 4096
        message = "\n".join(results)
        
        for i in range(0, len(message), max_message_length):
            await update.message.reply_text(message[i:i + max_message_length], parse_mode="HTML", disable_web_page_preview=True)

        await update.message.reply_text('Введите название товара:', parse_mode="HTML")
    
    except Exception as e:
        await update.message.reply_text(f'Ошибка при обработке: {e}', parse_mode="HTML")
        await update.message.reply_text('Введите название товара:', parse_mode="HTML")

def main():
    token = '7729099930:AAFveGDAgd6oBzzVtufJKbk2oMyNgbcnz3Q'
    # token = '7160408679:AAHHo2JYCv4JsDt8FIs29mGv0x9PxoqExrQ'
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == '__main__':
    main()
