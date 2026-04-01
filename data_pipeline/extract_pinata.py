import requests
import io
import re
import pymupdf as fitz
import pdfplumber


def extract_printed_page_number(page) -> str | None:
    """
    Extract the page number as printed on the page itself.
    Looks for a standalone number at the top or bottom of the page
    (where page numbers are typically placed in documents).
    """
    blocks = page.get_text("blocks")  # each block: (x0, y0, x1, y1, text, ...)
    page_height = page.rect.height

    # Only look at blocks in the top 10% or bottom 10% of the page
    candidates = []
    for block in blocks:
        x0, y0, x1, y1, text = block[:5]
        text = text.strip()
        in_header = y0 < page_height * 0.10
        in_footer = y1 > page_height * 0.90
        if (in_header or in_footer) and re.fullmatch(r'\d+', text):
            candidates.append(text)

    return candidates[0] if candidates else None


def find_topic_pages(url: str) -> dict:
    """Find page numbers for a list of topics in a PDF from URL."""

    topics = [
        "Summary of Restated Consolidated Statement of Profit and Loss",
        "Summary of Restated Consolidated Statement of Assets and Liabilities"
    ]

    print(f"Fetching PDF from: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    doc = fitz.open(stream=io.BytesIO(response.content), filetype="pdf")
    print(f"Total pages: {len(doc)}\n")

    topic_pages = {topic: [] for topic in topics}

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text().lower()

        for topic in topics:
            if topic.lower() in text:
                # Try to get the number printed on the page itself
                printed_num = extract_printed_page_number(page)
                display = printed_num if printed_num else str(page_num + 1)
                topic_pages[topic].append(display)

    return topic_pages


if __name__ == "__main__":
    url = "https://amethyst-defensive-bovid-22.mypinata.cloud/ipfs/bafybeifj5l5xzac2pxrpojuurwgkfjxbmzpbpljzfvvxslchhskihm2igy?pinataGatewayToken=VcE_9hln7dMXmqBui_l1KyxKkCxInRVzqRPujWj3ItO_vsSS31BoLb6VeWs9vS7A"



    print("\nSearching...\n")
    results = find_topic_pages(url)

    print(results)

    response = requests.get(url)
    response.raise_for_status()

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        print(results['Summary of Restated Consolidated Statement of Profit and Loss'])

        page_num_1based =results['Summary of Restated Consolidated Statement of Profit and Loss'][0]
        print(page_num_1based)
        
        # Access the specific page by subtracting 1 (e.g., Page 5 becomes Index 4)
        target_page = pdf.pages[page_num_1based - 1]
        
        # Extract only that page's text
        content = target_page.extract_text()
        
        print(content)