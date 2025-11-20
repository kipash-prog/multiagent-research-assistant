<img width="1288" height="603" alt="image" src="https://github.com/user-attachments/assets/498b66a0-bc6c-4a45-90b4-f2b8e4000f17" />

## Multiagent Research Assistant

An end-to-end research assistant that gathers sources from the web and produces concise, high-quality summaries using an agentic backend.

- **Backend**: Django REST API with modular agents
- **Research**: SerpAPI + Wikipedia fallback
- **Summarization**: Hugging Face Transformers (BART)
- **Frontend**: React app (optional)

---

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
  - [System Overview](#system-overview)
  - [Agent Orchestration Framework](#agent-orchestration-framework)
- [Agent Communication & Coordination](#agent-communication--coordination)
  - [Research Gathering Agent](#1-research-gathering-agent)
  - [Summarization Agent](#2-summarization-agent)
  - [Knowledge Manager Agent](#3-knowledge-manager-agent)
- [Task Management & Workflow](#task-management--workflow)
  - [Synchronous Sequential Execution](#synchronous-sequential-execution)
  - [Error Handling & Resilience](#error-handling--resilience)
  - [Data Flow & State Management](#data-flow--state-management)
  - [Inter-Agent Communication](#inter-agent-communication)
  - [Complete Orchestration Flow Example](#complete-orchestration-flow-example)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup-optional)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Starting the Application](#starting-the-application)
  - [API Endpoints](#api-endpoints)
  - [Using the Frontend](#using-the-frontend)
- [API Examples](#api-examples)
- [Important Notes](#important-notes)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
  - [Contributing](#contributing)
  - [Running Tests](#running-tests)
  - [Project Structure](#project-structure)
  - [Adding New Features](#adding-new-features)
  - [Future Enhancements: Async Orchestration](#future-enhancements-async-orchestration)
  - [Monitoring & Observability](#monitoring--observability)
- [FAQ](#faq)
- [License](#license)

---

## Features
- **Query endpoint** to gather N sources and synthesize a summary
- **Pluggable research agent** with SerpAPI and Wikipedia fallback
- **Tokenizer-aware chunking** and two-pass summarization for long inputs
- **Persistent storage** of queries, documents, and summaries
- **RESTful API** for easy integration
- **React frontend** for user-friendly interaction (optional)

---

## Architecture

### System Overview
- **backend/**: Django project and `core` app
  - `core/agents/research_gathering.py`: fetches sources (SerpAPI → Wikipedia fallback)
  - `core/agents/summarization.py`: BART summarization with safe token chunking
  - `core/agents/knowledge_manager.py`: persists documents and summaries
  - `core/views.py`: REST endpoints and orchestration controller
- **frontend/**: React UI (optional)

### Agent Orchestration Framework

The system implements a **Sequential Pipeline Pattern** for agent coordination, orchestrated through Django REST views. This lightweight approach provides deterministic, synchronous workflow execution without the overhead of complex orchestration frameworks.

#### **Orchestration Pattern: Sequential Coordinator**

The `QueryView` in `core/views.py` acts as the **central orchestrator** that:
1. Receives incoming requests
2. Coordinates agent execution in a defined sequence
3. Manages data flow between agents
4. Handles error states and fallbacks
5. Returns aggregated results

**Workflow Diagram:**
```
Client Request
      ↓
[QueryView Orchestrator]
      ↓
┌─────────────────────────────────────────────┐
│  1. Create Query Record (Database)          │
└─────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────┐
│  2. Research Gathering Agent                │
│     ├─ Try SerpAPI search                   │
│     └─ Fallback to Wikipedia if needed      │
└─────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────┐
│  3. Knowledge Manager Agent                 │
│     └─ Store documents in database          │
└─────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────┐
│  4. Summarization Agent                     │
│     ├─ Chunk content by tokens              │
│     ├─ Generate summaries per chunk         │
│     └─ Combine & re-summarize if needed     │
└─────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────┐
│  5. Knowledge Manager Agent                 │
│     └─ Store summary in database            │
└─────────────────────────────────────────────┘
      ↓
[Return Serialized Response]
      ↓
Client Response
```

---

## Agent Communication & Coordination

### 1. **Research Gathering Agent**

**Role**: Data Acquisition Specialist

**Responsibilities:**
- Query external data sources (SerpAPI, Wikipedia)
- Implement fallback mechanisms for resilience
- Return standardized document format

**Communication Protocol:**
```python
# Input from Orchestrator
query_text: str
max_sources: int

# Output to Orchestrator
[
  {
    "source": "Article Title",
    "url": "https://...",
    "content": "Article content..."
  },
  ...
]
```

**Key Features:**
- **Fault Tolerance**: Automatic fallback from SerpAPI to Wikipedia
- **Environment Management**: Dynamic API key loading
- **Error Handling**: Graceful degradation with empty results
- **Timeout Protection**: 20-25 second request timeouts

**Decision Logic:**
```
IF SerpAPI key exists:
    TRY SerpAPI search
    IF results empty OR error:
        FALLBACK to Wikipedia
ELSE:
    Use Wikipedia directly
```

---

### 2. **Summarization Agent**

**Role**: Content Processing & Synthesis

**Responsibilities:**
- Load and manage BART transformer model
- Chunk content based on tokenizer limits
- Generate multi-pass summaries for long content
- Adapt output length to user preferences

**Communication Protocol:**
```python
# Input from Orchestrator
docs: List[Dict]  # Documents from Research Agent
length: str       # "short" | "medium" | "long"

# Output to Orchestrator
summary_text: str  # Generated summary
```

**Processing Pipeline:**
1. **Content Extraction**: Combine all document content
2. **Token-based Chunking**: Split by model token limits (default ~1024 tokens)
3. **Chunk Summarization**: Process each chunk independently
4. **Summary Combination**: If multiple chunks, re-summarize combined output
5. **Output Optimization**: Apply beam search with length penalties

**Length Configuration:**
- `short`: 60-110 tokens (~50-100 words)
- `medium`: 120-180 tokens (~150-300 words)
- `long`: 200-260 tokens (~400-600 words)

**Optimization Strategies:**
- **Beam Search**: 3-4 beams for quality
- **N-gram Prevention**: No 3-gram repetition
- **Length Penalty**: Balanced at 1.0
- **Timeout Protection**: 15-25 seconds per chunk

---

### 3. **Knowledge Manager Agent**

**Role**: Data Persistence & Retrieval

**Responsibilities:**
- Store documents in relational database
- Persist summaries with metadata
- Maintain query history
- Link related entities (Query → Documents → Summaries)

**Communication Protocol:**
```python
# For document storage
store_documents(query_obj: Query, gathered_docs: List[Dict])

# For summary storage
store_summary(query_obj: Query, summary_text: str, summary_type: str)
```

**Data Model Relationships:**
```
Query (1) ──→ (Many) Documents
Query (1) ──→ (Many) Summaries

Each Query contains:
- query_text: Original user query
- created_at: Timestamp
- documents: Related source documents
- summaries: Generated summaries
```

**Storage Strategy:**
- **Atomic Operations**: Each storage operation is independent
- **Cascading Deletes**: Removing query removes all related data
- **Timestamp Tracking**: Auto-generated timestamps for audit trails

---

## Task Management & Workflow

### Synchronous Sequential Execution

The system uses **synchronous, blocking execution** where each agent completes before the next begins. This provides:

**Advantages:**
- ✅ **Deterministic Behavior**: Predictable execution order
- ✅ **Error Isolation**: Failures don't affect completed stages
- ✅ **Simplified Debugging**: Clear execution trace
- ✅ **State Consistency**: No race conditions

**Trade-offs:**
- ⚠️ **Blocking I/O**: Client waits for full pipeline (30-120 seconds)
- ⚠️ **Sequential Bottleneck**: No parallel processing

### Error Handling & Resilience

**Hierarchical Fallback Strategy:**
```
Level 1: API-level fallbacks
  └─ SerpAPI fails → Wikipedia fallback

Level 2: Component-level error handling
  └─ Each agent catches exceptions locally
  
Level 3: Orchestrator-level recovery
  └─ QueryView catches all errors → HTTP 500 with message
```

**Failure Recovery Examples:**

| Failure Point | Recovery Mechanism | User Impact |
|---------------|-------------------|-------------|
| SerpAPI timeout | Wikipedia fallback | Transparent - different sources |
| Tokenization error | Skip chunk, continue | Partial summary |
| Model inference timeout | Return partial results | Reduced quality |
| Database error | Transaction rollback | Error message to client |

### Data Flow & State Management

**Request Lifecycle:**
```
1. Client POST → Django View (Orchestrator)
   └─ State: Request validation

2. Create Query record in DB
   └─ State: Query ID assigned

3. Research Agent execution
   └─ State: In-memory document list
   
4. Store documents via Knowledge Manager
   └─ State: Documents persisted, IDs assigned

5. Summarization Agent execution
   └─ State: In-memory summary text

6. Store summary via Knowledge Manager
   └─ State: Summary persisted, ID assigned

7. Serialize complete Query object
   └─ State: Full response with all IDs

8. Return HTTP 201 Created
   └─ State: Client receives complete result
```

**State Persistence Points:**
- After Query creation (Step 2)
- After Document storage (Step 4)
- After Summary storage (Step 6)

This ensures partial results are saved even if later stages fail.

### Inter-Agent Communication

**Direct Function Calls:**
Agents communicate through simple Python function calls with standardized data structures:

```python
# Orchestrator in views.py
gathered = research_gathering.gather(q_text, max_sources=4)
# → Returns: List[Dict] with source, url, content

knowledge_manager.store_documents(q_obj, gathered)
# → Returns: None (side effect: DB writes)

summary_text = summarization.summarize_documents(gathered, length=summary_type)
# → Returns: str (summary text)

knowledge_manager.store_summary(q_obj, summary_text, summary_type)
# → Returns: None (side effect: DB writes)
```

**No Message Queue or Event Bus**: This simple architecture avoids complexity but limits:
- Asynchronous processing
- Distributed agent deployment
- Real-time progress updates

### Complete Orchestration Flow Example

Here's a complete trace of how a query flows through the system:

```
[CLIENT] POST /api/query/
Body: {"query_text": "AI in healthcare", "summary_type": "medium"}
    ↓
[ORCHESTRATOR - views.py:QueryView.post()]
├─ Validate request data
├─ Extract query_text = "AI in healthcare"
├─ Extract summary_type = "medium"
    ↓
[ORCHESTRATOR] Step 1: Create Query Record
├─ Execute: Query.objects.create(query_text="AI in healthcare")
├─ Result: Query object with ID=1
    ↓
[ORCHESTRATOR] Step 2: Call Research Agent
├─ Execute: research_gathering.gather("AI in healthcare", max_sources=4)
    ↓
    [RESEARCH AGENT - research_gathering.py]
    ├─ Load SERPAPI_KEY from environment
    ├─ IF key exists:
    │   ├─ HTTP GET to serpapi.com
    │   ├─ Parse organic_results
    │   └─ Return: [{"source": "...", "url": "...", "content": "..."}]
    ├─ ELSE fallback to Wikipedia:
    │   ├─ Search Wikipedia API
    │   ├─ Fetch article extracts
    │   └─ Return: [{"source": "...", "url": "...", "content": "..."}]
    ↓
├─ Result: 4 documents gathered
    ↓
[ORCHESTRATOR] Step 3: Store Documents
├─ Execute: knowledge_manager.store_documents(query_obj, gathered_docs)
    ↓
    [KNOWLEDGE MANAGER - knowledge_manager.py]
    ├─ FOR EACH document in gathered_docs:
    │   └─ Document.objects.create(query=query_obj, source=..., url=..., content=...)
    ↓
├─ Result: 4 Document records created (IDs 1-4)
    ↓
[ORCHESTRATOR] Step 4: Call Summarization Agent
├─ Execute: summarization.summarize_documents(gathered_docs, length="medium")
    ↓
    [SUMMARIZATION AGENT - summarization.py]
    ├─ Combine all document content → full_text
    ├─ Tokenize full_text → token count
    ├─ IF token_count > 1024:
    │   ├─ Chunk into segments (each ~1024 tokens)
    │   ├─ FOR EACH chunk:
    │   │   ├─ Call BART model with max_new_tokens=180
    │   │   └─ Collect chunk summary
    │   ├─ Combine chunk summaries
    │   └─ Re-summarize combined text (final pass)
    ├─ ELSE:
    │   └─ Single-pass BART summarization
    ↓
├─ Result: "AI is transforming healthcare through..."
    ↓
[ORCHESTRATOR] Step 5: Store Summary
├─ Execute: knowledge_manager.store_summary(query_obj, summary_text, "medium")
    ↓
    [KNOWLEDGE MANAGER - knowledge_manager.py]
    ├─ Summary.objects.create(query=query_obj, summary_text=..., summary_type="medium")
    ↓
├─ Result: Summary record created (ID=1)
    ↓
[ORCHESTRATOR] Step 6: Serialize Response
├─ Execute: QuerySerializer(query_obj).data
├─ Includes: query details, related documents, related summaries
    ↓
[ORCHESTRATOR] Return HTTP 201 Created
    ↓
[CLIENT] Receives:
{
  "id": 1,
  "query_text": "AI in healthcare",
  "created_at": "2025-11-20T20:08:00Z",
  "documents": [
    {"id": 1, "source": "...", "url": "...", "content": "..."},
    {"id": 2, "source": "...", "url": "...", "content": "..."},
    {"id": 3, "source": "...", "url": "...", "content": "..."},
    {"id": 4, "source": "...", "url": "...", "content": "..."}
  ],
  "summaries": [
    {
      "id": 1,
      "summary_text": "AI is transforming healthcare...",
      "summary_type": "medium",
      "created_at": "2025-11-20T20:09:15Z"
    }
  ]
}
```

**Total Duration**: ~30-120 seconds depending on:
- SerpAPI response time (2-5 seconds)
- Document size and number of chunks (affects summarization)
- Model load state (cached vs. first run)
- Summary length setting

---

## Prerequisites

Before installing the Multiagent Research Assistant, ensure you have the following:

### Required Software
- **Python 3.10 or higher** - [Download Python](https://www.python.org/downloads/)
  - Verify installation: `python --version`
- **pip** (Python package manager) - Usually comes with Python
  - Verify installation: `pip --version`
- **Git** - [Download Git](https://git-scm.com/downloads)
  - Verify installation: `git --version`

### Optional (for Frontend)
- **Node.js 18+ and npm** - [Download Node.js](https://nodejs.org/)
  - Verify installation: `node --version` and `npm --version`

### API Keys
- **SerpAPI Key** (Required for web search functionality)
  1. Visit [SerpAPI](https://serpapi.com/)
  2. Sign up for a free account (100 searches/month free)
  3. Navigate to your [API Key page](https://serpapi.com/manage-api-key)
  4. Copy your API key for later use

### System Requirements
- **Storage**: At least 2GB free space (for model weights)
- **Memory**: 4GB RAM minimum (8GB recommended for better performance)
- **Internet**: Required for initial model downloads and API calls

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kipash-prog/multiagent-research-assistant
cd multiagent-research-assistant
```

### 2. Backend Setup

#### Step 1: Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt indicating the virtual environment is active.

#### Step 2: Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

This will install:
- Django 4.2+
- Django REST Framework
- Django CORS Headers
- Requests
- Python-dotenv
- LangChain
- NLTK
- Transformers
- PyTorch

**Note**: First installation may take several minutes, especially for PyTorch.

#### Step 3: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   # Windows
   copy backend\.env.example backend\.env
   
   # macOS/Linux
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` and add your SerpAPI key:
   ```env
   SERPAPI_KEY=your_actual_serpapi_key_here
   ```

3. **Important**: Also create the same file in `backend/backend/.env`:
   ```bash
   # Windows
   copy backend\.env.example backend\backend\.env
   
   # macOS/Linux
   cp backend/.env.example backend/backend/.env
   ```

#### Step 4: Initialize Database

```bash
python backend/manage.py migrate
```

This creates the SQLite database and necessary tables.

#### Step 5: (Optional) Create Admin User

To access Django admin panel:
```bash
python backend/manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 3. Frontend Setup (Optional)

If you want to use the React web interface:

#### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

#### Step 2: Install Node Dependencies

```bash
npm install
```

This installs all required packages including React, React DOM, and testing libraries.

#### Step 3: Configure API Endpoint (if needed)

If your backend runs on a different port or host, update the API base URL in your frontend configuration.

---

## Configuration

### Backend Configuration

**Environment Variables** (`backend/.env` and `backend/backend/.env`):
```env
SERPAPI_KEY=your_serpapi_key_here
```

**Summary Types**:
The system supports three summary lengths:
- `short`: Brief overview (~50-100 words)
- `medium`: Balanced summary (~150-300 words)
- `long`: Detailed summary (~400-600 words)

**Model Configuration**:
- Default model: `facebook/bart-large-cnn`
- Alternative (faster): `sshleifer/distilbart-cnn-12-6`
- Edit `core/agents/summarization.py` to change models

### Frontend Configuration

**API Base URL**: By default, the frontend expects the backend at `http://127.0.0.1:8000/`

---

## Usage

### Starting the Application

#### Start Backend Server

1. Ensure virtual environment is activated:
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

2. Start the Django development server:
   ```bash
   python backend/manage.py runserver
   ```

3. The API will be available at: **http://127.0.0.1:8000/**

You should see output like:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

#### Start Frontend (Optional)

In a **new terminal window**:

```bash
cd frontend
npm start
```

The React app will open automatically at: **http://localhost:3000/**

### API Endpoints

The backend provides the following RESTful endpoints:

#### 1. **POST** `/api/query/` - Submit a Research Query

Submit a new research query to gather sources and generate a summary.

**Request Body:**
```json
{
  "query_text": "AI in healthcare",
  "summary_type": "medium"
}
```

**Parameters:**
- `query_text` (string, required): The research topic or question
- `summary_type` (string, required): Summary length - one of: `short`, `medium`, or `long`

**Behavior:**
1. Gathers up to 4 sources via SerpAPI (falls back to Wikipedia on error/empty results)
2. Combines and processes the content
3. Generates a summary using BART
4. Persists the query, documents, and summary to database

**Response:** Returns the serialized Query record with linked documents and summary IDs.

**Example Response:**
```json
{
  "id": 1,
  "query_text": "AI in healthcare",
  "summary_type": "medium",
  "created_at": "2025-11-20T20:08:00Z",
  "documents": [
    {"id": 1, "title": "...", "url": "...", "content": "..."},
    {"id": 2, "title": "...", "url": "...", "content": "..."}
  ],
  "summary": {
    "id": 1,
    "summary_text": "AI is transforming healthcare..."
  }
}
```

#### 2. **GET** `/api/queries/` - List All Queries

Retrieve a list of all research queries.

**Response:** Array of query objects with summaries and documents.

#### 3. **GET** `/api/queries/<id>/` - Get Specific Query

Retrieve details of a specific query by ID.

**Parameters:**
- `id` (integer): Query ID

**Response:** Single query object with full details.

---

### Using the Frontend

If you're running the React frontend:

1. **Navigate to** http://localhost:3000/
2. **Enter your research query** in the search box
3. **Select summary length**: short, medium, or long
4. **Click "Search"** to submit your query
5. **View results**: The app will display sources and the generated summary
6. **Browse history**: Access previous queries from the sidebar

---

## API Examples

### Example 1: Research Query via cURL

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/query/" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"query_text":"Climate change effects","summary_type":"medium"}'
```

**macOS/Linux:**
```bash
curl -X POST http://127.0.0.1:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"query_text":"Climate change effects","summary_type":"medium"}'
```

### Example 2: List Queries via cURL

```bash
curl http://127.0.0.1:8000/api/queries/
```

### Example 3: Python Script

```python
import requests

# Submit a query
response = requests.post(
    "http://127.0.0.1:8000/api/query/",
    json={
        "query_text": "Machine learning applications",
        "summary_type": "long"
    }
)

result = response.json()
print(f"Query ID: {result['id']}")
print(f"Summary: {result['summary']['summary_text']}")

# Get all queries
queries = requests.get("http://127.0.0.1:8000/api/queries/").json()
print(f"Total queries: {len(queries)}")
```

### Example 4: JavaScript Fetch

```javascript
// Submit a query
fetch('http://127.0.0.1:8000/api/query/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query_text: 'Quantum computing basics',
    summary_type: 'short'
  })
})
.then(response => response.json())
.then(data => {
  console.log('Query ID:', data.id);
  console.log('Summary:', data.summary.summary_text);
})
.catch(error => console.error('Error:', error));
```

---

## Important Notes

### First Run Behavior
- **Model Download**: On first execution, the system will download BART model weights (approximately 1-2GB)
- **Download Time**: May take 5-30 minutes depending on your internet speed
- **Caching**: Subsequent runs will use the cached model for instant startup

### API Limits
- **SerpAPI**: Free tier provides 100 searches/month
- **Fallback**: System automatically uses Wikipedia when SerpAPI quota is exhausted
- **Rate Limiting**: Be mindful of API rate limits when making multiple requests

### Performance Considerations
- **Inference Speed**: First query may take 30-60 seconds as models load into memory
- **Faster Alternative**: Edit `core/agents/summarization.py` to use `sshleifer/distilbart-cnn-12-6` for faster (but slightly less accurate) summaries
- **Memory Usage**: Expect 2-4GB RAM usage when models are loaded

## Troubleshooting

### Installation Issues

#### **Problem**: `pip install` fails with dependency conflicts
**Solution:**
- Upgrade pip: `python -m pip install --upgrade pip`
- Try installing in a fresh virtual environment
- On Windows, you may need Microsoft C++ Build Tools for some packages

#### **Problem**: PyTorch installation fails or takes too long
**Solution:**
- Install PyTorch separately first: `pip install torch`
- For CPU-only version (smaller, faster): `pip install torch --index-url https://download.pytorch.org/whl/cpu`

#### **Problem**: Virtual environment not activating
**Solution:**
- **Windows**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell
- **macOS/Linux**: Ensure you used `source` command, not `sh`

### Runtime Issues

#### **Problem**: "No module named 'dotenv'" or similar import errors
**Solution:**
- Ensure virtual environment is activated (you should see `(.venv)` in terminal)
- Reinstall requirements: `pip install -r backend/requirements.txt`

#### **Problem**: Database migration errors
**Solution:**
```bash
# Delete existing database and migrations
rm backend/db.sqlite3
find backend -path "*/migrations/*.py" -not -name "__init__.py" -delete
find backend -path "*/migrations/*.pyc" -delete

# Recreate migrations
python backend/manage.py makemigrations
python backend/manage.py migrate
```

#### **Problem**: SerpAPI key not recognized
**Solution:**
- Verify `.env` file exists in both `backend/.env` AND `backend/backend/.env`
- Check for typos in key name: must be exactly `SERPAPI_KEY`
- Ensure no quotes around the key value in `.env` file
- Restart the Django server after changing `.env`

#### **Problem**: "Address already in use" error
**Solution:**
- Another process is using port 8000
- **Kill existing process:**
  - **Windows**: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`
  - **macOS/Linux**: `lsof -ti:8000 | xargs kill -9`
- **Or use different port**: `python backend/manage.py runserver 8080`

### API Issues

#### **Problem**: Summaries are cut short or timeout
**Solution:**
- Reduce `summary_type` from `long` to `medium` or `short`
- Edit `core/agents/summarization.py` to adjust `max_length` parameter
- Switch to faster model: `sshleifer/distilbart-cnn-12-6`

#### **Problem**: No research results returned
**Solution:**
- Verify SerpAPI key is valid: test at https://serpapi.com/account
- Check your SerpAPI quota hasn't been exhausted
- Wikipedia fallback should still provide basic content
- Check Django console for error messages

#### **Problem**: Model download fails
**Solution:**
- Ensure stable internet connection
- Check firewall isn't blocking Hugging Face downloads
- Manually set cache directory:
  ```bash
  # Windows
  set HF_HOME=C:\path\to\cache
  
  # macOS/Linux
  export HF_HOME=/path/to/cache
  ```
- Download model manually from https://huggingface.co/facebook/bart-large-cnn

#### **Problem**: CORS errors in frontend
**Solution:**
- Verify `django-cors-headers` is installed
- Check CORS settings in `backend/backend/settings.py`
- Ensure backend server is running on expected port

### Performance Issues

#### **Problem**: First query takes very long (>2 minutes)
**Solution:**
- This is normal on first run (model loading + download)
- Subsequent queries should be much faster (30-60 seconds)
- For faster performance, use the distilBART model variant

#### **Problem**: High memory usage
**Solution:**
- Normal: BART models require 2-4GB RAM
- Close other applications if system is struggling
- Consider using distilBART variant for lower memory footprint

---

## Development

### Contributing
- **Code Style**: Follow existing patterns; keep agents modular
- **Tests**: Add Django tests under `backend/core/tests/`
- **Secrets**: Never commit `.env` files or API keys
- **Documentation**: Update README when adding features

### Running Tests
```bash
python backend/manage.py test
```

### Project Structure
```
multiagent-research-assistant/
├── backend/
│   ├── backend/          # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── .env         # Environment variables
│   ├── core/            # Main application
│   │   ├── agents/      # Modular agent implementations
│   │   │   ├── research_gathering.py
│   │   │   ├── summarization.py
│   │   │   └── knowledge_manager.py
│   │   ├── models.py    # Database models
│   │   ├── views.py     # API endpoints
│   │   └── tests/       # Test suite
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/            # React application
│   ├── src/
│   ├── public/
│   └── package.json
└── readme.md
```

### Adding New Features

**To add a new agent:**
1. Create file in `backend/core/agents/`
2. Implement agent class with clear interface
3. Update `views.py` to integrate agent
4. Add tests in `backend/core/tests/`

**To modify summarization:**
- Edit `backend/core/agents/summarization.py`
- Change model, parameters, or chunking strategy
- Test with various query lengths

**To add new endpoints:**
1. Define route in `backend/core/urls.py`
2. Implement view in `backend/core/views.py`
3. Update this README with API documentation

### Future Enhancements: Async Orchestration

The current synchronous orchestration can be enhanced for production systems:

#### **Option 1: Celery Task Queue**
Convert the pipeline to asynchronous tasks:

```python
# Pseudo-code for Celery implementation
@shared_task
def process_query_async(query_id):
    q_obj = Query.objects.get(id=query_id)
    
    # Chain tasks
    chain(
        research_task.s(q_obj.query_text),
        store_documents_task.s(q_obj.id),
        summarize_task.s(),
        store_summary_task.s(q_obj.id)
    ).apply_async()
```

**Benefits:**
- Non-blocking API responses
- Progress tracking via task states
- Retry mechanisms for failed stages
- Distributed processing across workers

**Requirements:**
- Redis or RabbitMQ message broker
- Celery worker processes
- WebSocket or polling for status updates

#### **Option 2: Django Channels + WebSockets**
Real-time progress updates:

```python
# Stream progress to client
async def query_consumer(websocket):
    await websocket.send({"status": "researching"})
    # ... research agent
    await websocket.send({"status": "summarizing"})
    # ... summarization
    await websocket.send({"status": "complete", "result": data})
```

**Benefits:**
- Live progress updates
- Better user experience
- Partial result streaming

#### **Option 3: LangChain Agent Orchestration**
Leverage LangChain's agent framework:

```python
from langchain.agents import AgentExecutor, Tool

tools = [
    Tool(name="Research", func=research_gathering.gather),
    Tool(name="Summarize", func=summarization.summarize_documents),
]

agent = AgentExecutor.from_agent_and_tools(
    agent=ZeroShotAgent(...),
    tools=tools
)
```

**Benefits:**
- Advanced agent reasoning
- Dynamic tool selection
- Built-in memory and state

**Trade-offs:**
- More complex architecture
- Harder to debug
- Less deterministic behavior

### Monitoring & Observability

For production deployments, consider adding:

**Logging:**
```python
import structlog

logger = structlog.get_logger()
logger.info("research_started", query_id=q_obj.id, source="serpapi")
```

**Metrics:**
- Request duration per agent
- Success/failure rates
- API quota usage (SerpAPI)
- Model inference time

**Tools:**
- Prometheus + Grafana for metrics
- Sentry for error tracking
- ELK stack for log aggregation

---

## FAQ

**Q: Why not use LangChain for orchestration?**
A: The current implementation prioritizes simplicity and transparency. LangChain adds complexity that's unnecessary for this linear pipeline, but it's a great option for more dynamic, reasoning-based workflows. See "Future Enhancements" for integration ideas.

**Q: Can agents run in parallel?**
A: Not currently. The sequential design ensures data dependencies are met (e.g., documents must be fetched before summarization). Future async implementations could parallelize independent operations.

**Q: How do I add a new agent to the pipeline?**
A: 
1. Create agent file in `backend/core/agents/` with a function that takes input and returns output
2. Import in `views.py`
3. Call it in sequence within `QueryView.post()`
4. Update data flow documentation

**Q: Can agents communicate with each other directly?**
A: No, all communication flows through the orchestrator (`QueryView`). This centralized pattern simplifies debugging and ensures predictable execution order.

**Q: Can I use this without a SerpAPI key?**
A: Yes, but only Wikipedia will be used as a source. For web search, SerpAPI is required.

**Q: How much does SerpAPI cost?**
A: Free tier includes 100 searches/month. Paid plans start at $50/month for 5,000 searches.

**Q: Can I deploy this to production?**
A: Yes, but you'll need to:
- Use a production database (PostgreSQL recommended)
- Set `DEBUG=False` in Django settings
- Configure proper static file serving
- Use a production WSGI server (gunicorn, uwsgi)
- Set up HTTPS and proper security headers
- Consider async orchestration (Celery) for better scalability

**Q: Can I use a different summarization model?**
A: Yes! Edit `core/agents/summarization.py` and change the model name. Any Hugging Face summarization model should work.

**Q: How do I clear the database?**
A: Delete `backend/db.sqlite3` and run `python backend/manage.py migrate` again.

**Q: Is GPU required?**
A: No, but it will significantly speed up summarization. PyTorch will automatically use GPU if available.

---

## License

MIT License
---

## Support & Contact

For issues, questions, or contributions:
- **Issues**: Open an issue on GitHub
- **Documentation**: Refer to this README
- **Code**: Follow existing patterns and add tests

---

## Acknowledgments

- **SerpAPI** for web search functionality
- **Hugging Face** for transformer models
- **Django** and **React** communities
