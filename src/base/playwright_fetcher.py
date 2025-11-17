from playwright.sync_api import sync_playwright

def fetch_with_playwright(url: str) -> str:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(url)
        html = page.content()
        browser.close()
        return html
