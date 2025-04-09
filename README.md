#  **Micron** 

This project is a Telegram bot that helps users find the best prices for microchips by gathering information from popular online electronics stores. The bot automatically scrapes websites and provides users with the current best prices for the components they are looking for.

## 📜 **Description**

The Telegram bot allows users to search for microchips by name and get real-time prices from various online stores like **ChipDip**, **Mirekom**, **Dip8**, and others. The bot uses scraping technology to collect information from multiple websites and presents users with the lowest prices for the products they search for.

Main features of the bot:
- Search for microchips by name.
- Compare prices from different stores.
- Provide product availability information.
- Scraped from popular websites for microchip shopping.

## ⚙️ **How It Works**

1. The bot receives a request from the user with the name of the microchip.
2. It scrapes several websites to find the most current prices for the product.
3. The bot sends the user information about the product, including:
   - Product name.
   - Price.
   - Availability.
   - Store link.

### Example Usage:

1. **Search for a product**:
   - Send the name of the microchip, for example: `ATmega328-AU`.
   
2. **Receiving a response**:
   - The bot finds the product on multiple platforms and shows you the best offers, like:
     ```
    Результаты для Platan:
    Название: AN7112E, усилитель 0.7Вт 9В 16Ом SIP9
    Наличие:  630 шт.
    Цены:
    Цена: 9.55 /шт, Количество: от 1000 шт
    Цена: 10.93 /шт, Количество: от 700 шт
    Цена: 12.32 /шт, Количество: от 400 шт
    Цена: 13.70 /шт, Количество: от 100 шт
    Цена: 28.00 /шт, Количество: от 20 шт

     ```

## **Conributors**
  Litvintsev Matvei
  Karasev Dmitry
