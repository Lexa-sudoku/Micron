import html
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from parsers.compile import parsing


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправьте мне название товара, и я найду информацию.')


async def handle_message(update: Update, context: CallbackContext) -> None:
    try:
        searching_message = await update.message.reply_text('Ищу данные...')

        product_name = update.message.text.strip()
        output_results = await parsing(product_name)

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
    token = 'ur token'
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == '__main__':
    main()
