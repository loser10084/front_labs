"""Local browser smoke test for the static Venus exhibit."""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


BASE_URL = "http://127.0.0.1:5174/"
OUTPUT = Path(__file__).resolve().parents[1] / ".qa"


async def check_viewport(browser, name: str, width: int, height: int) -> None:
    page = await browser.new_page(viewport={"width": width, "height": height})
    console_errors: list[str] = []
    page.on("pageerror", lambda error: console_errors.append(str(error)))
    response = await page.goto(BASE_URL, wait_until="networkidle")
    assert response and response.status == 200
    await page.locator("#hero-video").wait_for(state="visible")
    await page.wait_for_function("document.querySelector('#hero-video').readyState >= 2")

    duration = await page.locator("#hero-video").evaluate("video => video.duration")
    assert 9.9 <= duration <= 10.1, f"video duration: {duration}"
    assert await page.locator("#hero-video").evaluate("video => video.videoWidth") == 1920
    await page.wait_for_timeout(900)
    first_time = await page.locator("#hero-video").evaluate("video => video.currentTime")
    assert first_time > 0, f"video did not advance: {first_time}"

    await page.locator("#play-toggle").click()
    assert await page.locator("#hero-video").evaluate("video => video.paused")
    assert await page.locator("#play-toggle").get_attribute("aria-label") == "播放背景视频"
    await page.locator("#play-toggle").click()
    await page.wait_for_function("!document.querySelector('#hero-video').paused")

    await page.locator("#detail-tab-2").click()
    await page.wait_for_timeout(400)
    assert "venus-seam-final-1080p.png" in await page.locator("#detail-image").get_attribute("src")
    assert await page.locator("#detail-tab-2").get_attribute("aria-selected") == "true"
    await page.locator("#detail-tab-3").click()
    await page.wait_for_timeout(400)
    assert "venus-drapery-final-1080p.png" in await page.locator("#detail-image").get_attribute("src")

    overflow = await page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    assert not overflow, f"horizontal overflow at {width}px"
    assert not console_errors, f"browser errors: {console_errors}"
    OUTPUT.mkdir(exist_ok=True)
    await page.screenshot(path=str(OUTPUT / f"{name}-viewport.png"), full_page=False)
    await page.screenshot(path=str(OUTPUT / f"{name}-full.png"), full_page=True)
    print(f"{name}: video {duration:.3f}s, playback and details work, no overflow or page errors")
    await page.close()


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            await check_viewport(browser, "desktop", 1440, 900)
            await check_viewport(browser, "mobile", 390, 844)
            reduced = await browser.new_page(reduced_motion="reduce")
            await reduced.goto(BASE_URL, wait_until="networkidle")
            assert await reduced.locator("#hero-video").evaluate("video => video.paused")
            print("reduced motion: video starts paused")
            await reduced.close()
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
