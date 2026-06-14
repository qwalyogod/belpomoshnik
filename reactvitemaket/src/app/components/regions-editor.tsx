import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { Building2, Check, EyeOff, List, MapPin, Move, Plus, RotateCcw, Save, Trash2, X } from "lucide-react";
import { useStore } from "../data/store";
import { clampMapPercent, defaultRegionPosition, type GeoRegion } from "../data/geo";

type Row = { id: string; name: string; center: string; sortOrder: number; isActive: boolean };
type Position = { x: number; y: number };

let RID = 0;

const inputCls =
  "w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-[14px] tracking-tight text-black outline-none transition-colors placeholder:text-black/30 focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/25";

const labelCls = "text-[12px] tracking-tight text-black/45 dark:text-white/45";

function regionKey(region: GeoRegion) {
  return region.id || region.region;
}

function toRows(region?: GeoRegion | null): Row[] {
  return (region?.districts ?? []).map((district, index) => ({
    id: district.id || `d${RID++}`,
    name: district.name,
    center: district.center || "",
    sortOrder: typeof district.sortOrder === "number" ? district.sortOrder : index,
    isActive: district.isActive !== false,
  }));
}

function shortName(region: GeoRegion) {
  return region.displayName || defaultRegionPosition(region.region).short || region.region.replace(/ область$/i, "");
}

function activeTone(active?: boolean) {
  return active === false ? "text-amber-600 dark:text-amber-300" : "text-emerald-600 dark:text-emerald-400";
}

