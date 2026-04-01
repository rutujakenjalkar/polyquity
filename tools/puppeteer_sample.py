"""
Scrape IPO details from chittorgarh.com using Playwright (Python).
Playwright is the modern Python equivalent of Node.js Puppeteer.

Install dependencies:
    pip install playwright
    playwright install chromium
"""

import json
from playwright.sync_api import sync_playwright

URL = "https://www.chittorgarh.com/ipo/bvishal-oil-and-energy-ipo/2988/"


def scrape_ipo(url: str) -> dict:
    with sync_playwright() as p:
        # Launch headless Chromium (same engine as Puppeteer)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            )
        )

        print(f"Opening: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)

        # ── Page title ──────────────────────────────────────────────────────
        title = page.title()
        print(f"Page title: {title}")

        # ── IPO name (h1) ───────────────────────────────────────────────────
        ipo_name = page.locator("h1").first.inner_text()

        # ── Key detail tables  ───────────────────────────────────────────────
        # Chittorgarh renders IPO info in <table> blocks.
        # We grab every table on the page as key→value pairs.
        tables = {}
        table_elements = page.locator("table").all()

        for idx, table in enumerate(table_elements):
            rows = table.locator("tr").all()
            table_data = {}
            for row in rows:
                cells = row.locator("td, th").all()
                if len(cells) >= 2:
                    key   = cells[0].inner_text().strip()
                    value = cells[1].inner_text().strip()
                    if key:
                        table_data[key] = value
            if table_data:
                tables[f"table_{idx + 1}"] = table_data

        # ── Subscription status (if rendered) ──────────────────────────────
        subscription = {}
        sub_rows = page.locator(".subscription-table tr, table.table-bordered tr").all()
        for row in sub_rows:
            cells = row.locator("td, th").all()
            if len(cells) >= 2:
                key   = cells[0].inner_text().strip()
                value = cells[-1].inner_text().strip()
                if key:
                    subscription[key] = value

        # ── Full visible text (fallback) ────────────────────────────────────
        body_text = page.locator("body").inner_text()

        browser.close()

    return {
        "url":          url,
        "page_title":   title,
        "ipo_name":     ipo_name,
        "tables":       tables,
        "subscription": subscription,
        "body_snippet": body_text[:2000],   # first 2000 chars as a preview
    }


def main():
    data = scrape_ipo(URL)

    print("\n" + "=" * 60)
    print(f"IPO Name : {data['ipo_name']}")
    print("=" * 60)

    for table_name, rows in data["tables"].items():
        print(f"\n── {table_name} ──")
        for k, v in rows.items():
            print(f"  {k:<35} {v}")

    # Save full result to JSON
    out_path = "ipo_data.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Full data saved to: {out_path}")


if __name__ == "__main__":
    main()