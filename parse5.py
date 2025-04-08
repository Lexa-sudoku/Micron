from playwright.sync_api import sync_playwright
import random
import json

def configure_browser(proxy: str = None) -> None:
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    user_agent = random.choice(user_agents)

    with sync_playwright() as p:
        browser_args = []

        if proxy:
            browser_args.append(f'--proxy-server={proxy}')
        
        browser = p.chromium.launch(headless=True, args=browser_args)
        context = browser.new_context(user_agent=user_agent)
        page = context.new_page()
        
        return page, browser  # Вернем page и browser для дальнейшей работы

def fetch_page(page, url: str) -> str:
    page.goto(url)
    return page.content()  # Получаем HTML-страницу



async def save_json(arr, filename):
    with open(f"{filename}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(arr, ensure_ascii=False, indent=4))
