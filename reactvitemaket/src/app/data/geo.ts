// Belarus regions -> districts -> administrative center (city).
// Source: data/import/regions.json (mirrored from the Flet geo_data module).
// Editable: the admin "Регионы и города" panel persists changes to localStorage
// under GEO_KEY; this module reads that override first and falls back to the
// bundled JSON. Edits become visible app-wide after a reload.
import regionsData from "./geo-regions.json";

export type GeoDistrict = {
  id?: string;
  name: string;
  center?: string;
  sortOrder?: number;
  isActive?: boolean;
};

export type GeoRegion = {
  id?: string;
  region: string;
  displayName?: string;
  region_center?: string;
  districts: GeoDistrict[];
  mapLabelX?: number;
  mapLabelY?: number;
  mapLabelAnchor?: string;
  mapLabelOrder?: number;
  mapLabelVisible?: boolean;
  isActive?: boolean;
  createdAt?: string;
  updatedAt?: string;
};

export const GEO_KEY = "belp.geo";

export const DEFAULT_REGION_POSITIONS: Record<string, { x: number; y: number; short: string; order: number }> = {
  "Витебская область": { x: 58, y: 22, short: "Витебская", order: 1 },
  "Гродненская область": { x: 27, y: 48, short: "Гродненская", order: 2 },
  "Минская область": { x: 52, y: 58, short: "Минская", order: 3 },
  "Могилевская область": { x: 75, y: 47, short: "Могилевская", order: 4 },
  "Могилёвская область": { x: 75, y: 47, short: "Могилевская", order: 4 },
  "Брестская область": { x: 30, y: 76, short: "Брестская", order: 5 },
  "Гомельская область": { x: 66, y: 78, short: "Гомельская", order: 6 },
  "г. Минск": { x: 49, y: 50, short: "Минск", order: 7 },
  "Минск": { x: 49, y: 50, short: "Минск", order: 7 },
};

const fallbackSlots = [
  { x: 84, y: 16 },
  { x: 84, y: 28 },
  { x: 84, y: 40 },
  { x: 84, y: 52 },
  { x: 84, y: 64 },
  { x: 84, y: 76 },
];

export function clampMapPercent(value: unknown, fallback: number): number {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(0, Math.min(100, Math.round(n * 10) / 10));
}

export function defaultRegionPosition(region: string, index = 0) {
  const known = DEFAULT_REGION_POSITIONS[region];
  if (known) return known;
  const slot = fallbackSlots[index % fallbackSlots.length];
  return { ...slot, short: region.replace(/ область$/i, ""), order: 100 + index };
}

export function normalizeGeoRegion(input: GeoRegion, index = 0): GeoRegion {
  const pos = defaultRegionPosition(input.region, index);
  const regionId = input.id || input.region.toLowerCase().replace(/[^0-9a-zа-яё]+/gi, "-").replace(/^-|-$/g, "") || `region-${index}`;
  const now = new Date().toISOString();
  return {
    id: regionId,
    region: input.region,
    displayName: input.displayName || pos.short || input.region,
    region_center: input.region_center || "",
    districts: (input.districts || []).map((district, districtIndex) => ({
      id: district.id || `${regionId}-district-${districtIndex}`,
      name: district.name,
      center: district.center || "",
      sortOrder: typeof district.sortOrder === "number" ? district.sortOrder : districtIndex,
      isActive: district.isActive !== false,
    })),
    mapLabelX: clampMapPercent(input.mapLabelX, pos.x),
    mapLabelY: clampMapPercent(input.mapLabelY, pos.y),
    mapLabelAnchor: input.mapLabelAnchor || "center",
    mapLabelOrder: typeof input.mapLabelOrder === "number" ? input.mapLabelOrder : pos.order,
    mapLabelVisible: input.mapLabelVisible !== false,
    isActive: input.isActive !== false,
    createdAt: input.createdAt || now,
    updatedAt: input.updatedAt || now,
  };
}

function normalizeGeoList(items: GeoRegion[]): GeoRegion[] {
  return items.filter((r) => r.region).map((r, index) => normalizeGeoRegion(r, index));
}

/** Immutable seed straight from the bundled JSON (used as fallback + reset). */
export const GEO_SEED: GeoRegion[] = normalizeGeoList(regionsData as GeoRegion[]);

function loadGeo(): GeoRegion[] {
  try {
    if (typeof window !== "undefined") {
      const raw = window.localStorage.getItem(GEO_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as GeoRegion[];
        if (Array.isArray(parsed) && parsed.length) return normalizeGeoList(parsed);
      }
    }
  } catch {
    /* corrupt override -> fall back to seed */
  }
  return GEO_SEED;
}

const REGIONS = loadGeo();

export const REGION_NAMES: string[] = REGIONS.filter((r) => r.isActive !== false).map((r) => r.region);

export function districtsForRegion(region: string): GeoDistrict[] {
  return REGIONS.find((r) => r.region === region && r.isActive !== false)?.districts.filter((d) => d.isActive !== false) ?? [];
}

export function cityForDistrict(region: string, district: string): string {
  const d = districtsForRegion(region).find((x) => x.name === district);
  return d?.center || district;
}