export function RegionsEditor({ mobile = false }: { mobile?: boolean }) {
  const { geo, addRegion, deleteRegion, updateRegion, resetGeo } = useStore();
  const reduce = useReducedMotion();
  const mapRef = useRef<HTMLDivElement>(null);
  const dragId = useRef<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editLayout, setEditLayout] = useState(false);
  const [positions, setPositions] = useState<Record<string, Position>>({});
  const [error, setError] = useState("");

  const sortedGeo = useMemo(
    () => [...geo].sort((a, b) => (a.mapLabelOrder ?? 999) - (b.mapLabelOrder ?? 999) || a.region.localeCompare(b.region, "ru")),
    [geo],
  );
  const activeGeo = sortedGeo.filter((region) => region.isActive !== false);
  const archivedGeo = sortedGeo.filter((region) => region.isActive === false);
  const selected = useMemo(
    () => sortedGeo.find((r) => regionKey(r) === selectedId || r.region === selectedId) ?? null,
    [selectedId, sortedGeo],
  );

  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [center, setCenter] = useState("");
  const [mapX, setMapX] = useState(0);
  const [mapY, setMapY] = useState(0);
  const [visible, setVisible] = useState(true);
  const [isActive, setIsActive] = useState(true);
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    if (!selected) return;
    setName(selected.region);
    setDisplayName(selected.displayName || shortName(selected));
    setCenter(selected.region_center || "");
    setMapX(clampMapPercent(selected.mapLabelX, defaultRegionPosition(selected.region).x));
    setMapY(clampMapPercent(selected.mapLabelY, defaultRegionPosition(selected.region).y));
    setVisible(selected.mapLabelVisible !== false);
    setIsActive(selected.isActive !== false);
    setRows(toRows(selected));
    setError("");
  }, [selected]);

  useEffect(() => {
    if (!editLayout) return;
    const next: Record<string, Position> = {};
    activeGeo.forEach((region, index) => {
      const fallback = defaultRegionPosition(region.region, index);
      next[regionKey(region)] = {
        x: clampMapPercent(region.mapLabelX, fallback.x),
        y: clampMapPercent(region.mapLabelY, fallback.y),
      };
    });
    setPositions(next);
  }, [editLayout]);

  useEffect(() => {
    if (!selectedId) return;
    const exists = sortedGeo.some((region) => regionKey(region) === selectedId || region.region === selectedId);
    if (!exists) setSelectedId(null);
  }, [selectedId, sortedGeo]);

  const draftDistricts = rows
    .filter((row) => row.name.trim())
    .map((row, index) => ({
      id: row.id,
      name: row.name.trim(),
      center: row.center.trim() || undefined,
      sortOrder: index,
      isActive: row.isActive,
    }));

  const dirty = !!selected && (
    name !== selected.region ||
    displayName !== (selected.displayName || shortName(selected)) ||
    center !== (selected.region_center || "") ||
    mapX !== clampMapPercent(selected.mapLabelX, defaultRegionPosition(selected.region).x) ||
    mapY !== clampMapPercent(selected.mapLabelY, defaultRegionPosition(selected.region).y) ||
    visible !== (selected.mapLabelVisible !== false) ||
    isActive !== (selected.isActive !== false) ||
    JSON.stringify(draftDistricts.map((d) => ({ name: d.name, center: d.center || "", isActive: d.isActive }))) !==
      JSON.stringify((selected.districts || []).map((d) => ({ name: d.name, center: d.center || "", isActive: d.isActive !== false })))
  );

  const validate = () => {
    const cleanName = name.trim();
    if (!cleanName) return "Название региона не может быть пустым.";
    const duplicateRegion = sortedGeo.some((region) => regionKey(region) !== regionKey(selected || region) && region.region.toLowerCase() === cleanName.toLowerCase());
    if (duplicateRegion) return "Регион с таким названием уже есть.";
    const districtNames = draftDistricts.map((district) => district.name.toLowerCase());
    if (new Set(districtNames).size !== districtNames.length) return "Внутри региона есть районы с одинаковым названием.";
    if (mapX < 0 || mapX > 100 || mapY < 0 || mapY > 100) return "Координаты карточки должны быть от 0 до 100.";
    return "";
  };

  const save = () => {
    if (!selected) return;
    const validation = validate();
    if (validation) {
      setError(validation);
      return;
    }
    const next: GeoRegion = {
      ...selected,
      region: name.trim(),
      displayName: displayName.trim() || name.trim(),
      region_center: center.trim(),
      districts: draftDistricts,
      mapLabelX: clampMapPercent(mapX, 50),
      mapLabelY: clampMapPercent(mapY, 50),
      mapLabelVisible: visible,
      isActive,
    };
    updateRegion(selected.region, next);
    setSelectedId(next.id || next.region);
    setError("");
  };

  const resetDraft = () => {
    if (!selected) return;
    setName(selected.region);
    setDisplayName(selected.displayName || shortName(selected));
    setCenter(selected.region_center || "");
    setMapX(clampMapPercent(selected.mapLabelX, defaultRegionPosition(selected.region).x));
    setMapY(clampMapPercent(selected.mapLabelY, defaultRegionPosition(selected.region).y));
    setVisible(selected.mapLabelVisible !== false);
    setIsActive(selected.isActive !== false);
    setRows(toRows(selected));
    setError("");
  };

  const close = () => {
    if (dirty && !window.confirm("Закрыть без сохранения? Изменения будут потеряны.")) return;
    setSelectedId(null);
    setError("");
  };

  const addRow = () => setRows((prev) => [...prev, { id: `d${RID++}`, name: "", center: "", sortOrder: prev.length, isActive: true }]);
  const patchRow = (id: string, key: "name" | "center", value: string) => setRows((prev) => prev.map((row) => row.id === id ? { ...row, [key]: value } : row));
  const toggleRow = (id: string) => setRows((prev) => prev.map((row) => row.id === id ? { ...row, isActive: !row.isActive } : row));
  const delRow = (id: string) => setRows((prev) => prev.filter((row) => row.id !== id));

  const onAddRegion = () => {
    const region = window.prompt("Название нового региона");
    const clean = region?.trim();
    if (!clean) return;
    if (sortedGeo.some((item) => item.region.toLowerCase() === clean.toLowerCase())) {
      window.alert("Регион с таким названием уже есть.");
      return;
    }
    addRegion(clean);
    setSelectedId(clean);
  };

  const onArchiveRegion = () => {
    if (!selected) return;
    if (window.confirm(`Архивировать регион «${selected.region}»? Он останется в списке, но будет помечен как неактивный.`)) {
      deleteRegion(selected.region);
      setSelectedId(null);
    }
  };

  const onResetAll = () => {
    if (window.confirm("Восстановить стандартные регионы Беларуси? Пользовательские правки гео-справочника будут сброшены.")) {
      resetGeo();
      setSelectedId(null);
      setEditLayout(false);
    }
  };

  const setPointerPosition = (id: string, clientX: number, clientY: number) => {
    const rect = mapRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = clampMapPercent(((clientX - rect.left) / rect.width) * 100, 50);
    const y = clampMapPercent(((clientY - rect.top) / rect.height) * 100, 50);
    setPositions((prev) => ({ ...prev, [id]: { x, y } }));
  };

  const savePositions = () => {
    activeGeo.forEach((region) => {
      const pos = positions[regionKey(region)];
      if (!pos) return;
      updateRegion(region.region, { ...region, mapLabelX: pos.x, mapLabelY: pos.y, mapLabelVisible: true });
    });
    setEditLayout(false);
  };

  const resetPositions = () => {
    const next: Record<string, Position> = {};
    activeGeo.forEach((region, index) => {
      const fallback = defaultRegionPosition(region.region, index);
      next[regionKey(region)] = { x: fallback.x, y: fallback.y };
    });
    setPositions(next);
  };

  const map = (
    <div className="flex min-h-0 flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">География сервиса</div>
          <div className="text-[18px] tracking-tight text-black dark:text-white">Карта Беларуси</div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button onClick={onAddRegion} className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-black/10 px-3 text-[12px] tracking-tight text-black/70 transition-colors hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70">
            <Plus size={14} /> Регион
          </button>
          <button onClick={() => setEditLayout((prev) => !prev)} className={`inline-flex h-9 items-center gap-1.5 rounded-xl px-3 text-[12px] tracking-tight transition-colors ${editLayout ? "bg-[#0056FF] text-white" : "border border-black/10 text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70"}`}>
            <Move size={14} /> Расположение
          </button>
        </div>
      </div>

      {editLayout && (
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-[#0056FF]/20 bg-[#E3E7FC]/60 p-2 dark:border-[#7FA8FF]/20 dark:bg-[#0E1A3A]">
          <span className="px-2 text-[12px] tracking-tight text-[#0056FF] dark:text-[#7FA8FF]">Перетащите карточки на карте и сохраните позицию.</span>
          <button onClick={savePositions} className="inline-flex h-8 items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 text-[12px] tracking-tight text-white"><Save size={13} /> Сохранить</button>
          <button onClick={resetPositions} className="inline-flex h-8 items-center gap-1.5 rounded-xl px-3 text-[12px] tracking-tight text-black/60 hover:bg-black/[0.04] dark:text-white/60 dark:hover:bg-white/[0.06]"><RotateCcw size={13} /> Сбросить</button>
          <button onClick={() => setEditLayout(false)} className="inline-flex h-8 items-center rounded-xl px-3 text-[12px] tracking-tight text-black/45 hover:bg-black/[0.04] dark:text-white/45 dark:hover:bg-white/[0.06]">Отменить</button>
        </div>
      )}

      <div
        ref={mapRef}
        className="relative min-h-[420px] flex-1 overflow-hidden rounded-[28px] border border-black/[0.06] bg-white shadow-[0_18px_70px_-45px_rgba(15,23,42,0.55)] dark:border-white/[0.06] dark:bg-[#0F1117]"
        style={{
          backgroundImage: "url(/belarus.svg)",
          backgroundSize: "contain",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      >
        {activeGeo.map((region, index) => {
          if (region.mapLabelVisible === false) return null;
          const id = regionKey(region);
          const fallback = defaultRegionPosition(region.region, index);
          const pos = editLayout && positions[id]
            ? positions[id]
            : { x: clampMapPercent(region.mapLabelX, fallback.x), y: clampMapPercent(region.mapLabelY, fallback.y) };
          const active = selected && regionKey(selected) === id;
          return (
            <motion.button
              key={id}
              onClick={() => !editLayout && setSelectedId(id)}
              onPointerDown={(event) => {
                if (!editLayout) return;
                dragId.current = id;
                event.currentTarget.setPointerCapture(event.pointerId);
                setPointerPosition(id, event.clientX, event.clientY);
              }}
              onPointerMove={(event) => {
                if (!editLayout || dragId.current !== id) return;
                setPointerPosition(id, event.clientX, event.clientY);
              }}
              onPointerUp={() => { dragId.current = null; }}
              style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
              className={`absolute -translate-x-1/2 -translate-y-1/2 outline-none ${editLayout ? "touch-none cursor-grab active:cursor-grabbing" : ""}`}
              whileHover={reduce || editLayout ? undefined : { scale: 1.05 }}
              whileTap={reduce ? undefined : { scale: 0.97 }}
            >
              <span className={`flex min-w-[104px] flex-col items-center gap-0.5 rounded-2xl border px-3 py-2 text-center shadow-[0_10px_26px_-14px_rgba(15,23,42,0.65)] backdrop-blur transition-colors ${active ? "border-[#0056FF] bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "border-black/[0.06] bg-white/90 text-black hover:bg-white dark:border-white/[0.08] dark:bg-[#0B0D13]/90 dark:text-white"}`}>
                <span className="text-[12px] font-medium leading-none tracking-tight">{shortName(region)}</span>
                <span className="text-[10px] leading-none tracking-tight opacity-55">{region.districts.filter((d) => d.isActive !== false).length} р-нов</span>
              </span>
            </motion.button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {activeGeo.filter((region) => region.mapLabelVisible === false).map((region) => (
          <button key={regionKey(region)} onClick={() => setSelectedId(regionKey(region))} className="inline-flex items-center gap-1.5 rounded-full bg-[#F6F7FB] px-3 py-1.5 text-[12px] tracking-tight text-black/55 dark:bg-white/[0.05] dark:text-white/55">
            <EyeOff size={12} /> {region.region}
          </button>
        ))}
      </div>
    </div>
  );

  const regionList = (
    <div className="space-y-2">
      {activeGeo.map((region) => {
        const active = selected && regionKey(selected) === regionKey(region);
        return (
          <button key={regionKey(region)} onClick={() => setSelectedId(regionKey(region))} className={`w-full rounded-2xl border px-3 py-3 text-left transition-colors ${active ? "border-[#0056FF] bg-[#E3E7FC] dark:bg-[#0E1A3A]" : "border-black/[0.06] bg-white hover:bg-black/[0.02] dark:border-white/[0.08] dark:bg-white/[0.03] dark:hover:bg-white/[0.06]"}`}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate text-[14px] font-medium tracking-tight text-black dark:text-white">{region.region}</div>
                <div className="mt-0.5 truncate text-[12px] tracking-tight text-black/45 dark:text-white/45">Центр: {region.region_center || "не указан"}</div>
              </div>
              <span className="shrink-0 rounded-full bg-black/[0.04] px-2 py-1 text-[11px] tracking-tight text-black/45 dark:bg-white/[0.06] dark:text-white/45">{region.districts.filter((d) => d.isActive !== false).length}</span>
            </div>
          </button>
        );
      })}
      {archivedGeo.length > 0 && (
        <div className="pt-3">
          <div className="mb-2 text-[11px] uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Архив</div>
          {archivedGeo.map((region) => (
            <button key={regionKey(region)} onClick={() => setSelectedId(regionKey(region))} className="mb-2 w-full rounded-2xl border border-amber-500/20 bg-amber-500/[0.04] px-3 py-3 text-left text-[13px] tracking-tight text-black/60 dark:text-white/60">
              {region.region}
            </button>
          ))}
        </div>
      )}
    </div>
  );

  const inspector = (
    <div className="flex h-full min-h-0 flex-col rounded-[24px] border border-black/[0.06] bg-white dark:border-white/[0.06] dark:bg-[#0F1117]">
      <div className="flex shrink-0 items-center justify-between gap-3 border-b border-black/[0.06] px-4 py-3 dark:border-white/[0.06]">
        <div>
          <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{selected ? "Инспектор региона" : "Список регионов"}</div>
          <div className="text-[17px] tracking-tight text-black dark:text-white">{selected ? selected.region : `${activeGeo.length} активных регионов`}</div>
        </div>
        {selected && <button onClick={close} className="grid h-9 w-9 place-items-center rounded-xl text-black/45 hover:bg-black/[0.04] dark:text-white/45 dark:hover:bg-white/[0.06]"><X size={17} /></button>}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4 [&::-webkit-scrollbar]:hidden">
        {!selected ? (
          <>
            <div className="mb-3 flex items-center gap-2">
              <button onClick={onAddRegion} className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 text-[12px] tracking-tight text-white"><Plus size={14} /> Добавить регион</button>
              <button onClick={onResetAll} className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-black/10 px-3 text-[12px] tracking-tight text-black/55 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/55 dark:hover:bg-white/[0.06]"><RotateCcw size={14} /> Восстановить</button>
            </div>
            {regionList}
          </>
        ) : (
          <div className="space-y-4">
            {error && <div className="rounded-2xl border border-red-500/20 bg-red-500/[0.06] px-3 py-2 text-[12px] tracking-tight text-red-600 dark:text-red-300">{error}</div>}
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="space-y-1.5 sm:col-span-2"><div className={labelCls}>Название региона</div><input className={inputCls} value={name} onChange={(e) => setName(e.target.value)} /></label>
              <label className="space-y-1.5"><div className={labelCls}>Название на карте</div><input className={inputCls} value={displayName} onChange={(e) => setDisplayName(e.target.value)} /></label>
              <label className="space-y-1.5"><div className={labelCls}>Главный город</div><input className={inputCls} value={center} onChange={(e) => setCenter(e.target.value)} /></label>
              <label className="space-y-1.5"><div className={labelCls}>Карта X, %</div><input className={inputCls} type="number" min={0} max={100} value={mapX} onChange={(e) => setMapX(clampMapPercent(e.target.value, mapX))} /></label>
              <label className="space-y-1.5"><div className={labelCls}>Карта Y, %</div><input className={inputCls} type="number" min={0} max={100} value={mapY} onChange={(e) => setMapY(clampMapPercent(e.target.value, mapY))} /></label>
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              <button onClick={() => setVisible((prev) => !prev)} className="rounded-xl border border-black/10 px-3 py-2 text-left text-[13px] tracking-tight text-black/65 dark:border-white/12 dark:text-white/65">Карточка на карте: <span className={activeTone(visible)}>{visible ? "видна" : "скрыта"}</span></button>
              <button onClick={() => setIsActive((prev) => !prev)} className="rounded-xl border border-black/10 px-3 py-2 text-left text-[13px] tracking-tight text-black/65 dark:border-white/12 dark:text-white/65">Статус: <span className={activeTone(isActive)}>{isActive ? "активен" : "архив"}</span></button>
            </div>

            <div className="flex items-center justify-between gap-2">
              <div className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/60 dark:text-white/60"><List size={14} /> Районы · {rows.filter((r) => r.isActive).length}</div>
              <button onClick={addRow} className="inline-flex h-8 items-center gap-1.5 rounded-xl border border-black/10 px-2.5 text-[12px] tracking-tight text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70"><Plus size={13} /> Район</button>
            </div>

            <div className="space-y-2">
              {rows.length === 0 && <div className="rounded-xl border border-dashed border-black/10 px-3 py-6 text-center text-[12px] tracking-tight text-black/40 dark:border-white/12 dark:text-white/35">Районов пока нет.</div>}
              {rows.map((row) => (
                <div key={row.id} className={`grid gap-2 rounded-2xl border p-2 sm:grid-cols-[1fr_1fr_auto_auto] ${row.isActive ? "border-black/[0.06] dark:border-white/[0.08]" : "border-amber-500/20 bg-amber-500/[0.04]"}`}>
                  <input value={row.name} onChange={(e) => patchRow(row.id, "name", e.target.value)} placeholder="Район" className={inputCls} />
                  <input value={row.center} onChange={(e) => patchRow(row.id, "center", e.target.value)} placeholder="Город / центр" className={inputCls} />
                  <button onClick={() => toggleRow(row.id)} className="rounded-xl px-3 text-[12px] tracking-tight text-black/55 hover:bg-black/[0.04] dark:text-white/55 dark:hover:bg-white/[0.06]">{row.isActive ? "Архив" : "Вернуть"}</button>
                  <button onClick={() => delRow(row.id)} className="grid h-9 w-9 place-items-center rounded-xl text-black/35 hover:bg-red-500/10 hover:text-red-500 dark:text-white/35"><Trash2 size={15} /></button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {selected && (
        <div className="flex shrink-0 items-center justify-between gap-2 border-t border-black/[0.06] p-3 dark:border-white/[0.06]" style={{ paddingBottom: mobile ? "max(0.75rem, env(safe-area-inset-bottom))" : undefined }}>
          <button onClick={onArchiveRegion} className="inline-flex items-center gap-1.5 rounded-xl px-2.5 py-2 text-[12px] tracking-tight text-red-500 hover:bg-red-500/10"><Trash2 size={14} /> Архивировать</button>
          <div className="flex items-center gap-2">
            {dirty && <button onClick={resetDraft} className="inline-flex h-9 items-center rounded-xl px-3 text-[13px] tracking-tight text-black/55 hover:bg-black/[0.04] dark:text-white/55 dark:hover:bg-white/[0.06]">Отменить</button>}
            <button onClick={save} disabled={!dirty} className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#0056FF] px-4 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px] disabled:opacity-40"><Check size={15} /> Сохранить</button>
          </div>
        </div>
      )}
    </div>
  );

  const mobileSheet = (
    <AnimatePresence>
      {mobile && selected && (
        <>
          <motion.div className="absolute inset-0 z-[60] bg-black/35 backdrop-blur-[2px]" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={close} />
          <motion.div className="absolute inset-x-0 bottom-0 z-[61] mx-auto max-h-[86%] w-full max-w-[680px] overflow-hidden rounded-t-[28px] shadow-[0_-30px_80px_-30px_rgba(15,23,42,0.5)]" initial={reduce ? { opacity: 0 } : { y: "100%" }} animate={reduce ? { opacity: 1 } : { y: 0 }} exit={reduce ? { opacity: 0 } : { y: "100%" }} transition={{ type: "spring", stiffness: 280, damping: 32 }}>
            {inspector}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );

  if (mobile) {
    return (
      <div className="relative min-h-[70vh] overflow-hidden">
        {map}
        {!selected && <div className="mt-4">{inspector}</div>}
        {mobileSheet}
      </div>
    );
  }

  return (
    <div className="grid h-full min-h-[640px] gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
      {map}
      {inspector}
    </div>
  );
}
