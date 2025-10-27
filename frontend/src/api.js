const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

export async function createQuery(queryText, summaryType = "medium") {
  const resp = await fetch(`${API_BASE}/query/`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ query_text: queryText, summary_type: summaryType }),
  });
  return resp.json();
}

export async function listQueries() {
  const resp = await fetch(`${API_BASE}/query/list/`);
  return resp.json();
}

export async function getQuery(id) {
  const resp = await fetch(`${API_BASE}/query/${id}/`);
  return resp.json();
}
