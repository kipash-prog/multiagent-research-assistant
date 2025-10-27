import React from "react";

export default function Results({ data }) {
  if (!data) return <div className="muted">No results yet. Submit a query to see results.</div>;
  const { id, query_text, created_at, documents = [], summaries = [] } = data;

  function copy(text){
    if (!text) return;
    navigator.clipboard?.writeText(text);
  }

  return (
    <div>
      <div style={{ marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>Result for: <em>{query_text}</em></h3>
        <p className="muted"><small>Query ID: {id} • {new Date(created_at).toLocaleString()}</small></p>
      </div>

      <section className="section">
        <h4>Summary</h4>
        {summaries.length === 0 ? (
          <div className="muted">No summary available.</div>
        ) : (
          summaries.map(s => (
            <div key={s.id} className="summary" style={{ padding: 8, marginBottom: 8 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <p style={{ margin: 0 }}><strong>{s.summary_type}</strong> • {new Date(s.created_at).toLocaleString()}</p>
                <button className="button secondary" type="button" onClick={() => copy(s.summary_text)}>Copy</button>
              </div>
              <p style={{ whiteSpace: "pre-wrap" }}>{s.summary_text}</p>
            </div>
          ))
        )}
      </section>

      <section className="section">
        <h4>Documents <span className="badge">{documents.length}</span></h4>
        {documents.length === 0 ? (
          <div className="muted">No documents found.</div>
        ) : (
          documents.map(d => (
            <div key={d.id} className="doc">
              <p style={{ marginBottom: 6 }}>
                <a href={d.url} target="_blank" rel="noreferrer">{d.source || d.url}</a>
              </p>
              <p style={{ whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto" }}>{d.content}</p>
            </div>
          ))
        )}
      </section>
    </div>
  );
}
