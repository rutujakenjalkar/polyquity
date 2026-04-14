

from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from playwright.sync_api import sync_playwright
import requests
import io
import uuid
from pypdf import PdfReader
from astrapy import DataAPIClient
import os


def get_pinata_url(cid):
    # Retrieve the gateway from environment variables
    # If not found, it defaults to the public gateway
    gateway = os.getenv("PINATA_GATEWAY", "gateway.pinata.cloud")
    return f"https://{gateway}/ipfs/{cid}"



def get_ipo_url_professional(company_query):
    # Standard Dashboard URL from your screenshots
    url = "https://chittorgarh.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        search_term = company_query.lower()

        # Loop through EVERY link on the page
        for link in soup.find_all("a", href=True):
            # 1. Get the visible text (Standard)
            text = link.text.strip().lower()
            
            # 2. Get the 'title' attribute (Critical for PNGS Reva & GSP Crop)
            title = link.get('title', '').strip().lower()
            
            # 3. Get the URL path itself (The 'Slug')
            href = link['href'].lower()

            # LOGIC: Check all 3 spots to avoid "luck-based" results
            if (search_term in text or search_term in title or search_term.replace(" ", "-") in href) and "/ipo/" in href:
                return urljoin("https://chittorgarh.com", link['href'])
                
        return "Result: Company URL not found (Checked Text, Title, and Href)"

    except Exception as e:
        return f"Error connecting to site: {e}"


def scrape_ipo(url: str) -> dict:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Opening: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        title = page.title()
        ipo_name = page.locator("h1").first.inner_text()

        # Extract all tables
        tables = {}
        table_elements = page.locator("table").all()

        for idx, table in enumerate(table_elements):
            rows = table.locator("tr").all()
            table_data = {}

            for row in rows:
                cells = row.locator("td, th").all()
                texts = [cell.inner_text().strip() for cell in cells]

                if len(texts) >= 2:
                    table_data[texts[0]] = texts[1:] if len(texts) > 2 else texts[1]

            if table_data:
                tables[f"table_{idx + 1}"] = table_data

        browser.close()
    print("the data is scrped")
    return {
        "url": url,
        "page_title": title,
        "ipo_name": ipo_name,
        "tables": tables
    }

def get_data(url:str):
    data = scrape_ipo(url)

    # Save JSON
    with open("ipo_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Data saved to ipo_data.json")






