import html
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import parse4
import asyncio

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправьте мне название товара, и я найду информацию.')


async def save_json(arr, filename):
    with open(f"{filename}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(arr, ensure_ascii=False))
        f.close()

async def handle_message(update: Update, context: CallbackContext) -> None:
    try:
        await update.message.reply_text('Ищу данные...')

        product_name = update.message.text

        links = {
            "Platan": f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}",
            "DIP8": f"https://dip8.ru/shop/?q={product_name}",
            "MIRECOM": f"https://mirekom.ru/price/find.php?text={product_name}",
            "RADIOCOMPLECT": f"https://radiocomplect.ru/search/?searchstring={product_name}",
            "CHIPSTER": f"https://chipster.ru/search.html?q={product_name}",
            "ChipDip": f"https://www.chipdip.ru/search?searchtext={product_name}"
        }

        parsers = {
            "Platan": parse4.parse_platan,
            "DIP8": parse4.parse_dip8,
            "MIRECOM": parse4.parse_mirecom,
            "RADIOCOMPLECT": parse4.parse_radiocomplect,
            # "CHIPSTER": parse4.parse_chipster,
            "ChipDip": parse4.parse_chipdip
        }
        tasks = [parsers[key](links[key]) for key in parsers]
        results_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        # Обработка результатов
        output_results = {}
        for elem in results_tasks:
            if isinstance(elem, dict):
                parse_site = list(elem.keys())[0]
                parse_result = list(elem.values())[0]
                output_results[parse_site] = parse_result
            else:
                output_results[str(elem)] = []

        # Формирование сообщения
        results = []
        for name, result in output_results.items():
            results.append(f"<b>Результаты для {html.escape(name)}:</b>")
            if result and isinstance(result, list):
                for product in result:
                    product_name = html.escape(product.get("name", "Неизвестный товар"))
                    availability = html.escape(str(product.get("availability", "-")))
                    price = html.escape(str(product.get("price", "-")))
                    product_url = html.escape(product.get("url", ""))

                    # Формируем гиперссылку, если есть URL
                    if "url" in product and product["url"]:
                        name_with_link = f'<a href="{product_url}">{product_name}</a>'
                    else:
                        name_with_link = product["name"]

                    # Формируем сообщение
                    details = [
                        f"🔹 {name_with_link.replace("-", "&#45;")}",
                        f"📦 Наличие: {availability.replace("-", "&#45;")}\n"
                        f"💰 Цена:{price.replace("-", "&#45;")}"
                    ]
                    results.append("\n".join(details) + "\n")
            else:
                results.append("⚠️ <i>Результатов не найдено</i>")

        # Ограничение Telegram (макс. длина сообщения — 4096 символов)
        max_message_length = 4096
        message = "\n".join(results)

        for i in range(0, len(message), max_message_length):
            await update.message.reply_text(message[i:i + max_message_length], parse_mode="HTML",
                                            disable_web_page_preview=True)

        await update.message.reply_text('Введите название товара:', parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f'Ошибка при обработке: {e}', parse_mode="HTML")
        await update.message.reply_text('Введите название товара:', parse_mode="HTML")


def main():
    token = '7729099930:AAFveGDAgd6oBzzVtufJKbk2oMyNgbcnz3Q'
    # my
    # token = '7160408679:AAHHo2JYCv4JsDt8FIs29mGv0x9PxoqExrQ'
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == '__main__':
    main()
