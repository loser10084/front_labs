import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


URL = "http://127.0.0.1:5174/prototypes/continuous-video-v2-1080p/"
OUTPUT = Path(__file__).parent / "previews"


async def capture(page, scene_id: str, filename: str) -> None:
    await page.locator(scene_id).scroll_into_view_if_needed()
    await page.wait_for_timeout(450)
    await page.locator("#capture-frame").evaluate("image => image.decode()")
    await page.screenshot(path=str(OUTPUT / filename))


async def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    async with async_playwright() as playwright:
        chromium = await playwright.chromium.launch(headless=True)
        page = await chromium.new_page(viewport={"width": 1440, "height": 900})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: errors.append(f"{message.type}: {message.text}")
            if message.type in {"warning", "error"}
            else None,
        )
        response = await page.goto(f"{URL}?capture=1", wait_until="networkidle")
        assert response and response.status == 200
        assert await page.title() == "VENUS — 1080p 连续滚动界面原型"
        await page.wait_for_function("window.__scrollCanvas?.ready")
        dimensions = await page.locator("#story-canvas").evaluate(
            "canvas => [canvas.width, canvas.height]"
        )
        assert dimensions == [1920, 1080], dimensions

        await capture(page, "#opening", "01-opening.png")
        await capture(page, "#form", "02-form.png")
        await capture(page, "#seam", "03-repair.png")
        await capture(page, "#matter", "04-material.png")
        await capture(page, "#return", "05-return.png")
        assert not errors, errors
        assert not await page.evaluate("document.documentElement.scrollWidth > innerWidth")

        mobile = await chromium.new_page(viewport={"width": 390, "height": 844})
        await mobile.goto(f"{URL}?capture=1", wait_until="networkidle")
        await mobile.wait_for_function("window.__scrollCanvas?.ready")
        await capture(mobile, "#opening", "mobile-opening.png")
        await capture(mobile, "#matter", "mobile-material.png")
        assert not await mobile.evaluate("document.documentElement.scrollWidth > innerWidth")

        edge = await playwright.chromium.launch(channel="msedge", headless=True)
        interactive = await edge.new_page(viewport={"width": 1440, "height": 900})
        edge_errors: list[str] = []
        interactive.on("pageerror", lambda error: edge_errors.append(str(error)))
        interactive.on(
            "console",
            lambda message: edge_errors.append(f"{message.type}: {message.text}")
            if message.type in {"warning", "error"}
            else None,
        )
        await interactive.goto(URL, wait_until="networkidle")
        await interactive.wait_for_function("window.__scrollCanvas?.ready")
        assert await interactive.evaluate("window.__scrollCanvas.scrollMode") == "direct"
        assert await interactive.evaluate("window.__scrollCanvas.directWheelEnabled") is True
        assert await interactive.locator("#scroll-mode-value").text_content() == "直控"
        await interactive.locator("#scroll-mode").click()
        assert await interactive.evaluate("window.__scrollCanvas.scrollMode") == "native"
        assert await interactive.evaluate("window.__scrollCanvas.directWheelEnabled") is False
        await interactive.locator("#scroll-mode").click()
        assert await interactive.evaluate("window.__scrollCanvas.scrollMode") == "direct"
        assert await interactive.evaluate("window.__scrollCanvas.directWheelEnabled") is True

        inertia_result = await interactive.evaluate(
            """async () => {
                window.scrollTo(0, 0);
                const telemetry = window.__scrollCanvas;
                telemetry.acceptedWheelEvents = 0;
                telemetry.rejectedWheelEvents = 0;
                const deltas = [120, 110, 92, 70, 48, 28, 14, 6];
                for (const deltaY of deltas) {
                    window.dispatchEvent(new WheelEvent('wheel', {
                        deltaY,
                        deltaMode: WheelEvent.DOM_DELTA_PIXEL,
                        bubbles: true,
                        cancelable: true
                    }));
                    await new Promise(resolve => setTimeout(resolve, 16));
                }
                const decaying = {
                    accepted: telemetry.acceptedWheelEvents,
                    rejected: telemetry.rejectedWheelEvents,
                    scrollY
                };

                telemetry.acceptedWheelEvents = 0;
                telemetry.rejectedWheelEvents = 0;
                await new Promise(resolve => setTimeout(resolve, 120));
                for (const deltaY of [80, 80, 80, 80]) {
                    window.dispatchEvent(new WheelEvent('wheel', {
                        deltaY,
                        deltaMode: WheelEvent.DOM_DELTA_PIXEL,
                        bubbles: true,
                        cancelable: true
                    }));
                    await new Promise(resolve => setTimeout(resolve, 16));
                }
                await new Promise(requestAnimationFrame);
                return {
                    decaying,
                    constant: {
                        accepted: telemetry.acceptedWheelEvents,
                        rejected: telemetry.rejectedWheelEvents
                    }
                };
            }"""
        )
        assert inertia_result["decaying"]["accepted"] <= 1, inertia_result
        assert inertia_result["decaying"]["rejected"] >= 7, inertia_result
        assert inertia_result["decaying"]["scrollY"] > 0, inertia_result
        assert inertia_result["constant"]["accepted"] == 4, inertia_result
        assert inertia_result["constant"]["rejected"] == 0, inertia_result

        result = await interactive.evaluate(
            """async () => {
                const maxScroll = document.documentElement.scrollHeight - innerHeight;
                const telemetry = window.__scrollCanvas;
                const waitForFrame = async (frame, timeout = 5000) => {
                    const started = performance.now();
                    while (telemetry.presentedFrame !== frame && performance.now() - started < timeout) {
                        await new Promise(resolve => setTimeout(resolve, 5));
                    }
                    return performance.now() - started;
                };
                const go = async progress => {
                    const frame = Math.round(progress * 299);
                    window.scrollTo(0, maxScroll * progress);
                    const latency = await waitForFrame(frame);
                    return { frame, latency, presented: telemetry.presentedFrame };
                };
                const measure = async (from, to) => {
                    await go(from);
                    await new Promise(resolve => setTimeout(resolve, 60));
                    const started = performance.now();
                    const result = await go(to);
                    return { ...result, total: performance.now() - started };
                };
                const measureContinuousScroll = async (from, to) => {
                    await go(from);
                    const target = Math.round(to * 299);
                    let maxLag = 0;
                    for (let step = 1; step <= 120; step += 1) {
                        const progress = from + (to - from) * (step / 120);
                        window.scrollTo(0, maxScroll * progress);
                        await new Promise(requestAnimationFrame);
                        maxLag = Math.max(maxLag, Math.abs(telemetry.targetFrame - telemetry.presentedFrame));
                    }
                    const settleLatency = await waitForFrame(target);
                    return {
                        presented: telemetry.presentedFrame,
                        target,
                        maxLag,
                        settleLatency
                    };
                };

                const short = {
                    start: await measure(0, 0.03),
                    middle: await measure(0.5, 0.53),
                    end: await measure(1, 0.97)
                };
                const largeJump = await measure(0, 0.15);
                const down = await measureContinuousScroll(0, 1);
                const up = await measureContinuousScroll(1, 0);
                return {
                    short, largeJump, down, up,
                    scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior,
                    ...telemetry
                };
            }"""
        )
        for state in result["short"].values():
            assert state["presented"] == state["frame"], result
            assert state["latency"] < 120, result
        assert result["largeJump"]["presented"] == result["largeJump"]["frame"], result
        assert result["largeJump"]["latency"] < 100, result
        assert result["down"]["presented"] == 299, result
        assert result["up"]["presented"] == 0, result
        assert result["down"]["maxLag"] <= 18, result
        assert result["up"]["maxLag"] <= 18, result
        assert result["down"]["settleLatency"] < 100, result
        assert result["up"]["settleLatency"] < 100, result
        assert result["scrollBehavior"] == "auto", result
        assert result["maxConcurrentDraws"] == 1, result

        await interactive.evaluate("window.scrollTo(0, 0)")
        await interactive.wait_for_function("window.__scrollCanvas.presentedFrame === 0")
        await interactive.mouse.wheel(0, 600)
        await interactive.wait_for_timeout(100)
        wheel_y = await interactive.evaluate("scrollY")
        await interactive.wait_for_timeout(250)
        wheel_y_after = await interactive.evaluate("scrollY")
        assert abs(wheel_y_after - wheel_y) <= 1, (wheel_y, wheel_y_after)
        await interactive.wait_for_function(
            "window.__scrollCanvas.presentedFrame === window.__scrollCanvas.targetFrame"
        )
        assert await interactive.evaluate("window.__scrollCanvas.wheelEvents > 0")
        assert await interactive.evaluate("window.__scrollCanvas.scrollEvents > 0")
        assert not edge_errors, edge_errors
        print(
            f"canvas prototype ok: {dimensions[0]}x{dimensions[1]}, 300 WebP frames; "
            f"short scrub ms start/middle/end "
            f"{result['short']['start']['latency']:.1f}/"
            f"{result['short']['middle']['latency']:.1f}/"
            f"{result['short']['end']['latency']:.1f}; "
            f"continuous max lag down/up {result['down']['maxLag']}/"
            f"{result['up']['maxLag']} frames; settle ms "
            f"{result['down']['settleLatency']:.1f}/"
            f"{result['up']['settleLatency']:.1f}; "
            f"post-wheel drift {abs(wheel_y_after - wheel_y):.1f}px; "
            f"max concurrent draws {result['maxConcurrentDraws']}"
        )
        await edge.close()
        await chromium.close()


if __name__ == "__main__":
    asyncio.run(main())
