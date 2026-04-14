import os
from astrapy import DataAPIClient
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI # Or your preferred LLM
load_dotenv()
#print("Astra and Langchain imported successfully.")

# 1. The function that "Heals" the broken text into a proper answer
def get_prospectus_answer(query: str):
    client = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN"))
    db = client.get_database_by_api_endpoint(os.getenv("ASTRA_DB_API_ENDPOINT"))
    collection = db.get_collection("demo")

    # A. Retrieve the 5 "broken" chunks
    results = collection.find(
        sort={"$vectorize": query},
        limit=5,
        projection={"$vectorize": True}
    )
    context_chunks = [doc.get("$vectorize", "") for doc in results]
    raw_context = "\n---\n".join(context_chunks)

    # B. Use an LLM to "Clean and Answer"
    # This turns the "Further, CRISIL," fragments into a professional response
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = f"""
    You are an IPO Expert. Use the following snippets from a Draft Red Herring Prospectus 
    to answer the user's question. If a snippet is cut off, use the other snippets 
    to complete the thought. Provide a professional and accurate answer. Also the answer must be in breif 4-5 lines

    Question: {query}
    
    Context from Prospectus:
    {raw_context}
    
    Answer:"""

    response = llm.invoke(prompt)
    return response.content

'''
print(get_prospectus_answer("""For Om power transmision which are it's major clients"""))
'''