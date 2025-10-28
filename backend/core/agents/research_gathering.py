import os
import requests
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from django.conf import settings


def _load_serpapi_env():
    """
    Load SERPAPI_KEY from .env files located in backend or base directories.
    """
    tried = []
    fd = find_dotenv()
    if fd:
        tried.append(fd)
        load_dotenv(fd, override=True)

    here = Path(__file__).resolve()
    backend_root = here.parents[2]
    base_dir = Path(getattr(settings, "BASE_DIR", backend_root))

    candidate_paths = [
        backend_root / ".env",
        backend_root / "backend" / ".env",
        here.parents[1] / ".env",
        here.parents[0] / ".env",
        base_dir / ".env",
        base_dir / "backend" / ".env",
    ]

    for p in candidate_paths:
        tried.append(str(p))
        if p.exists():
            load_dotenv(p, override=True)

    key = os.getenv("SERPAPI_KEY")
    if not key:
        print("[ResearchGatheringAgent] ❌ SERPAPI_KEY not found. Tried:", " | ".join(tried))
    return key

# -------------------------------
# 2️⃣ SerpAPI Search Request
# -------------------------------
def gather(query_text: str, max_sources: int = 5):
    """
    Query SerpAPI to gather research data based on a query.
    Falls back to Wikipedia if SerpAPI is unavailable.
    """
    key = _load_serpapi_env()
    if not key:
        print("[ResearchGatheringAgent] ⚠️ Missing SerpAPI key. Using Wikipedia fallback.")
        return _fallback_wikipedia(query_text, max_sources=max_sources)

    url = "https://serpapi.com/search.json"
    params = {
        "q": query_text,
        "hl": "en",
        "num": max_sources,
        "api_key": key
    }

    try:
        res = requests.get(url, params=params, timeout=25)
        res.raise_for_status()
        data = res.json()
        results = data.get("organic_results", [])

        if not results:
            print("[ResearchGatheringAgent] ⚠️ SerpAPI returned no results. Using fallback.")
            return _fallback_wikipedia(query_text, max_sources=max_sources)

        print(f"[ResearchGatheringAgent] ✅ Retrieved {len(results)} results from SerpAPI.")
        documents = [
            {
                "source": r.get("title", "Unknown"),
                "url": r.get("link", ""),
                "content": r.get("snippet", "")
            }
            for r in results[:max_sources]
        ]
        return documents

    except requests.exceptions.RequestException as e:
        print(f"[ResearchGatheringAgent] ❌ SerpAPI request failed: {e}")
        return _fallback_wikipedia(query_text, max_sources=max_sources)


def _fallback_wikipedia(query_text: str, max_sources: int = 5):
    """
    Fetches fallback results from Wikipedia if SerpAPI is unavailable.
    """
    try:
        headers = {"User-Agent": "ResearchGatheringAgent/1.0"}
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query_text,
                "utf8": 1,
                "format": "json",
                "srlimit": max_sources,
            },
            timeout=20,
            headers=headers,
        )

        if resp.status_code != 200:
            return []

        search_results = resp.json().get("query", {}).get("search", [])
        docs = []

        for item in search_results[:max_sources]:
            title = item.get("title")
            page_id = item.get("pageid")
            if not (title and page_id):
                continue
            page_url = f"https://en.wikipedia.org/?curid={page_id}"
            extract_resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "prop": "extracts",
                    "explaintext": 1,
                    "format": "json",
                    "pageids": page_id,
                },
                timeout=20,
                headers=headers,
            )
            if extract_resp.status_code == 200:
                page_data = extract_resp.json()
                extract = (
                    page_data.get("query", {})
                    .get("pages", {})
                    .get(str(page_id), {})
                    .get("extract", "")
                )
                docs.append({"source": title, "url": page_url, "content": extract})
        print(f"[ResearchGatheringAgent] 🟡 Wikipedia fallback returned {len(docs)} documents.")
        return docs
    except Exception as e:
        print("[ResearchGatheringAgent] ❌ Wikipedia fallback failed:", e)
        return []
