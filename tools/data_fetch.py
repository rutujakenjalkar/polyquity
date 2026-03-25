from ast import pattern
import os
from urllib import response

from dotenv import load_dotenv

from db_utils import execute_postgres_query

load_dotenv()
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




def get_ipfs_url(company_list):
    # Ensure company_list is a tuple for the IN clause
    params = tuple(f"%{name.strip().lower()}%" for name in company_list)

    # 2. Build the conditions string
    # For 3 names: "lower(ipo.name) LIKE %s OR lower(ipo.name) LIKE %s OR lower(ipo.name) LIKE %s"
    conditions = " OR ".join(["lower(ipo.name) LIKE %s"] * len(params))

    query = f"""
        SELECT url.url 
        FROM ipfs_urls url 
        JOIN ipo ON ipo.ipo_id = url.ipo_id 
        WHERE {conditions};
    """
    print(query)
    

    # Use params= to skip all the host/db/user positional arguments
    rows=execute_postgres_query(query, params=params)
    urls=[row[0] for row in rows]

    return urls

# Test call
#print(get_ipfs_url(["Belrise","Ola Electric","Nykaa"]))

def data_fetch(question:str):
        
        text_data = question

        response = client.responses.create(
            model="gpt-4o-mini",
            input=f"""
        Here is the text:
        {text_data}

        Question: Find out the companies names about which questions are asked and put them in a list.And return the list only.Incase the name is not clear or has spelling errors then give your best guess.
        eg: If the question is "What is the revenue of Nykaa and Ola Electric?" then the output should be ["Nykaa", "Ola Electric"]
        """,
        )

        return response.output_text
        
print(data_fetch("What is the WHAT IS THE SHAREHOLDING OF HYUNDAI AND BELsirE?"))