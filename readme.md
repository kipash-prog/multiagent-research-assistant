<img width="1288" height="603" alt="image" src="https://github.com/user-attachments/assets/498b66a0-bc6c-4a45-90b4-f2b8e4000f17" />

# Multiagent Research Assistant

 An end-to-end research assistant that gathers sources from the web and produces concise, high-quality summaries using an agentic backend.

 - **Backend**: Django REST API with modular agents
 - **Research**: SerpAPI + Wikipedia fallback
 - **Summarization**: Hugging Face Transformers (BART)
 - **Frontend**: React app (optional)

---

## Features
 - **Query endpoint** to gather N sources and synthesize a summary.
 - **Pluggable research agent** with SerpAPI and Wikipedia fallback.
 - **Tokenizer-aware chunking** and two-pass summarization for long inputs.
 - **Persistent storage** of queries, documents, and summaries.

---

## Architecture
 - **backend/**: Django project and `core` app
   - `core/agents/research_gathering.py`: fetches sources (SerpAPI → Wikipedia fallback)
   - `core/agents/summarization.py`: BART summarization with safe token chunking
   - `core/agents/knowledge_manager.py`: persists documents and summaries
   - `core/views.py`: REST endpoints
 - **frontend/**: React UI (optional)

---

## Prerequisites
 - Python 3.10+
 - Node 18+ (only if running the frontend)
 - A valid **SerpAPI** key

---

## Backend Setup

 1. Create and activate a virtual environment
    ```bash
    python -m venv .venv
    .venv\Scripts\activate  # Windows
    # source .venv/bin/activate  # macOS/Linux
    ```

 2. Install dependencies
    ```bash
    pip install -r backend/requirements.txt
    ```

 3. Environment variables
    Create `backend/.env` with:
    ```env
    SERPAPI_KEY=your_serpapi_key
    ```
    If you maintain a separate `backend/backend/.env`, mirror the same key there.

 4. Database migrations
    ```bash
    python backend/manage.py migrate
    ```

 5. Run the server
    ```bash
    python backend/manage.py runserver
    ```

 The API will be available at `http://127.0.0.1:8000/`.

---

## API Usage

 - **POST** `/api/query/`
   - Request body
     ```json
     {
       "query_text": "AI in healthcare",
       "summary_type": "medium"  // one of: short | medium | long
     }
     ```
   - Behavior
     - Gathers up to 4 sources via SerpAPI (Wikipedia fallback on error/empty)
     - Summarizes the combined content via BART
     - Persists the query, documents, and summary
   - Response
     - Returns the serialized Query record, including linked documents and summary IDs.

 - **GET** `/api/queries/`
   - List recent queries

 - **GET** `/api/queries/<id>/`
   - Retrieve a specific query

---

## Frontend (optional)
 If you plan to run the React frontend:
```bash
cd frontend
npm install
npm start
```
 Configure the frontend API base URL if needed.

---

## Configuration Notes
 - SerpAPI quota and rate limits apply. If results are empty or an error occurs, the system falls back to Wikipedia.
 - First run will download the BART model weights (hundreds of MB). Subsequent runs use the cache.
 - For faster inference, consider `sshleifer/distilbart-cnn-12-6` in `summarization.py`.

---

## Development
 - Code style: follow existing patterns; keep agents modular.
 - Tests: add Django tests under `backend/core/tests/`.
 - Secrets: do not commit `.env` files or API keys.

---

## Troubleshooting
 - Summaries cut short or time out
   - Reduce `summary_type` or adjust generation parameters in `summarization.py`.
 - No research results
   - Verify `SERPAPI_KEY` is valid and has quota; Wikipedia fallback should still provide basic content.
 - Model download failures
   - Ensure network access; optionally pre-download models or configure HF cache directory.

---

## License
 MIT (or project-specific). Update as appropriate.
