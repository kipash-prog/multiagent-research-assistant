import os
import requests
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from django.conf import settings

def _load_tavily_env():
    tried = []
    fd = find_dotenv()
    if fd:
        tried.append(fd)
        load_dotenv(fd, override=True)
    here = Path(__file__).resolve()
    backend_root = here.parents[2]
    # Resolve via Django BASE_DIR as well (BASE_DIR points to .../backend)
    base_dir = Path(getattr(settings, 'BASE_DIR', backend_root))
    candidate_paths = [
        backend_root / 'backend' / '.env',
        backend_root / '.env',
        here.parents[1] / '.env',
        here.parents[0] / '.env',
        base_dir / '.env',
        base_dir / 'backend' / '.env',
    ]
    for p in candidate_paths:
        tried.append(str(p))
        if p.exists():
            load_dotenv(p, override=True)
    key = os.getenv('TAVILY_API_KEY')
    if not key:
        print('[ResearchGatheringAgent] TAVILY_API_KEY not found. Tried: ' + ' | '.join(tried))
    return key

def _tavily_enabled():
    # Default True; allow disabling via env
    val = os.getenv('TAVILY_ENABLED')
    if val is None:
        return True
    return str(val).strip().lower() not in ("0", "false", "no")

def gather(query_text: str, max_sources: int = 5):
    url = "https://api.tavily.com/search"
    key = _load_tavily_env()
    if not _tavily_enabled():
        # Explicitly disabled: use fallback only
        fb = _fallback_wikipedia(query_text, max_sources=max_sources)
        if fb:
            print("[ResearchGatheringAgent] Tavily disabled; using Wikipedia fallback results.")
        else:
            print("[ResearchGatheringAgent] Wikipedia fallback returned 0 documents.")
        return fb
    if not (key and key.strip()):
        print("[ResearchGatheringAgent] Missing TAVILY_API_KEY; trying Wikipedia fallback.")
        return _fallback_wikipedia(query_text, max_sources=max_sources)
    variants = [
        ({
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }, {
            "query": query_text,
            "search_depth": "advanced",
            "include_images": False,
            "include_answers": True,
        }),
        ({
            "x-api-key": key,
            "Content-Type": "application/json",
        }, {
            "api_key": key,
            "query": query_text,
            "search_depth": "advanced",
            "include_images": False,
            "include_answers": True,
        }),
        ({
            "X-Tavily-API-Key": key,
            "Content-Type": "application/json",
        }, {
            "query": query_text,
            "search_depth": "advanced",
            "include_images": False,
            "include_answers": True,
        }),
        ({
            "Content-Type": "application/json",
        }, {
            "api_key": key,
            "query": query_text,
            "search_depth": "advanced",
            "include_images": False,
            "include_answers": True,
        }),
    ]

    def _try_request(hdrs, body):
        try:
            res = requests.post(url, headers=hdrs, json=body, timeout=25)
        except Exception as e:
            print(f"[ResearchGatheringAgent] Request error with headers {list(hdrs.keys())}: {e}")
            return None
        if res.status_code != 200:
            print(f"[ResearchGatheringAgent] Tavily HTTP {res.status_code} with headers {list(hdrs.keys())}: {res.text[:200]}")
            return None
        try:
            return res.json()
        except Exception:
            print(f"[ResearchGatheringAgent] Non-JSON response with headers {list(hdrs.keys())}: {res.text[:200]}")
            return None

    data = None
    for hdrs, body in variants:
        data = _try_request(hdrs, body)
        if data is not None:
            break
    if data is None:
        # Fallback: try Wikipedia to provide useful docs without external API key
        try:
            wiki_docs = _fallback_wikipedia(query_text, max_sources=max_sources)
            if wiki_docs:
                print("[ResearchGatheringAgent] Using Wikipedia fallback results.")
                return wiki_docs
            else:
                print("[ResearchGatheringAgent] Wikipedia fallback returned 0 documents.")
        except Exception as _:
            print("[ResearchGatheringAgent] Wikipedia fallback failed due to an exception.")
        return []

    results = data.get("results", [])
    if not results:
        # If Tavily returns 200 but with no results, try fallback
        try:
            wiki_docs = _fallback_wikipedia(query_text, max_sources=max_sources)
            if wiki_docs:
                print("[ResearchGatheringAgent] Tavily returned no results; using Wikipedia fallback.")
                return wiki_docs
            else:
                print("[ResearchGatheringAgent] Wikipedia fallback returned 0 documents.")
        except Exception:
            print("[ResearchGatheringAgent] Wikipedia fallback failed due to an exception.")
    documents = []
    for r in results[:max_sources]:
        documents.append({
            "source": r.get("title", "Unknown"),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        })
    return documents

