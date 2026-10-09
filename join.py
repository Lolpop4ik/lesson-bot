import asyncio, os
from playwright.async_api import async_playwright

URL = os.environ["MEET_URL"]
NAME = os.environ["MEET_NAME"]
STAY_MINUTES = 45

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=[
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
        ])
        page = await browser.new_page()
        try:
            await page.goto(URL)
            await page.click("text=Продолжить в браузере", timeout=15000)
            await page.fill("input[type='text']", NAME)
            await page.click("text=Подключиться")
            await page.wait_for_timeout(5000)
            await page.screenshot(path="after_join.png")
            await asyncio.sleep(STAY_MINUTES * 60)
        except Exception:
            await page.screenshot(path="error.png")
            raise
        finally:
            await browser.close()

asyncio.run(main())
