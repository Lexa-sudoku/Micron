from builders import build_urls, fetch_page_data
from chipdip_parser import parse_chipdip
from platan_parser import parse_platan
from dip8_parser import parse_dip8
from mirekom_parser import parse_mirekom
from radiocomplect_parser import parse_radiocomplect
from playwright.async_api import async_playwright
import asyncio
import json


async def main():
    product = input("Введите название товара: ")
    urls = build_urls(product)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        tasks = [
            fetch_page_data(browser, urls["platan"], parse_platan),
            fetch_page_data(browser, urls["dip8"], parse_dip8),
            fetch_page_data(browser, urls["mirekom"], parse_mirekom),
            fetch_page_data(browser, urls["radiocomplect"], parse_radiocomplect),
            fetch_page_data(browser, urls["chipdip"], parse_chipdip)
        ]

        results = await asyncio.gather(*tasks)
        site_names = ["Platan", "DIP8", "MIREKOM", "RADIOCOMPLECT", "ChipDip"]
        to_file = {}
        for name, res in zip(site_names, results):
            print(f"\nРезультаты для {name}:")
            print(json.dumps(res, indent=2, ensure_ascii=False))
            to_file[name] = res
        with open('1.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(to_file, ensure_ascii=False))

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
