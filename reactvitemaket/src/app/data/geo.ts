// Belarus regions → districts → administrative center (city).
// Source: data/import/regions.json (mirrored from the Flet geo_data module).
import regionsData from "./geo-regions.json";

export type GeoDistrict = { name: string; center?: string };
export type GeoRegion = { region: string; districts: GeoDistrict[] };

const REGIONS = (regionsData as GeoRegion[]).filter((r) => r.region);

export const REGION_NAMES: string[] = REGIONS.map((r) => r.region);

export function districtsForRegion(region: string): GeoDistrict[] {
  return REGIONS.find((r) => r.region === region)?.districts ?? [];
}

export function cityForDistrict(region: string, district: string): string {
  const d = districtsForRegion(region).find((x) => x.name === district);
  return d?.center || district;
}
