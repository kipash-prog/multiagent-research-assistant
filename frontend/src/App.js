import React, { useEffect, useState } from "react";
import "./styles.css";
import QueryForm from "./components/QueryForm";
import Results from "./components/Results";
import History from "./components/History";
import { listQueries, getQuery } from "./api";

function App(){
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);

  async function refreshHistory(){
    try {
      const items = await listQueries();
      setHistory(items || []);
    } catch (e) {}
  }

  useEffect(() => {
    refreshHistory();
  }, []);

  async function handleSelect(id){
    try {
      const data = await getQuery(id);
      setResult(data);
    } catch (e) {}
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>Recent</h2>
        <History items={history} onSelect={handleSelect} />
      </aside>
      <main className="main">
        <div className="header">
          <h1 className="title">Multi‑Agent Research Assistant</h1>
          <span className="badge">v0.1</span>
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <QueryForm onResult={(data) => { setResult(data); refreshHistory(); }} />
        </div>

        <div className="card">
          <Results data={result} />
        </div>
      </main>
    </div>
  );
}

export default App;
