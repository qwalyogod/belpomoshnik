// Google-like search helpers: recent queries (localStorage) + prefix/scored
// suggestion ranking. Mirrors the Flet search_suggestions module.

const RECENT_KEY = "belp.recentSearches";

export const POPULAR_QUERIES = [
  "Потерял паспорт",
  "Рождение ребёнка",
  "Открыть ИП",
  "Оплатить ЖКХ",
  "Налог на недвижимость",
  "Переезд и регистрация",
];

export function getRecentSearches(): string[] {
  try {
    const v = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
    return Array.isArray(v) ? v.filter(x => typeof x === "string").slice(0, 8) : [];
  } catch {
    return [];
  }
}

export function addRecentSearch(query: string) {
  const q = query.trim();
  if (q.length < 2) return;
  try {
    const prev = getRecentSearches().filter(x => x.toLowerCase() !== q.toLowerCase());
    localStorage.setItem(RECENT_KEY, JSON.stringify([q, ...prev].slice(0, 8)));
  } catch {
    /* ignore */
  }
}

export function clearRecentSearches() {
  try { localStorage.removeItem(RECENT_KEY); } catch { /* ignore */ }
}

export type SuggestionItem = { label: string; kind: string };

const norm = (s: string) => (s || "").toLowerCase().replace(/ё/g, "е").trim();

export function scoreLabel(label: string, query: string): number {
  const l = norm(label);
  const q = norm(query);
  if (!l || !q) return 0;
  if (l === q) return 1;
  if (l.startsWith(q)) return 0.8;
  if (l.split(/\s+/).some(w => w.startsWith(q))) return 0.5;
  if (l.includes(q)) return 0.35;
  return 0;
}

export function buildSuggestions(query: string, pool: SuggestionItem[], limit = 8): SuggestionItem[] {
  const q = norm(query);
  if (q.length < 2) return [];
  const seen = new Set<string>();
  const scored: { item: SuggestionItem; score: number }[] = [];
  for (const item of pool) {
    const key = norm(item.label);
    if (!key || seen.has(key)) continue;
    const score = scoreLabel(item.label, q);
    if (score > 0) {
      seen.add(key);
      scored.push({ item, score });
    }
  }
  scored.sort((a, b) => b.score - a.score || a.item.label.localeCompare(b.item.label));
  return scored.slice(0, limit).map(x => x.item);
}

// Generic page-scoped text filter: keeps items whose any searchable field matches.
export function matchesQuery(query: string, fields: (string | undefined)[]): boolean {
  const q = norm(query);
  if (!q) return true;
  return fields.some(f => norm(f || "").includes(q));
}
