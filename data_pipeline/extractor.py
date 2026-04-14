
import uuid
import json
from playwright.sync_api import sync_playwright
from googlesearch import search
import psycopg2
import os
from dotenv import load_dotenv
from extractor_utils import get_ipo_url_professional,scrape_ipo,get_data,get_pinata_url
from sample_upload import upload_pdf_to_astra




# Load the variables from the .env file into the system environment
load_dotenv()

def clean(val):
        if not val: return 0.0
        return float(str(val).replace(',', '').replace('%', '').strip())


def extract_ipo_metrics(file_path):
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tables = data.get('tables', {})
    
    # Helper function to find a keyword anywhere in the JSON tables
    def find_key(keyword):
        for table_id, content in tables.items():
            if keyword in content:
                value = content[keyword]
                # If it's a list, return the first item (usually the most recent)
                return value[0] if isinstance(value, list) else value
        return None

    # Dynamically extract metrics regardless of table number
    pe_ratio    = find_key('P/E (x)')
    eps         = find_key('EPS (₹)')
    roe         = find_key('ROE')
    roce        = find_key('ROCE')
    pat         = find_key('Profit After Tax')
    revenue     = find_key('Total Income') # Revenue is often called Total Income here

    return {
        "PE Ratio": pe_ratio,
        "EPS": eps,
        "ROE": roe,
        "ROCE": roce,
        "PAT": pat,
        "Revenue": revenue
    }


def classify_company(revenue):
    # Priority 1: Revenue Classification
    if revenue >= 5000.00:
        return "Large"
    elif 500 <= revenue < 5000.00:
        return "Mid"
    elif revenue < 500.00:
        # Secondary check: High asset value can bump a small-revenue firm to Mid
        return "Small"
    print("the companyis classifeis")
    return "Unknown"


def add_to_table(ipo_id:uuid.UUID,name:str,ipo_cid:str):
    company=get_ipo_url_professional(name)
    get_data(company)
    result=extract_ipo_metrics("ipo_data.json")
    print(result)

    rev_val = clean(result.get('Revenue'))
    pe_val  = clean(result.get('PE Ratio'))
    eps_val = clean(result.get('EPS'))
    roe_val = clean(result.get('ROE'))
    roce_val = clean(result.get('ROCE'))
    pat_val = clean(result.get('PAT'))
    
    result["cap_size"] = classify_company(rev_val)
    
    try:
            # Connect to the database
            connection = psycopg2.connect(
                dbname=os.environ["POSTGRES_DB"], 
                user=os.environ["POSTGRES_USER"], 
                password=os.environ["POSTGRES_PASSWORD"], 
                host=os.environ["POSTGRES_HOST"], 
                port=os.environ["POSTGRES_PORT"]
            )
            cursor = connection.cursor()

            # Add an entry (Insert)
            insert_query = "INSERT INTO ipo (ipo_id,name,revenue,pe_ratio,eps,roce,roe,pat,cap_size,ipfs_doc_cid) VALUES (%s, %s, %s, %s,%s,%s,%s,%s,%s,%s)"
            print("the error is occuring here")
            record_to_insert = (ipo_id, name, rev_val, pe_val, eps_val, roce_val, roe_val, pat_val, result['cap_size'], ipo_cid)
        
            cursor.execute(insert_query, record_to_insert)
            # Commit changes to save to the database
            connection.commit()
            print("Record inserted successfully")
            url_astra=get_pinata_url(ipo_cid)
            print(url_astra)
            upload_pdf_to_astra(url_astra)


    except Exception as error:
            print(f"Error: {error}")
    finally:
            if connection:
                cursor.close()
                connection.close()
    




'''
if __name__ == "__main__":
   print(add_to_table('905d48c5-9a21-4b9d-aa4f-e44f25a6af27','Innovision','bafybeidiitbmfuruxlwtzixi3dt54tt75gvycmrsyaglnwpo3pr7ljmuwa'))

'''