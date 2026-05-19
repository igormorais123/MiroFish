"""E2E Playwright local — captura erros de console no Step4Report.

Roda fora de pytest porque depende de servidores live em 127.0.0.1.
Uso:
    python tests/phase03_e2e_validation.py
"""

from __future__ import annotations

import asyncio
import json
import sys


async def main() -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("playwright nao instalado; execute: pip install playwright && playwright install chromium")
        return 2

    console_errors: list[str] = []
    console_warnings: list[str] = []
    network_failures: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text)
                if msg.type == "error"
                else console_warnings.append(msg.text)
                if msg.type == "warning"
                else None
            ),
        )
        page.on(
            "response",
            lambda r: network_failures.append(f"{r.status} {r.url}") if r.status >= 400 else None,
        )

        await page.goto("http://127.0.0.1:5173/report/report_c7762071893d", wait_until="networkidle")
        await page.wait_for_timeout(1500)

        result = await page.evaluate(
            """() => ({
                lgpdBanner: !!document.querySelector('[data-testid=\"vox-lgpd-banner\"]'),
                ceiling: document.querySelector('[data-testid=\"vox-ceiling\"]')?.textContent?.trim() || null,
                dpd: document.querySelector('[data-testid=\"vox-dpd\"]')?.textContent?.trim() || null,
                replicators: document.querySelector('[data-testid=\"vox-replicators\"]')?.textContent?.trim() || null,
                blindTest: document.querySelector('[data-testid=\"vox-blind-test\"]')?.textContent?.trim() || null,
                voxPanel: !!document.querySelector('.vox-science-panel'),
                voxMetricsCount: document.querySelectorAll('.vox-science-metric').length,
            })"""
        )

        await browser.close()

    print(json.dumps({
        "ui": result,
        "console_errors": console_errors,
        "console_warnings": console_warnings,
        "network_failures": network_failures,
    }, ensure_ascii=False, indent=2))

    failures = 0
    if console_errors:
        print(f"FAIL: {len(console_errors)} console errors")
        failures += 1
    if network_failures:
        print(f"FAIL: {len(network_failures)} network failures (>=400)")
        failures += 1
    if not result.get("lgpdBanner") or not result.get("voxPanel"):
        print("FAIL: UI elements missing")
        failures += 1
    if failures == 0:
        print("ALL CHECKS PASS: console limpo, network sem 4xx/5xx, UI elementos presentes.")
    return failures


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
