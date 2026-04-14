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

    # Load JSON file
    with open('ipo_data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extract table_5
    table_5 = data.get("tables", {}).get("table_5", {})

    # Print the result
    print("Table 5 Data:")
    for key, value in table_5.items():
        print(f"{key}: {value}")




if __name__ == "__main__":
    main()


'''

def upload_pdf_to_astra(pinata_url: str):
    start_time = time.perf_counter()
    astra_token        = os.environ["ASTRA_DB_APPLICATION_TOKEN"]
    astra_api_endpoint = os.environ["ASTRA_DB_API_ENDPOINT"]
    collection_name    = "demo"
    chunk_size         = int(os.getenv("CHUNK_SIZE", 100))
    chunk_overlap      = int(os.getenv("CHUNK_OVERLAP", 20))
    batch_size         = int(os.getenv("BATCH_SIZE", 20))

    # Alter collection to deny indexing on text field (run-safe, can be called repeatedly)
    client = DataAPIClient(astra_token)
    db = client.get_database_by_api_endpoint(astra_api_endpoint)
    db.get_collection("demo")
    print("✅ Collection altered — text field non-indexed")

    # Fetch PDF into memory
    response = requests.get(pinata_url, stream=True)
    response.raise_for_status()
    pdf_buffer = io.BytesIO(response.content)

    # Extract text
    reader = PdfReader(pdf_buffer)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            full_text += text.strip() + "\n"

    print(f"Extracted {len(full_text.split())} words from {len(reader.pages)} pages.")

    # Chunk with overlap
    words = full_text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start + chunk_size])
        chunks.append(chunk)
        start += chunk_size - chunk_overlap

    print(f"Created {len(chunks)} chunks.")

    # Build documents
    documents = [
        {
        "_id": str(uuid.uuid4()),
        "$vectorize": chunk,
        "chunk_index": i,
        "text": chunk,
        "source_url": pinata_url,
        }
        for i, chunk in enumerate(chunks)
    ]

    # Upload to AstraDB in batches
    collection = db.get_collection(collection_name)
    for i in range(0, len(documents), batch_size):
        collection.insert_many(documents[i:i + batch_size])
        print(f"Inserted batch {i // batch_size + 1} ({len(documents[i:i + batch_size])} docs)")

    print(f"✅ Uploaded {len(documents)} chunks successfully.")
    total_time = time.perf_counter() - start_time
    print(f"Total execution time: {total_time:.2f} seconds")
    return documents
'''