"use client";

function truncate(text: string, max: number) {
  return text.length > max ? text.slice(0, max) + "…" : text;
}

function cellColor(value: number) {
  // Dark theme heat scale: low similarity stays near-invisible against the
  // panel background, high similarity glows in the app's indigo accent.
  return `rgba(20, 184, 166, ${Math.max(0.06, value)})`;
}

export default function SimilarityHeatmap({
  matrix,
  chunksA,
  chunksB,
  docALabel,
  docBLabel,
}: {
  matrix: number[][];
  chunksA: string[];
  chunksB: string[];
  docALabel: string;
  docBLabel: string;
}) {
  const rows = matrix.length;
  const cols = matrix[0]?.length ?? 0;
  const cellSize = Math.max(10, Math.min(22, Math.floor(640 / Math.max(cols, 1))));

  if (rows === 0 || cols === 0) {
    return <div className="text-sm text-gray-500">No matrix data to visualize.</div>;
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs text-gray-500">
        <span>{docALabel} (rows, {rows})</span>
        <span>{docBLabel} (columns, {cols})</span>
      </div>
      <div className="overflow-auto rounded-lg border border-white/5 bg-slate-900/60 p-2">
        <div
          className="grid"
          style={{ gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`, gap: 1, width: "max-content" }}
        >
          {matrix.map((row, i) =>
            row.map((value, j) => (
              <div
                key={`${i}-${j}`}
                title={`${docALabel} #${i + 1}: ${truncate(chunksA[i] ?? "", 200)}\n\n${docBLabel} #${j + 1}: ${truncate(
                  chunksB[j] ?? "",
                  200
                )}\n\nSimilarity: ${(value * 100).toFixed(1)}%`}
                style={{ width: cellSize, height: cellSize, backgroundColor: cellColor(value) }}
                className="cursor-default rounded-[2px]"
              />
            ))
          )}
        </div>
      </div>
      <p className="mt-2 text-xs text-gray-500">
        Hover any cell to see the paragraph pair and exact similarity score. Brighter = more similar.
      </p>
    </div>
  );
}
