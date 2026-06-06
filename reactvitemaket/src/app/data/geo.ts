// Belarus regions → districts → administrative center (city).
// Source: data/import/regions.json (mirrored from the Flet geo_data module).
// Editable: the admin "Регионы и города" panel persists changes to localStorage
// under GEO_KEY; this module reads that override first and falls back to the
// bundled JSON. Edits become visible app-wide after a reload.
import regionsData from "./geo-regions.json";

export type GeoDistrict = { name: string; center?: string };
export type GeoRegion = { region: string; region_center?: string; districts: GeoDistrict[] };

export const GEO_KEY = "belp.geo";

/** Immutable seed straight from the bundled JSON (used as fallback + reset). */
export const GEO_SEED: GeoRegion[] = (regionsData as GeoRegion[]).filter((r) => r.region);

function loadGeo(): GeoRegion[] {
  try {
    if (typeof window !== "undefined") {
      const raw = window.localStorage.getItem(GEO_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as GeoRegion[];
        if (Array.isArray(parsed) && parsed.length) return parsed.filter((r) => r.region);
      }
    }
  } catch {
    /* corrupt override → fall back to seed */
  }
  return GEO_SEED;
}

const REGIONS = loadGeo();

export const REGION_NAMES: string[] = REGIONS.map((r) => r.region);

export function districtsForRegion(region: string): GeoDistrict[] {
  return REGIONS.find((r) => r.region === region)?.districts ?? [];
}

export function cityForDistrict(region: string, district: string): string {
  const d = districtsForRegion(region).find((x) => x.name === district);
  return d?.center || district;
}
