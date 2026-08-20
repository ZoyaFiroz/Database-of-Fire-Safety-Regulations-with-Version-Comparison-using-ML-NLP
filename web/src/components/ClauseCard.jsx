import { highlightDiff } from "../lib/diff";

function DiffPane({ label, text, runs, empty }) {
  return (
    <div className="diff-pane">
      <div className="diff-pane-header">{label}</div>
      <div>
        {text
          ? runs.map((run, i) =>
              run.changed ? (
                <mark key={i} className={label.startsWith("Version A") ? "del" : "add"}>
                  {run.text}
                </mark>
              ) : (
                <span key={i}>{run.text}</span>
              )
            )
          : <em>{empty}</em>}
      </div>
    </div>
  );
}

export default function ClauseCard({ result }) {
  const num = result.old_clause_number || result.new_clause_number || "N/A";
  const simPct = (result.similarity * 100).toFixed(1) + "%";
  const { oldRuns, newRuns } = highlightDiff(result.old_text, result.new_text);

  return (
    <div className="clause-card">
      <div className="clause-header">
        <div className="clause-info">
          <div className="clause-tag">Clause {num}</div>
          <div className="section-title">
            Method: <code>{result.method}</code>
          </div>
        </div>
        <div className="badges-group">
          <div className="badge-sim">Sim: {simPct}</div>
          <div className={`badge ${result.change_type}`}>{result.change_type}</div>
        </div>
      </div>
      <div className="diff-grid">
        <DiffPane
          label="Version A (Base)"
          text={result.old_text}
          runs={oldRuns}
          empty="Clause not present in Version A"
        />
        <DiffPane
          label="Version B (Comparison)"
          text={result.new_text}
          runs={newRuns}
          empty="Clause not present in Version B"
        />
      </div>
    </div>
  );
}
