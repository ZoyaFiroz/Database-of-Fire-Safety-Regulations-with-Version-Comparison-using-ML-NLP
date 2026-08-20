import { useEffect, useMemo, useState } from "react";
import Controls from "./components/Controls";
import StatsGrid from "./components/StatsGrid";
import FilterBar from "./components/FilterBar";
import ClauseCard from "./components/ClauseCard";
import { listDocuments, listVersions, compareVersions } from "./lib/api";
import "./App.css";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [versions, setVersions] = useState([]);
  const [oldVersionId, setOldVersionId] = useState(null);
  const [newVersionId, setNewVersionId] = useState(null);
  const [method, setMethod] = useState("baseline");

  const [compareData, setCompareData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [activeFilter, setActiveFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  // Load the document list once.
  useEffect(() => {
    const controller = new AbortController();
    listDocuments(controller.signal)
      .then((docs) => {
        setDocuments(docs);
        if (docs.length > 0) setSelectedDocId(docs[0].id);
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(`Failed to load documents: ${err.message}`);
      });
    return () => controller.abort();
  }, []);

  // Load versions whenever the selected document changes.
  useEffect(() => {
    if (selectedDocId == null) return;
    setOldVersionId(null);
    setNewVersionId(null);
    const controller = new AbortController();
    listVersions(selectedDocId, controller.signal)
      .then((vs) => {
        setVersions(vs);
        if (vs.length >= 2) {
          setOldVersionId(vs[0].id);
          setNewVersionId(vs[1].id);
        }
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(`Failed to load versions: ${err.message}`);
      });
    return () => controller.abort();
  }, [selectedDocId]);

  // Run the comparison whenever version pair or method changes. Aborting the
  // previous request on rapid changes avoids an older, slower request (e.g.
  // an in-flight SBERT run) overwriting a newer selection's result.
  useEffect(() => {
    if (oldVersionId == null || newVersionId == null) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    compareVersions(oldVersionId, newVersionId, method, controller.signal)
      .then((data) => {
        setCompareData(data);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          setError(`Comparison failed: ${err.message}`);
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [oldVersionId, newVersionId, method]);

  const filteredResults = useMemo(() => {
    if (!compareData?.changes) return [];
    const term = searchTerm.toLowerCase().trim();
    return compareData.changes.filter((r) => {
      if (activeFilter !== "all" && r.change_type !== activeFilter) return false;
      if (term) {
        const clauseNum = (r.old_clause_number || r.new_clause_number || "").toLowerCase();
        const text = ((r.old_text || "") + (r.new_text || "")).toLowerCase();
        return clauseNum.includes(term) || text.includes(term);
      }
      return true;
    });
  }, [compareData, activeFilter, searchTerm]);

  return (
    <>
      <header>
        <div className="brand">
          <div className="brand-icon">ADB</div>
          <div className="brand-title">Approved Document B — Multi-Version Comparison Engine</div>
        </div>
        <div className="badge-stage">Stage 3 Semantic (SBERT + difflib)</div>
      </header>

      <div className="container">
        <Controls
          documents={documents}
          selectedDocId={selectedDocId}
          onDocChange={setSelectedDocId}
          versions={versions}
          oldVersionId={oldVersionId}
          newVersionId={newVersionId}
          onOldVersionChange={setOldVersionId}
          onNewVersionChange={setNewVersionId}
          method={method}
          onMethodChange={setMethod}
          onPreset={(oldId, newId) => {
            setOldVersionId(oldId);
            setNewVersionId(newId);
          }}
        />

        <StatsGrid summary={compareData?.summary} />

        <FilterBar
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
        />

        {compareData?.warning && (
          <div className="notice-banner">
            <strong>System Notice:</strong> {compareData.warning}
          </div>
        )}

        {error && <div className="empty-state error">{error}</div>}

        {!error && loading && (
          <div className="empty-state">
            Executing comparison pipeline{method === "sbert" ? " (Sentence-BERT — can take up to a minute on CPU for a full document)" : ""}...
          </div>
        )}

        {!error && !loading && filteredResults.length === 0 && (
          <div className="empty-state">No matching clauses found for current filter.</div>
        )}

        {!error && !loading && filteredResults.length > 0 && (
          <div className="results-list">
            {filteredResults.map((r) => (
              <ClauseCard key={`${r.old_clause_number || "-"}-${r.new_clause_number || "-"}-${r.method}`} result={r} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
