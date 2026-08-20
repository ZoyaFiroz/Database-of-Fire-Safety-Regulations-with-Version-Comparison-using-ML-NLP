function buildPresets(versions) {
  if (versions.length < 2) return [];
  const sorted = [...versions].sort((a, b) => a.id - b.id);
  const presets = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    presets.push({
      oldId: sorted[i].id,
      newId: sorted[i + 1].id,
      label: `${sorted[i].label} → ${sorted[i + 1].label}`,
    });
  }
  if (sorted.length > 2) {
    presets.push({
      oldId: sorted[0].id,
      newId: sorted[sorted.length - 1].id,
      label: `${sorted[0].label} → ${sorted[sorted.length - 1].label} (Full Evolution)`,
    });
  }
  return presets;
}

export default function Controls({
  documents,
  selectedDocId,
  onDocChange,
  versions,
  oldVersionId,
  newVersionId,
  onOldVersionChange,
  onNewVersionChange,
  method,
  onMethodChange,
  onPreset,
}) {
  const presets = buildPresets(versions);

  return (
    <>
      {presets.length > 0 && (
        <div className="presets-bar">
          <span className="preset-label">Comparison Presets:</span>
          {presets.map((p) => (
            <button
              key={`${p.oldId}-${p.newId}`}
              className="preset-btn"
              onClick={() => onPreset(p.oldId, p.newId)}
            >
              {p.label}
            </button>
          ))}
        </div>
      )}

      <div className="controls-panel">
        <div className="control-group">
          <label>Regulation Document</label>
          <select value={selectedDocId ?? ""} onChange={(e) => onDocChange(Number(e.target.value))}>
            {documents.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
        </div>
        <div className="control-group">
          <label>Version A (Base)</label>
          <select value={oldVersionId ?? ""} onChange={(e) => onOldVersionChange(Number(e.target.value))}>
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label} (v{v.id})
              </option>
            ))}
          </select>
        </div>
        <div className="control-group">
          <label>Version B (Comparison)</label>
          <select value={newVersionId ?? ""} onChange={(e) => onNewVersionChange(Number(e.target.value))}>
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label} (v{v.id})
              </option>
            ))}
          </select>
        </div>
        <div className="control-group">
          <label>NLP Model Pipeline</label>
          <select value={method} onChange={(e) => onMethodChange(e.target.value)}>
            <option value="sbert">Stage 3: Sentence-BERT (all-MiniLM-L6-v2)</option>
            <option value="baseline">Baseline: difflib + TF-IDF</option>
          </select>
        </div>
      </div>
    </>
  );
}