def _fallback_wikipedia(query_text: str, max_sources: int = 5):
   
    try:
        headers = {
            "User-Agent": "MultiAgentResearchAssistant/0.1 (contact@example.com)",
        }
        search_resp = requests.get(
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
        if search_resp.status_code != 200:
            return []
        search_data = search_resp.json()
        search_results = search_data.get("query", {}).get("search", [])
        # If normal search is empty, try opensearch as a fallback (handles typos better)
        if not search_results:
            os_resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": query_text,
                    "limit": max_sources,
                    "namespace": 0,
                    "format": "json",
                },
                timeout=20,
                headers=headers,
            )
            if os_resp.status_code == 200:
                os_data = os_resp.json()
                # os_data format: [query, titles[], descriptions[], urls[]]
                titles = os_data[1] if isinstance(os_data, list) and len(os_data) > 1 else []
                if titles:
                    # Build docs using REST summaries
                    docs = []
                    for t in titles[:max_sources]:
                        sum_resp = requests.get(
                            f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(t)}",
                            timeout=20,
                            headers=headers,
                        )
                        if sum_resp.status_code == 200:
                            sd = sum_resp.json()
                            title = sd.get("title", t)
                            extract = sd.get("extract") or sd.get("description") or ""
                            url = sd.get("content_urls", {}).get("desktop", {}).get("page") or sd.get("url") or ""
                            if extract:
                                docs.append({"source": title, "url": url, "content": extract})
                    if docs:
                        return docs
            # Extra fallback: REST search/title (new API)
            rest_search = requests.get(
                "https://en.wikipedia.org/w/rest.php/v1/search/title",
                params={
                    "q": query_text,
                    "limit": max_sources,
                },
                timeout=20,
                headers=headers,
            )
            if rest_search.status_code == 200:
                rs = rest_search.json()
                items = rs.get("pages") or rs.get("results") or []
                docs = []
                for it in items[:max_sources]:
                    title = it.get("title") or it.get("key")
                    if not title:
                        continue
                    sum_resp = requests.get(
                        f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}",
                        timeout=20,
                        headers=headers,
                    )
                    if sum_resp.status_code == 200:
                        sd = sum_resp.json()
                        t = sd.get("title", title)
                        extract = sd.get("extract") or sd.get("description") or ""
                        url = sd.get("content_urls", {}).get("desktop", {}).get("page") or sd.get("url") or ""
                        if extract:
                            docs.append({"source": t, "url": url, "content": extract})
                if docs:
                    return docs
            # If opensearch also fails to find anything
            return []
        page_ids = [str(item.get("pageid")) for item in search_results[:max_sources] if item.get("pageid")]
        if not page_ids:
            return []

        extract_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "format": "json",
                "pageids": "|".join(page_ids),
            },
            timeout=20,
            headers=headers,
        )
        if extract_resp.status_code != 200:
            return []
        extract_data = extract_resp.json()
        pages = extract_data.get("query", {}).get("pages", {})

        docs = []
        for pid in page_ids:
            page = pages.get(pid)
            if not page:
                continue
            title = page.get("title", "Wikipedia")
            extract = page.get("extract", "")
            url = f"https://en.wikipedia.org/?curid={pid}"
            if extract:
                docs.append({
                    "source": title,
                    "url": url,
                    "content": extract,
                })
        return docs
    except Exception:
        return []
