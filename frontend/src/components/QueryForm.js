import React, { useState } from "react";
import { createQuery } from "../api";
import Loader from "./Loader";

export default function QueryForm({ onResult }) {
  const [query, setQuery] = useState("");
  const [summaryType, setSummaryType] = useState("medium");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await createQuery(query, summaryType);
      onResult(data);
      setQuery("");
    } catch (err) {
      console.error(err);
      alert("Error sending query. Check backend.");
    } finally {
      setLoading(false);
    }
  }

  const chars = query.length;
  return (
    <form onSubmit={submit} className="form-row">
      <div>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your research query (e.g., AI in healthcare 2024)"
          rows={6}
          aria-label="Research query"
        />
        <div className="muted" style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
          <span>Describe what you want to research.</span>
          <span>{chars} chars</span>
        </div>
      </div>
      <div className="controls">
        <label>
          <span className="muted">Summary length</span>
          <select className="select" value={summaryType} onChange={(e) => setSummaryType(e.target.value)} aria-label="Summary length">
            <option value="short">Short</option>
            <option value="medium">Medium</option>
            <option value="long">Long</option>
          </select>
        </label>
        <button className="button" type="submit" disabled={loading || !query.trim()}>
          {loading ? <Loader label="Researching" /> : "Research"}
        </button>
        <button className="button secondary" type="button" onClick={() => setQuery("")} disabled={loading || !query}>
          Clear
        </button>
      </div>
    </form>
  );
}
