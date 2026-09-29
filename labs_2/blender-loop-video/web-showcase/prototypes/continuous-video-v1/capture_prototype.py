import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


URL = "http://127.0.0.1:5174/prototypes/continuous-video-v1/?capture=1"
OUTPUT = Path(__file__).parent / "previews"


async def capture(page, scene_id: str, filename: str, target_time: float) -> None:
    await page.locator(scene_id).scroll_into_view_if_needed()
    await page.wait_for_timeout(450)
    await page.locator("#capture-frame").evaluate("image => image.decode()")
    await page.screenshot(path=str(OUTPUT / filename))


async def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = await page.goto(URL, wait_until="networkidle")
        assert response and response.status == 200
        await page.wait_for_function("document.querySelector('#story-video').readyState >= 2")
        duration = await page.locator("#story-video").evaluate("video => video.duration")
        assert 9.9 <= duration <= 10.1

        await capture(page, "#opening", "01-opening.png", 0.0)
        await capture(page, "#form", "02-form.png", 2.5)
        await capture(page, "#seam", "03-repair.png", 5.0)
        await capture(page, "#matter", "04-material.png", 7.5)
        await capture(page, "#return", "05-return.png", 9.94)
        assert not errors, errors
        assert not await page.evaluate("document.documentElement.scrollWidth > innerWidth")

        mobile = await browser.new_page(viewport={"width": 390, "height": 844})
        await mobile.goto(URL, wait_until="networkidle")
        await mobile.wait_for_function("document.querySelector('#story-video').readyState >= 2")
        await capture(mobile, "#opening", "mobile-opening.png", 0.0)
        await capture(mobile, "#matter", "mobile-material.png", 7.5)
        assert not await mobile.evaluate("document.documentElement.scrollWidth > innerWidth")

        edge_browser = await playwright.chromium.launch(channel="msedge", headless=True)
        interactive = await edge_browser.new_page(viewport={"width": 1440, "height": 900})
        await interactive.goto(URL.replace("?capture=1", ""), wait_until="networkidle")
        await interactive.wait_for_function("document.querySelector('#story-video').readyState >= 2")
        await interactive.locator("#matter").scroll_into_view_if_needed()
        await interactive.wait_for_timeout(600)
        material_time = await interactive.locator("#story-video").evaluate("video => video.currentTime")
        material_state = await interactive.evaluate(
            """() => ({
                active: document.querySelector('#matter').classList.contains('is-active'),
                progress: parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--scroll-progress')),
                duration: document.querySelector('#story-video').duration,
                readyState: document.querySelector('#story-video').readyState
            })"""
        )
        assert material_state["active"]
        assert material_state["progress"] > 0.6
        await interactive.locator("#return").scroll_into_view_if_needed()
        await interactive.wait_for_timeout(600)
        return_time = await interactive.locator("#story-video").evaluate("video => video.currentTime")
        return_progress = await interactive.evaluate(
            "parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--scroll-progress'))"
        )
        assert return_progress > 0.95
        print(
            f"prototype ok: {duration:.3f}s video, 5 desktop states, 2 mobile states, "
            f"scroll map {material_state['progress']:.2f} -> {return_progress:.2f}; "
            f"Edge time {material_time:.2f}s -> {return_time:.2f}s"
        )
        await edge_browser.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
