// Profile-based institution matching (ТЗ §14) — mirrors Flet institutions.py.
// Sorts a scenario's institutions so the ones in the user's city/region come
// first, and flags them so the UI can show «подобрано по вашему городу».
import type { CategoryId, Institution, UserAddress, UserProfile } from "../data/types";

const norm = (s?: string) => (s || "").toLowerCase().replace(/ё/g, "е").trim();
const normPlace = (s?: string) =>
  norm(s)
    .replace(/[.,]/g, " ")
    .replace(/\bгород\b/g, "")
    .replace(/\bг\b/g, "")
    .replace(/\bобласть\b/g, "")
    .replace(/\bрайон\b/g, "")
    .replace(/\s+/g, " ")
    .trim();

const typeNorm = (s?: string) => norm(s).replace(/[\s_-]+/g, "_");

export type MatchedInstitution = Institution & { matched: boolean; matchReason?: string };

/** v1.1 (P5): один адрес пользователя. Совместимо с {city, region} из профиля. */
export type AddressLike = UserAddress | { city?: string; region?: string; district?: string; label?: string; id?: string };

const CATEGORY_TYPES: Record<CategoryId, string[]> = {
  documents: ["citizenship_migration", "one_window", "executive_committee", "notary", "registry_real_estate"],
  family: ["zags", "social_protection", "healthcare", "court", "one_window", "executive_committee"],
  work: ["employment_center", "court", "executive_committee", "one_window"],
  business: ["tax_office", "executive_committee", "one_window", "registry_real_estate"],
  housing: ["utility_service", "executive_committee", "one_window", "registry_real_estate"],
  taxes: ["tax_office", "one_window", "executive_committee"],
  health: ["healthcare", "one_window", "executive_committee"],
  auto: ["traffic_police", "one_window", "executive_committee"],
};

function includesNormalized(values: string[] | undefined, needle: string) {
  if (!needle) return false;
  return (values || []).some(value => {
    const hay = norm(value);
    return hay === needle || hay.includes(needle) || needle.includes(hay);
  });
}

function matchesScenarioTitle(inst: Institution, scenarioTitle: string) {
  const title = norm(scenarioTitle);
  if (!title) return false;
  if (includesNormalized(inst.relatedScenarios, title)) return true;
  const fields = [...(inst.services || []), ...(inst.tags || [])].map(norm).join(" ");
  if (!fields) return false;
  if (title.includes("паспорт")) return fields.includes("паспорт") || fields.includes("документ") || typeNorm(inst.type).includes("citizenship");
  if (title.includes("рожд") || title.includes("ребен")) return fields.includes("загс") || fields.includes("соц") || fields.includes("мед");
  if (title.includes("ип") || title.includes("бизнес")) return fields.includes("налог") || fields.includes("регистрац");
  if (title.includes("жкх") || title.includes("жиль")) return fields.includes("жкх") || fields.includes("жиль") || fields.includes("недвиж");
  if (title.includes("авто") || title.includes("водител")) return fields.includes("гаи") || fields.includes("транспорт");
  return false;
}

export function institutionsForScenario(
  scenarioInstitutions: Institution[],
  allInstitutions: Institution[],
  category: CategoryId,
  scenarioTitle: string,
  _max = 80,
): Institution[] {
  const categoryTypes = new Set((CATEGORY_TYPES[category] || []).map(typeNorm));
  const merged = new Map<string, Institution>();

  const add = (inst: Institution) => {
    if (inst.isActive === false) return;
    merged.set(inst.id, inst);
  };

  scenarioInstitutions.forEach(add);
  for (const inst of allInstitutions) {
    const instType = typeNorm(inst.type);
    const categoryMatch = includesNormalized(inst.relatedScenarioCategories, category);
    const typeMatch = instType ? categoryTypes.has(instType) : false;
    const scenarioMatch = matchesScenarioTitle(inst, scenarioTitle);
    if (categoryMatch || typeMatch || scenarioMatch) add(inst);
  }

  return Array.from(merged.values());
}

export function profileAddresses(profile: UserProfile): AddressLike[] {
  const addresses = (profile.addresses || [])
    .filter(address => address && (address.city || address.region || address.district))
    .sort((a, b) => Number(Boolean(b.isPrimary)) - Number(Boolean(a.isPrimary)));

  if (addresses.length) return addresses;
  if (profile.city || profile.region || profile.district) {
    return [{
      id: "legacy-profile-location",
      label: "Основной адрес",
      city: profile.city,
      region: profile.region,
      district: profile.district,
    }];
  }
  return [];
}

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
      items: institutions.filter(i => i.isActive !== false).map(i => ({ ...i, matched: false } as MatchedInstitution)),
    }];
  }

  return cleanAddresses.map((addr) => {
    const city = normPlace(addr.city);
    const region = normPlace(addr.region);
    const district = normPlace(addr.district);
    const seen = new Set<string>();
    const scored: Array<{ item: MatchedInstitution; score: number }> = [];

    for (const inst of institutions) {
      if (inst.isActive === false) continue;
      const ic = normPlace(inst.city);
      const is = normPlace(inst.settlement);
      const id = normPlace(inst.district);
      const ir = normPlace(inst.region);
      const ia = normPlace(inst.address);
      // Дедупликация: один и тот же институт не попадает в одну группу дважды.
      if (seen.has(inst.id)) continue;

      let score = 0;
      let reason: string | undefined;
      if (district && (id === district || ic === district || is === district || ia.includes(district))) {
        score = 4;
        reason = `В вашем районе (${inst.district || inst.city || inst.region})`;
      } else if (city && (ic === city || is === city || id === city || ia.includes(city))) {
        score = 3;
        reason = `В вашем городе (${inst.city || inst.settlement})`;
      } else if (region && ir && ir === region) {
        score = 2;
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
