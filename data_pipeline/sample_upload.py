import os
import requests
import io
import uuid
import time
from pypdf import PdfReader
from astrapy import DataAPIClient
from dotenv import load_dotenv
import os
import requests
import io
import uuid
import time
from pypdf import PdfReader
from astrapy import DataAPIClient
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

def upload_pdf_to_astra(pinata_url: str):
    start_time = time.perf_counter()
    
    # 1. SETUP & CONFIG
    astra_token = os.environ["ASTRA_DB_APPLICATION_TOKEN"]
    astra_api_endpoint = os.environ["ASTRA_DB_API_ENDPOINT"]
    collection_name = "polyquity_prospectus"
    
    # NVIDIA limits: 2000 chars is safe for the 512-token limit
    char_limit = 600 
    char_overlap = 200
    batch_size = 20
    max_workers = 5 

    client = DataAPIClient(astra_token)
    db = client.get_database_by_api_endpoint(astra_api_endpoint)
    collection = db.get_collection(collection_name)
    
    # 2. DOWNLOAD & EXTRACT TEXT
    print(f"🚀 Downloading PDF...")
    res = requests.get(pinata_url, stream=True)
    res.raise_for_status()
    pdf_buffer = io.BytesIO(res.content)
    
    reader = PdfReader(pdf_buffer)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text.strip() + "\n"
    
    # 3. CHUNKING
    chunks = []
    start = 0
    while start < len(full_text):
        chunks.append(full_text[start : start + char_limit])
        start += (char_limit - char_overlap)

    # 4. PREPARE DOCUMENTS
    documents = [
        {
            "_id": str(uuid.uuid4()),
            "$vectorize": chunk,
            "metadata": {"chunk_index": i, "text": chunk, "source": pinata_url}
        } for i, chunk in enumerate(chunks)
    ]

    # 5. DEFINE WORKER & EXECUTE PARALLEL UPLOAD
    # We define the batch function inside the main function to keep it all in one
    def worker_upload(batch_data, b_idx):
        for attempt in range(3):
            try:
                collection.insert_many(batch_data)
                return f"✅ Batch {b_idx} done"
            except Exception as e:
                if "429" in str(e) or "timeout" in str(e).lower():
                    time.sleep(2 * (attempt + 1))
                    continue
                return f"❌ Batch {b_idx} error: {e}"
        return f"❌ Batch {b_idx} failed after retries"

    batches = [documents[i : i + batch_size] for i in range(0, len(documents), batch_size)]
    print(f"📦 Uploading {len(chunks)} chunks in {len(batches)} batches...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_upload, b, i) for i, b in enumerate(batches)]
        for future in as_completed(futures):
            print(future.result())

    total_time = time.perf_counter() - start_time
    print(f"\n✨ FINISHED in {total_time:.2f} seconds.")

'''
# ── Usage ─────────────────────────────────────────────────────────────────────
upload_pdf_to_astra("https://gateway.pinata.cloud/ipfs/bafybeieppaobv5w3xyupb67qlk5ilw757z7mbesakannwdnpevvbkdex7q")
'''