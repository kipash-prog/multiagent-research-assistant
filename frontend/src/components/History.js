import React from "react";

export default function History({ items = [], onSelect }) {
  return (
    <div className="history">
      {items.length === 0 ? (
        <div className="muted">No recent queries</div>
      ) : (
        items.map((q) => (
          <div key={q.id} className="history-item" onClick={() => onSelect?.(q.id)}>
            <div style={{ fontWeight: 600 }}>{(q.query_text || "").slice(0, 60) || "(empty)"}</div>
            <small>{new Date(q.created_at).toLocaleString()}</small>
          </div>
        ))
      )}
    </div>
  );
}
