import asyncio, os
from playwright.async_api import async_playwright

URL = os.environ["MEET_URL"]
NAME = os.environ["MEET_NAME"]
STAY_MINUTES = 1  # для теста; потом поставь 45

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=[
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
        ])
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        try:
            await page.goto(URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(6000)

            # Если вдруг предложат продолжить в браузере: необязательный шаг
            try:
                await page.click("text=Продолжить в браузере", timeout=3000)
                await page.wait_for_timeout(3000)
            except Exception:
                pass

            await page.screenshot(path="1_before_name.png")

            # Меняем имя: кликаем на «Гость» и печатаем своё
            try:
                await page.get_by_text("Гость", exact=True).click(timeout=5000)
                await page.keyboard.press("Control+A")
                await page.keyboard.type(NAME)
                await page.keyboard.press("Enter")
            except Exception:
                await page.locator("input[type='text']").first.fill(NAME, timeout=5000)

            await page.wait_for_timeout(1000)
            await page.screenshot(path="2_after_name.png")

            # Нажимаем «Подключиться» (если Enter уже подключил, пропускаем)
            try:
                await page.get_by_role("button", name="Подключиться").click(timeout=5000)
            except Exception:
                pass

            await page.wait_for_timeout(8000)
            await page.screenshot(path="3_after_join.png")

            await asyncio.sleep(STAY_MINUTES * 60)
        except Exception:
            await page.screenshot(path="error.png")
            raise
        finally:
            await browser.close()

asyncio.run(main())
