// Token-level LCS diff, ported from the original app/api/dashboard.py implementation.
// Returns arrays of {text, changed} tokens instead of HTML strings, so React
// can render them directly without dangerouslySetInnerHTML.

function tokenize(text) {
  if (!text) return [];
  return text.match(/\w+|[^\w\s]|\s+/g) || [];
}

function computeLCS(oldTokens, newTokens) {
  const m = oldTokens.length;
  const n = newTokens.length;

  const dp = Array.from({ length: m + 1 }, () => new Int32Array(n + 1));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] =
        oldTokens[i - 1] === newTokens[j - 1]
          ? dp[i - 1][j - 1] + 1
          : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }

  let i = m, j = n;
  const inLcsOld = new Uint8Array(m);
  const inLcsNew = new Uint8Array(n);
  while (i > 0 && j > 0) {
    if (oldTokens[i - 1] === newTokens[j - 1]) {
      inLcsOld[i - 1] = 1;
      inLcsNew[j - 1] = 1;
      i--; j--;
    } else if (dp[i - 1][j] >= dp[i][j - 1]) {
      i--;
    } else {
      j--;
    }
  }
  return { inLcsOld, inLcsNew };
}

function toRuns(tokens, inLcs) {
  const runs = [];
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

// LCS is only meaningful up to a bounded token count - beyond that the O(n*m)
// DP table becomes impractically large (and, per our own evaluation findings,
// some malformed/oversized clauses can run to tens of thousands of
// characters). Above the cap, skip the alignment and show plain text.
const MAX_DIFF_TOKENS = 4000;

export function highlightDiff(oldText, newText) {
  if (!oldText || !newText) {
    return {
      oldRuns: [{ text: oldText || "", changed: false }],
      newRuns: [{ text: newText || "", changed: false }],
    };
  }

  const oldTokens = tokenize(oldText);
  const newTokens = tokenize(newText);

  if (oldTokens.length > MAX_DIFF_TOKENS || newTokens.length > MAX_DIFF_TOKENS) {
    return {
      oldRuns: [{ text: oldText, changed: false }],
      newRuns: [{ text: newText, changed: false }],
    };
  }

  const { inLcsOld, inLcsNew } = computeLCS(oldTokens, newTokens);
  return {
    oldRuns: toRuns(oldTokens, inLcsOld),
    newRuns: toRuns(newTokens, inLcsNew),
  };
}
