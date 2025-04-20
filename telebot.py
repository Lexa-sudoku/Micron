import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.enums import ParseMode
from parsers.compile import parsing
from config import TOKEN
API_TOKEN = TOKEN

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN,
          default=DefaultBotProperties(
              parse_mode=ParseMode.HTML,
              link_preview_is_disabled=True))
dp = Dispatcher()


def generate_market_info(site, result):
    message_list = [f"🛍 <b>Результаты для {site}:</b>"]
    if not result:
        message_list.append("⚠️ <i>Результатов не найдено</i>")
        message_list.append('')
        return message_list
    for product in result:
        name = product.get("name", "-")
        url = product.get("url", "-")
        name_with_link = f'<a href="{url}">{name}</a>'
        message_list.append(f'🔹 {name_with_link}')

        availability = product.get("availability", "-")
        message_list.append(f'📦 Наличие: {availability}')

        prices = product["price_info"]
        message_list.append('💰 Цены:')
        for price in prices:
            message_list.append(f'\tот {price["quantity"]} шт — {price["price"]} руб/шт')
        message_list.append('')
    return message_list


def split_message(text):
    parts = []
    while len(text) > 4096:
        break_point = text.rfind("<", 0, 4096)
        if break_point == -1:
            break_point = 4096
        open_tag = text.find(">", break_point)
        if open_tag == -1:
            open_tag = len(text)
        part = text[:open_tag + 1]
        parts.append(part)
        text = text[open_tag + 1:].lstrip()
    if text:
        parts.append(text)
    return parts


def generate_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text='Новый запрос', callback_data='new')
    return builder.as_markup()


@dp.message(Command('start'))
async def send_welcome(message):
    chat_id = message.chat.id
    username = message.from_user.first_name
    message_text = f'<b>Привет, {username}!</b> 👋\nОтправь мне название товара, и я найду информацию 📝'
    await bot.send_message(chat_id=chat_id, text=message_text)


@dp.callback_query()
async def callback(call):
    chat_id = call.message.chat.id
    message_text = 'Отправь мне название товара, и я найду информацию 📝'
    await bot.send_message(chat_id=chat_id, text=message_text)


@dp.message()
async def get_info(message):
    # Отправляем сообщение о поиске информации
    chat_id = message.chat.id
    message_text = '<i>Ищу информацию...</i> 💤'
    msg = await bot.send_message(chat_id=chat_id, text=message_text)

    # Получаем результаты парсинга
    product_name = message.text
    parsing_results = await parsing(product_name)

    # Обрабатываем результаты парсинга
    message_list = []
    for site_name, result in parsing_results.items():
        market_info = generate_market_info(site_name, result)
        message_list.extend(market_info)

    # Формируем сообщение ответа
    message_str = '\n'.join(message_list)
    parts = split_message(message_str)
    await bot.delete_message(chat_id, msg.message_id)
    for part in parts[:-1]:
        message_text = part
        await bot.send_message(chat_id=chat_id, text=message_text)
    reply_markup = generate_keyboard()
    message_text = parts[-1]
    await bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(dp.start_polling(bot))
