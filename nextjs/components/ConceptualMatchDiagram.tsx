"use client";

/**
 * The "user-friendly" result view for Custom Document Comparison: instead of
 * a literal added/removed/unchanged list, this shows the headline similarity
 * score as a ring, then draws threads connecting passages that express the
 * same idea in both documents - content unique to one side sits below as a
 * plain dotted list instead of a thread. Same visual language (teal/gold,
 * card borders) as the rest of the "Veritext" UI.
 */

interface ThreadPair {
  labelA: string;
  labelB: string;
  similarity: number; // 0-1
}

interface ConceptualMatchDiagramProps {
  docALabel: string;
  docBLabel: string;
  globalSimilarity: number; // 0-1
  pairs: ThreadPair[];
  uniqueA: string[];
  uniqueB: string[];
}

const ROW_H = 120;

function threadColor(sim: number) {
  return `rgba(20, 184, 166, ${0.25 + sim * 0.55})`;
}

function ScoreRing({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value * 100));
  return (
    <div className="relative flex h-36 w-36 items-center justify-center">
      <svg viewBox="0 0 140 140" className="absolute inset-0 -rotate-90">
        <defs>
          <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#14b8a6" />
            <stop offset="100%" stopColor="#d4af37" />
          </linearGradient>
        </defs>
        <circle cx="70" cy="70" r="60" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
        <circle
          cx="70"
          cy="70"
          r="60"
          fill="none"
          stroke="url(#scoreGrad)"
          strokeWidth="10"
          strokeLinecap="round"
          pathLength={100}
          strokeDasharray={`${pct} 100`}
        />
      </svg>
      <div className="text-center">
        <div className="text-3xl font-bold text-white">{pct.toFixed(0)}%</div>
        <div className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">similar</div>
      </div>
    </div>
  );
}

export default function ConceptualMatchDiagram({
  docALabel,
  docBLabel,
  globalSimilarity,
  pairs,
  uniqueA,
  uniqueB,
}: ConceptualMatchDiagramProps) {
  const rows = Math.max(pairs.length, 1);

  return (
    <div className="rounded-3xl border border-brand-teal/20 bg-gradient-to-b from-brand-ink2/70 to-transparent p-6 shadow-[0_0_60px_-30px_rgba(20,184,166,0.35)] sm:p-8">
      <div className="flex flex-col items-center text-center">
        <ScoreRing value={globalSimilarity} />
        <h2 className="mt-4 text-lg font-bold text-white">
          How {docALabel} and {docBLabel} relate
        </h2>
        <p className="mt-1 max-w-md text-sm text-gray-400">
          A line connects two passages that say the same thing. Thicker, brighter lines mean a closer
          match. Anything found in only one document is listed below instead.
        </p>
      </div>

      {pairs.length > 0 && (
        <div className="relative mt-10">
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox={`0 0 1000 ${rows * ROW_H}`}
            preserveAspectRatio="none"
          >
            {pairs.map((p, i) => {
              const y = i * ROW_H + ROW_H / 2;
              return (
                <path
                  key={i}
                  d={`M 440 ${y} C 500 ${y}, 500 ${y}, 560 ${y}`}
                  stroke={threadColor(p.similarity)}
                  strokeWidth={2 + p.similarity * 4}
                  fill="none"
                />
              );
            })}
          </svg>
          <div className="relative grid grid-cols-2 gap-0">
            <div className="flex flex-col">
              {pairs.map((p, i) => (
                <div key={i} style={{ height: ROW_H }} className="flex items-center pr-6">
                  <div className="line-clamp-3 w-full rounded-xl border border-brand-teal/20 bg-white/[0.04] px-4 py-3 text-xs leading-relaxed text-gray-200">
                    {p.labelA}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex flex-col">
              {pairs.map((p, i) => (
                <div key={i} style={{ height: ROW_H }} className="flex items-center pl-6">
                  <div className="line-clamp-3 w-full rounded-xl border border-brand-gold/20 bg-white/[0.04] px-4 py-3 text-xs leading-relaxed text-gray-200">
                    {p.labelB}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-2 flex justify-between text-[11px] font-semibold uppercase tracking-wide text-gray-500">
            <span>{docALabel}</span>
            <span>{docBLabel}</span>
          </div>
        </div>
      )}

      {pairs.length === 0 && (
        <p className="mt-8 text-center text-sm text-gray-500">
          These two documents don&apos;t share any closely matching passages.
        </p>
      )}

      {(uniqueA.length > 0 || uniqueB.length > 0) && (
        <div className="mt-10 grid grid-cols-1 gap-6 border-t border-white/10 pt-6 md:grid-cols-2">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wide text-brand-teal">Only in {docALabel}</h3>
            <ul className="mt-2 space-y-2">
              {uniqueA.map((u, i) => (
                <li key={i} className="flex gap-2 text-xs text-gray-400">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-teal" />
                  <span className="line-clamp-2">{u}</span>
                </li>
              ))}
              {uniqueA.length === 0 && <li className="text-xs text-gray-600">Nothing unique found.</li>}
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wide text-brand-goldLight">
              Only in {docBLabel}
            </h3>
            <ul className="mt-2 space-y-2">
              {uniqueB.map((u, i) => (
                <li key={i} className="flex gap-2 text-xs text-gray-400">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-gold" />
                  <span className="line-clamp-2">{u}</span>
                </li>
              ))}
              {uniqueB.length === 0 && <li className="text-xs text-gray-600">Nothing unique found.</li>}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
