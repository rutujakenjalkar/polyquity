
import uuid
import json
from playwright.sync_api import sync_playwright
from googlesearch import search
import psycopg2

URL = "https://www.chittorgarh.com/ipo/gsp-crop-ipo/2031/"


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

    return {
        "url": url,
        "page_title": title,
        "ipo_name": ipo_name,
        "tables": tables
    }


def main():
    data = scrape_ipo(URL)

    # Save JSON
    with open("ipo_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Data saved to ipo_data.json")



def extract_ipo_metrics(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tables = data.get('tables', {})

    # 1. PE Ratio & EPS (from table_9 - Pre IPO column)
    # The list contains [Pre IPO, Post IPO]
    pe_ratio = tables.get('table_9', {}).get('P/E (x)', [None])[0]
    eps = tables.get('table_9', {}).get('EPS (₹)', [None])[0]

    # 2. ROE & Debt/Equity (from table_8 - most recent period: Sep 30, 2025)
    # The list contains [Sep 30 2025, Mar 31 2025]
    roe = tables.get('table_8', {}).get('ROE', [None])[0]
    debt_equity = tables.get('table_8', {}).get('Debt/Equity', [None])[0]

    # 3. PAT & Revenue (from table_6 - most recent period: 30 Sep 2025)
    # The list contains [30 Sep 2025, 31 Mar 2025, 31 Mar 2024, 31 Mar 2023]
    pat = tables.get('table_6', {}).get('Profit After Tax', [None])[0]
    revenue = tables.get('table_6', {}).get('Total Income', [None])[0]

    return {
        "PE Ratio": pe_ratio,
        "EPS": eps,
        "ROE": roe,
        "Debt/Equity": debt_equity,
        "PAT": pat,
        "Revenue": revenue
    }


def classify_company(revenue):
    """
    Classifies a Media & Entertainment company based on industry benchmarks.
    Thresholds: Large > 5B, Mid 500M-5B, Small < 500M.
    Assumes values are in Millions (e.g., 847.61 = $847.61M).
    """
    
    # Priority 1: Revenue Classification
    if revenue >= 5000.00:
        return "Large"
    elif 500 <= revenue < 5000.00:
        return "Mid"
    elif revenue < 500.00:
        # Secondary check: High asset value can bump a small-revenue firm to Mid
        return "Small"
    
    return "Unknown"


def add_to_table(ipo_id:uuid.UUID,name:str,ipo_cid:str):
    main()
    result=extract_ipo_metrics("ipo_data.json")
    result["cap_size"]=classify_company(float(result['Revenue']))
    print(result)
    s = result['ROE']
    roe = float(s.strip("%"))
    print(roe)  # Output: 15.62

    try:
            # Connect to the database
            connection = psycopg2.connect(
                dbname="POLYQUITY_DATA", 
                user="postgres", 
                password="rutuja", 
                host="localhost", 
                port="5432"
            )
            cursor = connection.cursor()

            # Add an entry (Insert)
            insert_query = "INSERT INTO ipo (ipo_id,name,revenue,pe_ratio,eps,equity,roe,pat,cap_size,ipfs_doc_cid) VALUES (%s, %s, %s, %s,%s,%s,%s,%s,%s,%s)"
            record_to_insert = (ipo_id,name,float(result['Revenue']),float(result['PE Ratio']),float(result['EPS']),float(result['Debt/Equity']),roe,float(result['PAT']),result['cap_size'],ipo_cid)
            cursor.execute(insert_query, record_to_insert)

            # Commit changes to save to the database
            connection.commit()
            print("Record inserted successfully")

    except Exception as error:
            print(f"Error: {error}")
    finally:
            if connection:
                cursor.close()
                connection.close()
    




if __name__ == "__main__":
   print(add_to_table("b0632b91-6ac5-4dab-bd13-437b5cc703dc","gsp-crop-ipo","QmdfTbBqBPQ7VNxZEYEj14VmRuZBkqFbiwReogJgS1zR1n"))
