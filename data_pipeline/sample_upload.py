import io
import os
import time
import uuid

import requests
from astrapy import DataAPIClient
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()


def upload_pdf_to_astra(pinata_url: str):
    start_time = time.perf_counter()
    astra_token = os.environ["ASTRA_DB_APPLICATION_TOKEN"]
    astra_api_endpoint = os.environ["ASTRA_DB_API_ENDPOINT"]
    collection_name = os.environ["ASTRA_COLLECTION"]
    chunk_size = int(os.getenv("CHUNK_SIZE", 500))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 100))
    batch_size = int(os.getenv("BATCH_SIZE", 20))

    client = DataAPIClient(astra_token)
    db = client.get_database_by_api_endpoint(astra_api_endpoint)
    collection = db.get_collection(collection_name)
    print(f"Using existing collection: {collection_name}")

    response = requests.get(pinata_url, stream=True)
    response.raise_for_status()
    pdf_buffer = io.BytesIO(response.content)

    reader = PdfReader(pdf_buffer)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            full_text += text.strip() + "\n"

    print(f"Extracted {len(full_text.split())} words from {len(reader.pages)} pages.")

    words = full_text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start + chunk_size])
        chunks.append(chunk)
        start += chunk_size - chunk_overlap

    print(f"Created {len(chunks)} chunks.")

    documents = [
        {
            "_id": str(uuid.uuid4()),
            "chunk_index": i,
            "text": chunk,
            "source_url": pinata_url,
        }
        for i, chunk in enumerate(chunks)
    ]

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        collection.insert_many(batch)
        print(f"Inserted batch {i // batch_size + 1} ({len(batch)} docs)")

    print(f"Uploaded {len(documents)} chunks successfully.")
    total_time = time.perf_counter() - start_time
    print(f"Total execution time: {total_time:.2f} seconds")
    return documents


upload_pdf_to_astra(
    "https://amethyst-defensive-bovid-22.mypinata.cloud/ipfs/"
    "bafybeig6awp2ktcmdapa3nf3rb5rwvcwlwqlcadjfgghtehoigki5jb4gy"
    "?pinataGatewayToken=VcE_9hln7dMXmqBui_l1KyxKkCxInRVzqRPujWj3ItO_vsSS31BoLb6VeWs9vS7A"
)
