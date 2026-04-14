# Polyquity
AI-Powered Advisory Agent for a Blockchain-Based IPO Bidding System.

Quick links:
- `./data_pipeline/`
- `./tools/`
- `./database/schema.sql`

## 1) Prerequisites (Windows)
- Python 3.12+ installed
- PostgreSQL + pgAdmin installed: https://www.postgresql.org/download/
- pgvector installed/enabled for your Postgres instance: https://github.com/pgvector/pgvector
- Pinata account (to upload prospectus PDFs): https://pinata.cloud/
- DataStax Astra DB Serverless (vector) database (for prospectus chunk storage/search)

## 2) Install Dependencies (PowerShell)
From the repo root:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 3) Environment Variables
Copy `.env.example` to `.env` and fill values.

Minimum required keys:
- Postgres: `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`
- Astra: `ASTRA_DB_APPLICATION_TOKEN`, `ASTRA_DB_API_ENDPOINT`
- Pinata: `PINATA_GATEWAY` (default `gateway.pinata.cloud` is fine)
- LLM: `OPENAI_API_KEY` (needed for `./tools/prospectus_tool.py` and the agent)

Optional tuning keys (pipeline):
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `BATCH_SIZE`

## 4) PostgreSQL Setup
1. Create a database (example name used by code: `POLYQUITY_DATA`).
2. Run the schema file: `./database/schema.sql`

Example using `psql`:

```powershell
psql -U postgres -d POLYQUITY_DATA -f .\database\schema.sql
```

If you prefer pgAdmin: open Query Tool and run the contents of `./database/schema.sql`.

## 5) Pinata Setup (Get CID)
1. Upload the IPO prospectus PDF to Pinata.
2. Copy the CID (looks like `bafy...`). You will pass this CID into the ETL script.

## 6) Astra DB Setup (Token + Endpoint + Collection)
1. Create an Astra DB Serverless database with Vector enabled.
2. In Data Explorer, create a collection named `demo`.
   - Current code uses `db.get_collection("demo")` in a few places.
3. Generate an Application Token and copy it (starts with `AstraCS:...`).
4. Copy the API Endpoint from the database details page.
   - Looks like: `https://<DB_ID>-<REGION>.apps.astra.datastax.com`

Docs:
- https://docs.datastax.com/en/astra-db-serverless/get-started/quickstart.html
- https://docs.datastax.com/en/astra/docs/obtaining-database-credentials.html

## 7) Run ETL (Insert into Postgres + Upload Prospectus to Astra)
1. Pick an IPO name from Chittorgarh (use the exact IPO name): https://www.chittorgarh.com/
2. Get the prospectus PDF CID from Pinata.
3. Generate a UUID (temporary is fine): https://www.uuidgenerator.net/
4. Update the `if __name__ == "__main__":` call in `./data_pipeline/extractor.py` with:
   - `ipo_id` (UUID string)
   - `name` (IPO name string)
   - `ipo_cid` (Pinata CID string)

Run:

```powershell
python .\data_pipeline\extractor.py
```

Repeat for ~9 IPOs (or as needed).

## 8) Add Transactions (Manual)
Add sample rows to the `transaction` table for the inserted IPOs (needed for recommendations).

## 9) Run the Agent
Pick a `wallet_address` that exists in `transaction` and run:

```powershell
python -m agents.recommendation_agent
```

