import { ReactNode, useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import { REGION_NAMES, districtsForRegion, cityForDistrict } from "../data/geo";
import { useStore } from "../data/store";

export const COLORS = {
  royal: "#0056FF",
  azure: "#2277FF",
  lavender: "#E3E7FC",
};

// v1.2: единый кружок-аватар. Показывает фото (object-cover) либо инициал на
// фирменном градиенте. Используется в хедере (desktop), меню (tablet/sidebar) и
// на странице профиля — чтобы аватар выглядел одинаково везде.
//
// v1.3 (2026-06-11): если ни `src`, ни имя не дают осмысленного символа,
// показываем первую букву email, иначе — нейтральный «П». Это гарантирует,
// что у гостя с именем «Гость» отображается «Г», у залогиненного с именем
// «Алексей» — «А», а у безымянного аккаунта — первая буква email до «@».
function avatarInitial(name?: string, email?: string): string {
  const trimmed = (name ?? "").trim();
  if (trimmed) return trimmed[0]!.toUpperCase();
  const mail = (email ?? "").trim();
  if (mail) {
    const at = mail.indexOf("@");
    const head = (at > 0 ? mail.slice(0, at) : mail).trim();
    if (head) return head[0]!.toUpperCase();
  }
  return "П";
}

export function UserAvatarCircle({
  src,
  name,
  email,
  size = 36,
  className = "",
}: { src?: string; name?: string; email?: string; size?: number; className?: string }) {
  const initial = avatarInitial(name, email);
  return (
    <span
      className={`grid shrink-0 place-items-center overflow-hidden rounded-full bg-gradient-to-br from-[#0056FF] to-[#2277FF] font-medium text-white ${className}`}
      style={{ width: size, height: size, fontSize: Math.max(11, Math.round(size * 0.4)) }}
    >
      {src ? <img src={src} alt="" className="h-full w-full object-cover" /> : <span>{initial}</span>}
    </span>
  );
}

export function Pill({ children, tone = "lavender" }: { children: ReactNode; tone?: "lavender" | "royal" | "azure" | "ghost" | "warn" | "ok" }) {
  const map: Record<string, string> = {
    lavender: "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]",
    royal: "bg-[#0056FF] text-white",
    azure: "bg-[#2277FF] text-white",
    ghost: "bg-black/[0.04] text-black/70 dark:bg-white/10 dark:text-white/70",
    warn: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
    ok: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] tracking-tight ${map[tone]}`}>
      {children}
    </span>
  );
}

export function PrimaryButton({ children, className = "", icon, onClick }: { children: ReactNode; className?: string; icon?: ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`group relative inline-flex h-12 items-center justify-center gap-2 overflow-hidden rounded-2xl bg-[#0056FF] px-5 text-white shadow-[0_10px_30px_-12px_rgba(0,86,255,0.55)] transition-all active:translate-y-[1px] hover:bg-[#0049DB] ${className}`}
    >
      <span className="absolute inset-0 bg-gradient-to-r from-[#0056FF] via-[#2277FF] to-[#0056FF] opacity-0 transition-opacity group-hover:opacity-100" />
      <span className="relative inline-flex items-center gap-2 tracking-tight">
        {children}
        {icon}
      </span>
    </button>
  );
}

export function GhostButton({ children, className = "", onClick }: { children: ReactNode; className?: string; onClick?: () => void }) {
  return (
    <button onClick={onClick} className={`inline-flex h-12 items-center justify-center rounded-2xl border border-black/10 bg-white/60 px-5 tracking-tight text-black backdrop-blur transition-colors hover:bg-white dark:border-white/10 dark:bg-white/[0.04] dark:text-white dark:hover:bg-white/[0.08] ${className}`}>
      {children}
    </button>
  );
}

export function Card({ children, className = "", interactive = false }: { children: ReactNode; className?: string; interactive?: boolean }) {
  return (
    <div
      className={`relative rounded-3xl border border-black/[0.06] bg-white p-5 shadow-[0_1px_0_rgba(0,0,0,0.02),0_24px_48px_-32px_rgba(15,23,42,0.18)] dark:border-white/[0.06] dark:bg-[#0F1117] dark:shadow-[0_1px_0_rgba(255,255,255,0.02),0_24px_48px_-24px_rgba(0,0,0,0.6)] ${interactive ? "transition-all hover:-translate-y-[2px] hover:shadow-[0_1px_0_rgba(0,0,0,0.02),0_32px_60px_-28px_rgba(15,23,42,0.28)]" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

export function LocationPicker({
  value,
  onChange,
  className = "",
}: {
  value: { region: string; district?: string; city: string };
  onChange: (v: { region: string; district: string; city: string }) => void;
  className?: string;
}) {
  const districts = districtsForRegion(value.region);
  const fieldCls =
    "w-full appearance-none rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight text-black outline-none transition-colors focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white";
  const labelCls = "mb-1.5 block text-[11px] uppercase tracking-[0.12em] text-black/45 dark:text-white/45";

  const onRegion = (region: string) => {
    const ds = districtsForRegion(region);
    const district = ds[0]?.name ?? "";
    onChange({ region, district, city: cityForDistrict(region, district) });
  };
  const onDistrict = (district: string) => {
    onChange({ region: value.region, district, city: cityForDistrict(value.region, district) });
  };

  return (
    <div className={`grid gap-3 sm:grid-cols-3 ${className}`}>
      <div>
        <label className={labelCls}>Регион</label>
        <select value={value.region} onChange={(e) => onRegion(e.target.value)} className={fieldCls}>
          {!REGION_NAMES.includes(value.region) && <option value={value.region}>{value.region || "Выберите регион"}</option>}
          {REGION_NAMES.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>
      <div>
        <label className={labelCls}>Район</label>
        <select value={value.district ?? ""} onChange={(e) => onDistrict(e.target.value)} disabled={districts.length === 0} className={`${fieldCls} disabled:opacity-50`}>
          {districts.length === 0 && <option value="">Нет данных</option>}
          {districts.map((d) => <option key={d.name} value={d.name}>{d.name}</option>)}
        </select>
      </div>
      <div>
        <label className={labelCls}>Город</label>
        <input value={value.city} onChange={(e) => onChange({ region: value.region, district: value.district ?? "", city: e.target.value })} placeholder="Город" className={fieldCls} />
      </div>
    </div>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return <div className="mb-4 tracking-tight text-black/50 dark:text-white/50">{children}</div>;
}

export function PhoneFrame({ children, label }: { children: ReactNode; label?: string }) {
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative h-[760px] w-[370px] rounded-[48px] bg-black p-[10px] shadow-[0_50px_120px_-30px_rgba(0,0,0,0.35),0_0_0_1px_rgba(0,0,0,0.05)] dark:shadow-[0_50px_120px_-30px_rgba(0,0,0,0.7)]">
        <div className="relative h-full w-full overflow-hidden rounded-[40px] bg-[#F6F7FB] dark:bg-[#07080C]">
          <div className="absolute left-1/2 top-2 z-30 h-6 w-28 -translate-x-1/2 rounded-full bg-black" />
          {children}
        </div>
      </div>
      {label && <div className="text-[12px] tracking-tight text-black/50 dark:text-white/40">{label}</div>}
    </div>
  );
}

export function StatusBar() {
  return (
    <div className="relative z-20 flex items-center justify-between px-7 pt-4 text-[12px] tracking-tight text-black dark:text-white">
      <span>9:41</span>
      <span className="flex items-center gap-1.5 opacity-80">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
        <span className="inline-block h-1.5 w-2 rounded-sm bg-current" />
      </span>
    </div>
  );
}

export function Logo({ size = 28, white = false }: { size?: number; white?: boolean }) {
  return (
    <div className="inline-flex items-center gap-2.5">
      <motion.div
        initial={{ rotate: -8, scale: 0.9 }}
        animate={{ rotate: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 220, damping: 18 }}
        className="relative grid place-items-center rounded-[10px]"
        style={{ width: size, height: size, background: "linear-gradient(135deg,#0056FF 0%,#2277FF 60%,#9BB8FF 100%)" }}
      >
        <span className="tracking-tight text-white" style={{ fontSize: size * 0.5 }}>Б</span>
        <span className="absolute inset-0 rounded-[10px] ring-1 ring-inset ring-white/30" />
      </motion.div>
      <span className={`tracking-tight ${white ? "text-white" : "text-black dark:text-white"}`} style={{ fontSize: size * 0.55 }}>
        Белпомощник
      </span>
    </div>
  );
}

/**
 * Бэйдж "Backend" / "Mock-данные" — показывает, откуда UI получает контент.
 * Помогает на защите: сразу видно, идёт ли запрос в FastAPI или показываются
 * встроенные fallback-моки.
 */
export function DataModeBadge({ className = "" }: { className?: string }) {
  const status = useStore(s => (s as { publicContentStatus?: "loading" | "api" | "fallback" }).publicContentStatus);
  const label =
    status === "api" ? "Backend" :
    status === "loading" ? "Загрузка…" :
    "Mock-данные";
  const tone =
    status === "api" ? "ok" :
    status === "loading" ? "ghost" :
    "warn";
  return (
    <Pill tone={tone as "ok" | "ghost" | "warn"}>
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </Pill>
  );
}

/* ============================================================
   RegionSearch / DistrictSearch — autocomplete из geo-regions.json
   Пользователь НЕ может ввести произвольный текст: только выбор из базы.
   ============================================================ */

const searchFieldCls =
  "w-full appearance-none rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight text-black outline-none transition-colors focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white";
const searchLabelCls =
  "mb-1.5 block text-[11px] uppercase tracking-[0.12em] text-black/45 dark:text-white/45";

/** Autocomplete-инпут: фильтрует options по подстроке, позволяет выбрать только из базы. */
function AutocompleteInput({
  label,
  value,
  options,
  onChange,
  placeholder,
  disabled,
}: {
  label?: string;
  value: string;
  options: string[];
  onChange: (next: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(value);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => { setQuery(value); }, [value]);

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const filtered = (() => {
    const q = query.trim().toLowerCase();
    if (!q) return options.slice(0, 50);
    return options.filter(o => o.toLowerCase().includes(q)).slice(0, 50);
  })();

  const onPick = (next: string) => {
    onChange(next);
    setQuery(next);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative">
      {label && <label className={searchLabelCls}>{label}</label>}
      <input
        type="text"
        value={query}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        className={searchFieldCls}
        autoComplete="off"
      />
      {open && !disabled && filtered.length > 0 && (
        <div className="absolute z-30 mt-1 max-h-56 w-full overflow-y-auto rounded-xl border border-black/10 bg-white shadow-[0_18px_44px_-22px_rgba(15,23,42,0.45)] dark:border-white/10 dark:bg-[#0F1117]">
          {filtered.map((opt) => (
            <button
              key={opt}
              type="button"
              onClick={() => onPick(opt)}
              className="block w-full px-3 py-2 text-left text-[14px] tracking-tight text-black hover:bg-[#E3E7FC] dark:text-white dark:hover:bg-[#0E1A3A]"
            >
              {opt}
            </button>
          ))}
        </div>
      )}
      {open && !disabled && filtered.length === 0 && (
        <div className="absolute z-30 mt-1 w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-[12px] text-black/55 shadow dark:border-white/10 dark:bg-[#0F1117] dark:text-white/55">
          Ничего не найдено. Регион/район/город должны быть в базе.
        </div>
      )}
    </div>
  );
}

export function RegionSearch({
  value,
  onChange,
  label = "Область / регион",
  disabled,
}: {
  value: string;
  onChange: (next: string) => void;
  label?: string;
  disabled?: boolean;
}) {
  return (
    <AutocompleteInput
      label={label}
      value={value}
      options={REGION_NAMES}
      onChange={onChange}
      placeholder="Начните вводить: Минск, Гомел…"
      disabled={disabled}
    />
  );
}

export function DistrictSearch({
  region,
  value,
  onChange,
  label = "Район",
  disabled,
}: {
  region: string;
  value: string;
  onChange: (next: string) => void;
  label?: string;
  disabled?: boolean;
}) {
  const districtNames = districtsForRegion(region).map(d => d.name);
  return (
    <AutocompleteInput
      label={label}
      value={value}
      options={districtNames}
      onChange={onChange}
      placeholder={region ? "Начните вводить район…" : "Сначала выберите регион"}
      disabled={disabled || !region}
    />
  );
}

export function CitySearch({
  region,
  district,
  value,
  onChange,
  label = "Город / населённый пункт",
  disabled,
}: {
  region: string;
  district: string;
  value: string;
  onChange: (next: string) => void;
  label?: string;
  disabled?: boolean;
}) {
  // Города = центры районов выбранной области. Если ничего не выбрано — пустой список.
  const cities = (() => {
    if (!region) return [];
    const ds = districtsForRegion(region);
    // Собираем уникальные города из центров районов.
    const set = new Set<string>();
    ds.forEach(d => { if (d.center) set.add(d.center); });
    // Также сам центр региона.
    const regionObj = (() => {
      try {
        // Через loadGeo нельзя извне, но REGION_NAMES + districtsForRegion
        // уже умеют. Просто добавим «областной центр» если найдём.
        return null;
      } catch { return null; }
    })();
    return Array.from(set).sort();
  })();
  return (
    <AutocompleteInput
      label={label}
      value={value}
      options={cities}
      onChange={onChange}
      placeholder={region && district ? "Начните вводить город…" : "Сначала выберите регион и район"}
      disabled={disabled || !region}
    />
  );
}
