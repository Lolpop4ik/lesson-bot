import asyncio, os
from playwright.async_api import async_playwright

URL = os.environ["MEET_URL"]
NAME = os.environ["MEET_NAME"]
STAY_MINUTES = 1  # для теста; потом поставь 45
log = []

def save():
    with open("dump.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log))

async def dump(page, tag):
    for i, fr in enumerate(page.frames):
        try:
            info = await fr.evaluate("""() => {
                const q = s => [...document.querySelectorAll(s)];
                return {
                    url: location.href.slice(0, 80),
                    buttons: q('button,[role=button]').map(e =>
                        (e.getAttribute('aria-label') || '') + ' | ' + (e.innerText || '').trim().slice(0, 40)),
                    inputs: q('input,textarea,[contenteditable]').map(e =>
                        e.tagName + ' | ' + (e.placeholder || '') + ' | ' + (e.getAttribute('aria-label') || '')),
                };
            }""")
            log.append(f"== {tag} / frame {i}\n{info}\n")
        except Exception as e:
            log.append(f"== {tag} / frame {i} error: {e}\n")
    save()

async def find_join_frame(page):
    for _ in range(20):
        for fr in page.frames:
            try:
                if await fr.get_by_text("Подключиться").count() > 0:
                    return fr
            except Exception:
                pass
        await page.wait_for_timeout(1000)
    return None

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
            await page.wait_for_timeout(5000)
            fr = await find_join_frame(page)
            log.append(f"join frame found: {fr is not None}")
            await dump(page, "start")
            if fr is None:
                raise Exception("join frame not found")

            # выключаем микрофон и камеру
            for label in ("Выключить микрофон", "Выключить камеру"):
                for target in (fr, page):
                    try:
                        await target.get_by_role("button", name=label).first.click(timeout=2000)
                        log.append(f"clicked: {label}")
                        break
                    except Exception:
                        pass
            await page.wait_for_timeout(1000)
            await page.screenshot(path="2_after_mute.png")
            await dump(page, "after mute")

            # имя
            try:
                await fr.get_by_text("Гость", exact=True).first.click(timeout=5000)
                await page.wait_for_timeout(1000)
            except Exception as e:
                log.append(f"click on name failed: {e}")
            await page.screenshot(path="3_after_click_name.png")
            await dump(page, "after click on name")

            fields = fr.locator("input, [contenteditable='true']")
            if await fields.count() > 0:
                try:
                    await fields.first.fill(NAME)
                    await page.keyboard.press("Enter")
                except Exception as e:
                    log.append(f"fill name failed: {e}")
            await page.wait_for_timeout(1000)
            await page.screenshot(path="4_after_name.png")

            # вход
            try:
                await fr.get_by_role("button", name="Подключиться").first.click(timeout=5000)
            except Exception:
                try:
                    await fr.get_by_text("Подключиться").first.click(timeout=5000)
                except Exception as e:
                    log.append(f"join click failed: {e}")
            await page.wait_for_timeout(8000)
            await page.screenshot(path="5_after_join.png")
            await dump(page, "after join")

            await asyncio.sleep(STAY_MINUTES * 60)
        except Exception as e:
            log.append(f"FATAL: {e}")
            save()
            await page.screenshot(path="error.png")
            raise
        finally:
            await browser.close()

asyncio.run(main())
