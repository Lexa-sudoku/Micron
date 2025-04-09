from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import parsePlaywright
import asyncio

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Отправьте мне название товара, и я найду информацию.')

async def handle_message(update: Update, context: CallbackContext) -> None:
    product_name = update.message.text

    try:
        await update.message.reply_text('Ищу данные...')

        links = {
            "Platan": f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}",
            "DIP8": f"https://dip8.ru/shop/?q={product_name}",
            #"MIREKOM": f"https://mirekom.ru/price/find.php?text={product_name}",
            "RADIOCOMPLECT": f"https://radiocomplect.ru/search/?searchstring={product_name}",
            #"CHIPSTER": f"https://chipster.ru/search.html?q={product_name}",
            "ChipDip": f"https://www.chipdip.ru/search?searchtext={product_name}"
        }

        parsers = {
            "Platan": parsePlaywright.parse_platan,
            "DIP8": parsePlaywright.parse_dip8,
            #"MIREKOM": parsePlaywright.parse_MIREKOM,
            "RADIOCOMPLECT": parsePlaywright.parse_RADIOCOMPLECT,
            #"CHIPSTER": parseSelenium.parse_CHIPSTER,
            "ChipDip": parsePlaywright.parse_ChipDip
        }

        results = []
        tasks = {name: parsers[name](link) for name, link in links.items()}
        parsed_data = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for name, result in zip(tasks.keys(), parsed_data):
            results.append(f"Результаты для {name}:")
            if isinstance(result, Exception):
                results.append(f"Ошибка: {result}")
            elif result:
                for product in result:
                    details = [
                        f"Название: {product.get('name', 'N/A')}",
                        f"Наличие: {product.get('availability', 'N/A')}"
                    ]
                    if "article" in product:
                        details.append(f"Артикул: {product['article']}")
                    if "prices" in product:
                        prices = "\n".join([f"Цена: {price_info['price']}, Количество: {price_info['quantity']}" for price_info in product['prices']])
                        details.append(f"Цены:\n{prices}")
                    else:
                        details.append(f"Цена: {product.get('price', 'N/A')}")
                    results.append("\n".join(details) + "\n")
            else:
                results.append("Результатов не найдено")


        # Split results into multiple messages if too long
        max_message_length = 4096
        message = "\n".join(results)
        for i in range(0, len(message), max_message_length):
            await update.message.reply_text(message[i:i + max_message_length])

        await update.message.reply_text("\n".join(results))
        await update.message.reply_text('Введите название товара:')
    except Exception as e:
        await update.message.reply_text(f'Ошибка при обработке: {e}')
        await update.message.reply_text('Введите название товара:')

def main():
    TOKEN = '7729099930:AAFveGDAgd6oBzzVtufJKbk2oMyNgbcnz3Q'
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == '__main__':
    main()