// Profile-based institution matching (ТЗ §14) — mirrors Flet institutions.py.
// Sorts a scenario's institutions so the ones in the user's city/region come
// first, and flags them so the UI can show «подобрано по вашему городу».
import type { Institution } from "../data/types";

const norm = (s?: string) => (s || "").toLowerCase().replace(/ё/g, "е").trim();

export type MatchedInstitution = Institution & { matched: boolean; matchReason?: string };

export function matchInstitutions(
  institutions: Institution[],
  profile: { city?: string; region?: string },
): MatchedInstitution[] {
  const city = norm(profile.city);
  const region = norm(profile.region);

  const scored = institutions.map((i) => {
    const ic = norm(i.city);
    const ir = norm(i.region);
    let score = 0;
    let reason: string | undefined;
    if (city && ic && ic === city) {
      score = 2;
      reason = `В вашем городе (${i.city})`;
    } else if (region && ir && ir === region) {
      score = 1;
      reason = `В вашем регионе (${i.region})`;
    }
    return { item: { ...i, matched: score > 0, matchReason: reason } as MatchedInstitution, score };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored.map((x) => x.item);
}

export function hasProfileLocation(profile: { city?: string; region?: string }): boolean {
  return !!(norm(profile.city) || norm(profile.region));
}
