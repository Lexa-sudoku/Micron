import html
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from inDev import parsePlaywright


# Импорт парсеров напрямую из модуля parser



async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправьте мне название товара, и я найду информацию.')


async def handle_message(update: Update, context: CallbackContext) -> None:
    try:
        searching_message = await update.message.reply_text('Ищу данные...')

        product_name = update.message.text.strip()

        links = {
            "Platan": f"https://www.platan.ru/cgi-bin/qwery_i.pl?code={product_name}",
            "DIP8": f"https://dip8.ru/shop/?q={product_name}",
            "MIRECOM": f"https://mirekom.ru/price/find.php?text={product_name}",
            "RADIOCOMPLECT": f"https://radiocomplect.ru/search/?searchstring={product_name}",
            "ChipDip": f"https://www.chipdip.ru/search?searchtext={product_name}"
        }

        parsers = {
            "Platan": parsePlaywright.parse_platan,
            "DIP8": parsePlaywright.parse_dip8,
            "MIRECOM": parsePlaywright.parse_MIREKOM,
            "RADIOCOMPLECT": parsePlaywright.parse_RADIOCOMPLECT,
            "ChipDip": parsePlaywright.parse_ChipDip
        }

        # Параллельный запуск всех парсеров
        tasks = [parsers[key](links[key]) for key in parsers]
        results_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        output_results = {}
        for key, elem in zip(parsers.keys(), results_tasks):
            output_results[key] = elem if isinstance(elem, list) else []

        # Сборка сообщений
        results = []
        for site_name, products in output_results.items():
            results.append(f"<b>Результаты для {html.escape(site_name)}:</b>")

            if products:
                for product in products:
                    name = html.escape(product.get("name", "Неизвестный товар"))
                    url = product.get("url", "")
                    availability = html.escape(str(product.get("availability", "-")))
                    price = html.escape(str(product.get("price", "-")))

                    name_with_link = f'<a href="{html.escape(url)}">{name}</a>' if url else name

                    details = [
                        f"🔹 {name_with_link}",
                        f"📦 Наличие: {availability}",
                        f"💰 Цена: {price}"
                    ]
                    results.append("\n".join(details) + "\n")
            else:
                results.append("⚠️ <i>Результатов не найдено</i>")

        # Отправка по частям (на случай большого количества текста)
        max_len = 4096
        message = "\n".join(results)
        for i in range(0, len(message), max_len):
            await update.message.reply_text(
                message[i:i + max_len],
                parse_mode="HTML",
                disable_web_page_preview=True
            )

        await searching_message.delete()
        await update.message.reply_text('Введите название товара:', parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f'Ошибка при обработке: {html.escape(str(e))}', parse_mode="HTML")
        await update.message.reply_text('Введите название товара:', parse_mode="HTML")


def main():
    token = '7729099930:AAFveGDAgd6oBzzVtufJKbk2oMyNgbcnz3Q'
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == '__main__':
    main()
