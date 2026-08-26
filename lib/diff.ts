// Token-level LCS diff, ported from web/src/lib/diff.js (itself ported from
// the original app/api/dashboard.py implementation). Kept in sync across all
// three UIs deliberately - it's the one piece of comparison-result rendering
// logic that isn't just calling the API.

export interface DiffRun {
  text: string;
  changed: boolean;
}

function tokenize(text: string): string[] {
  if (!text) return [];
  return text.match(/\w+|[^\w\s]|\s+/g) || [];
}

function computeLCS(oldTokens: string[], newTokens: string[]) {
  const m = oldTokens.length;
  const n = newTokens.length;

  const dp: Int32Array[] = Array.from({ length: m + 1 }, () => new Int32Array(n + 1));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] =
        oldTokens[i - 1] === newTokens[j - 1]
          ? dp[i - 1][j - 1] + 1
          : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }

  let i = m;
  let j = n;
  const inLcsOld = new Uint8Array(m);
  const inLcsNew = new Uint8Array(n);
  while (i > 0 && j > 0) {
    if (oldTokens[i - 1] === newTokens[j - 1]) {
      inLcsOld[i - 1] = 1;
      inLcsNew[j - 1] = 1;
      i--;
      j--;
    } else if (dp[i - 1][j] >= dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }
  return { inLcsOld, inLcsNew };
}

function toRuns(tokens: string[], inLcs: Uint8Array): DiffRun[] {
  const runs: DiffRun[] = [];
  for (let i = 0; i < tokens.length; i++) {
    const changed = inLcs[i] !== 1;
    const last = runs[runs.length - 1];
    if (last && last.changed === changed) {
      last.text += tokens[i];
    } else {
      runs.push({ text: tokens[i], changed });
    }
  }
  return runs;
}

// Above this many tokens, skip the O(n*m) LCS alignment and show plain text -
// protects against pathologically oversized clauses (see the runaway-clause
// parser bug documented in app/ingestion/clause_parser.py's history).
const MAX_DIFF_TOKENS = 4000;

export function highlightDiff(oldText: string | null, newText: string | null) {
  if (!oldText || !newText) {
    return {
      oldRuns: [{ text: oldText || "", changed: false }] as DiffRun[],
      newRuns: [{ text: newText || "", changed: false }] as DiffRun[],
    };
  }

  const oldTokens = tokenize(oldText);
  const newTokens = tokenize(newText);

  if (oldTokens.length > MAX_DIFF_TOKENS || newTokens.length > MAX_DIFF_TOKENS) {
    return {
      oldRuns: [{ text: oldText, changed: false }] as DiffRun[],
      newRuns: [{ text: newText, changed: false }] as DiffRun[],
    };
  }

  const { inLcsOld, inLcsNew } = computeLCS(oldTokens, newTokens);
  return {
    oldRuns: toRuns(oldTokens, inLcsOld),
    newRuns: toRuns(newTokens, inLcsNew),
  };
}
