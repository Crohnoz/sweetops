from playwright.sync_api import sync_playwright
import json

URL = "https://isiscakes.ola.click/products"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    captured = []

    def handle_response(response):
        url = response.url

        if (
            "api.olaclick" in url
            or "product" in url.lower()
            or "categor" in url.lower()
        ):
            try:
                captured.append({
                    "url": url,
                    "status": response.status,
                    "content_type": response.headers.get("content-type", "")
                })
            except:
                pass

    page.on("response", handle_response)

    page.goto(URL, wait_until="networkidle", timeout=60000)

    page.wait_for_timeout(5000)

    print(json.dumps(captured, indent=2, ensure_ascii=False))

    browser.close()
