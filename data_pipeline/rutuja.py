import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
'''

def get_ipo_url_by_searching_list(company_query):
    # This is the 'Master List' page that contains all IPO links
    list_url = "https://chittorgarh.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    try:
        # 1. 'Go' to the website
        response = requests.get(list_url, headers=headers, timeout=15)
        if response.status_code != 200:
            return f"Failed to access site: {response.status_code}"

        # 2. 'Search' the page content for your company
        soup = BeautifulSoup(response.text, "html.parser")
        
        # We look for all links that contain your company name
        for link in soup.find_all("a", href=True):
            name_on_site = link.text.strip().lower()
            
            # 3. Match the name and 'Get' the URL
            if company_query.lower() in name_on_site and "/ipo/" in link['href']:
                # Construct the full absolute URL
                return urljoin("https://www.chittorgarh.com", link['href'])
        print("this is the extractor.")
        return "Company link not found on the page."

    except Exception as e:
        return f"Error: {e}"

# Usage
company = "Shadowfax Technologies"
print(get_ipo_url_by_searching_list(company))'''

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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


