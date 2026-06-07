// Profile-based institution matching (ТЗ §14) — mirrors Flet institutions.py.
// Sorts a scenario's institutions so the ones in the user's city/region come
// first, and flags them so the UI can show «подобрано по вашему городу».
import type { Institution, UserAddress } from "../data/types";

const norm = (s?: string) => (s || "").toLowerCase().replace(/ё/g, "е").trim();

export type MatchedInstitution = Institution & { matched: boolean; matchReason?: string };

/** v1.1 (P5): один адрес пользователя. Совместимо с {city, region} из профиля. */
export type AddressLike = UserAddress | { city?: string; region?: string; district?: string; label?: string; id?: string };

export function matchInstitutions(
  institutions: Institution[],
  profile: { city?: string; region?: string } | AddressLike,
): MatchedInstitution[] {
  // Backwards-compat: если это объект профиля {city, region} или один адрес.
  return matchInstitutionsForAddresses(institutions, [profile]).flatMap(g => g.items);
}

/** v1.1 (P5): сгруппировать учреждения по списку адресов пользователя.

  Возвращает массив групп — по одной на каждый адрес. Внутри группы
  учреждения отсортированы по релевантности (город → регион) и дедуплицированы.
  Если точного совпадения нет, но регион подходит — попадает в группу
  ближайшим общим вариантом.
*/
export function matchInstitutionsForAddresses(
  institutions: Institution[],
  addresses: AddressLike[],
): Array<{ address: AddressLike; items: MatchedInstitution[] }> {
  const cleanAddresses = addresses.filter(a => a && (norm((a as AddressLike).city) || norm((a as AddressLike).region) || norm((a as AddressLike).district)));
  if (cleanAddresses.length === 0) {
    // Нет ни одного валидного адреса — отдать как есть, без matchReason.
    return [{
      address: { label: "Без адреса" } as AddressLike,
      items: institutions.map(i => ({ ...i, matched: false } as MatchedInstitution)),
    }];
  }

  return cleanAddresses.map((addr) => {
    const city = norm(addr.city);
    const region = norm(addr.region);
    const district = norm(addr.district);
    const seen = new Set<string>();
    const scored: Array<{ item: MatchedInstitution; score: number }> = [];

    for (const inst of institutions) {
      const ic = norm(inst.city);
      const ir = norm(inst.region);
      // Дедупликация: один и тот же институт не попадает в одну группу дважды.
      if (seen.has(inst.id)) continue;

      let score = 0;
      let reason: string | undefined;
      if (city && ic && ic === city) {
        score = 3;
        reason = `В вашем городе (${inst.city})`;
      } else if (district && ir && ir === district) {
        score = 2;
        reason = `В вашем районе (${inst.region})`;
      } else if (region && ir && ir === region) {
        score = 1;
        reason = `В вашем регионе (${inst.region})`;
      }
      if (score > 0) {
        seen.add(inst.id);
        scored.push({ item: { ...inst, matched: true, matchReason: reason } as MatchedInstitution, score });
      }
    }

    // Сортируем внутри группы по релевантности.
    scored.sort((a, b) => b.score - a.score);
    return { address: addr, items: scored.map(s => s.item) };
  });
}

export function hasProfileLocation(profile: { city?: string; region?: string } | AddressLike): boolean {
  if (!profile) return false;
  return !!(norm((profile as AddressLike).city) || norm((profile as AddressLike).region) || norm((profile as AddressLike).district));
}
