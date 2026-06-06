import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { MapPin, Plus, Trash2, Check, RotateCcw, Building2, X } from "lucide-react";
import { useStore } from "../data/store";
import type { GeoRegion } from "../data/geo";

/* District draft row with a stable React key (names change while editing). */
type Row = { id: string; name: string; center: string };

/* Approximate centroid of each oblast on the Belarus outline (percent of the
   square map container). Regions without coords are listed as chips below. */
const POS: Record<string, { x: number; y: number; short: string }> = {
  "Витебская область": { x: 58, y: 22, short: "Витебская" },
  "Гродненская область": { x: 27, y: 48, short: "Гродненская" },
  "Минская область": { x: 52, y: 58, short: "Минская" },
  "Могилевская область": { x: 75, y: 47, short: "Могилёвская" },
  "Брестская область": { x: 30, y: 76, short: "Брестская" },
  "Гомельская область": { x: 66, y: 78, short: "Гомельская" },
  "г. Минск": { x: 49, y: 50, short: "Минск" },
};

let RID = 0;
const toRows = (r?: GeoRegion | null): Row[] =>
  (r?.districts ?? []).map((d) => ({ id: `d${RID++}`, name: d.name, center: d.center || "" }));

const inputCls =
  "w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-[14px] tracking-tight text-black outline-none transition-colors placeholder:text-black/30 focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/25";

export function RegionsEditor({ mobile = false }: { mobile?: boolean }) {
  const { geo, addRegion, deleteRegion, updateRegion, resetGeo } = useStore();
  const reduce = useReducedMotion();
  // Default view = map only, nothing open.
  const [sel, setSel] = useState<string | null>(null);

  const selected = useMemo(() => geo.find((r) => r.region === sel) ?? null, [geo, sel]);

  // Local editable draft of the selected region (commit on "Сохранить").
  const [name, setName] = useState("");
  const [center, setCenter] = useState("");
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    setName(selected?.region ?? "");
    setCenter(selected?.region_center ?? "");
    setRows(toRows(selected));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel, selected?.region, selected?.districts.length]);

  // Close the sheet with Escape.
  useEffect(() => {
    if (!sel) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setSel(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sel]);

  const dirty =
    !!selected &&
    (name !== selected.region ||
      center !== (selected.region_center ?? "") ||
      JSON.stringify(rows.map((r) => ({ name: r.name, center: r.center }))) !==
        JSON.stringify(selected.districts.map((d) => ({ name: d.name, center: d.center || "" }))));

  const save = () => {
    if (!selected) return;
    const next: GeoRegion = {
      region: name.trim() || selected.region,
      region_center: center.trim(),
      districts: rows
        .filter((r) => r.name.trim())
        .map((r) => ({ name: r.name.trim(), center: r.center.trim() || undefined })),
    };
    updateRegion(selected.region, next);
    setSel(next.region);
  };
  const resetDraft = () => {
    setName(selected?.region ?? "");
    setCenter(selected?.region_center ?? "");
    setRows(toRows(selected));
  };
  const close = () => {
    if (dirty && !window.confirm("Закрыть без сохранения? Изменения будут потеряны.")) return;
    setSel(null);
  };

  const addRow = () => setRows((p) => [...p, { id: `d${RID++}`, name: "", center: "" }]);
  const patchRow = (id: string, k: "name" | "center", v: string) =>
    setRows((p) => p.map((r) => (r.id === id ? { ...r, [k]: v } : r)));
  const delRow = (id: string) => setRows((p) => p.filter((r) => r.id !== id));

  const onAddRegion = () => {
    const n = window.prompt("Название нового региона");
    if (n && n.trim()) {
      addRegion(n.trim());
      setSel(n.trim());
    }
  };
  const onDeleteRegion = () => {
    if (!selected) return;
    if (window.confirm(`Удалить регион «${selected.region}» и все его районы?`)) {
      deleteRegion(selected.region);
      setSel(null);
    }
  };
  const onResetAll = () => {
    if (window.confirm("Сбросить все регионы и районы к исходным данным? Ваши правки будут потеряны.")) {
      resetGeo();
      setSel(null);
    }
  };

  const offMap = geo.filter((r) => !POS[r.region]);

  /* ---------- map (default view) ---------- */
  const map = (
    <div className="flex flex-col items-center gap-4">
      <div
        className="relative aspect-square w-full max-w-[560px] rounded-[28px] border border-black/[0.06] bg-white dark:border-white/[0.06] dark:bg-[#0F1117]"
        style={{
          backgroundImage: "url(/belarus.svg)",
          backgroundSize: "100%",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      >
        {geo.map((r) => {
          const p = POS[r.region];
          if (!p) return null;
          return (
            <motion.button
              key={r.region}
              onClick={() => setSel(r.region)}
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
              className="absolute -translate-x-1/2 -translate-y-1/2 outline-none"
              whileHover={reduce ? undefined : { scale: 1.06 }}
              whileTap={reduce ? undefined : { scale: 0.96 }}
            >
              <span className="flex flex-col items-center gap-0.5 rounded-2xl bg-white/90 px-3 py-1.5 text-center shadow-[0_8px_22px_-10px_rgba(15,23,42,0.55)] backdrop-blur transition-colors hover:bg-white dark:bg-[#0B0D13]/90 dark:hover:bg-[#0B0D13]">
                <span className="text-[12px] font-medium leading-none tracking-tight text-black dark:text-white">{p.short}</span>
                <span className="text-[10px] leading-none tracking-tight text-black/45 dark:text-white/45">{r.districts.length} р-нов</span>
              </span>
            </motion.button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center justify-center gap-2">
        <button
          onClick={onAddRegion}
          className="inline-flex items-center gap-1.5 rounded-xl border border-black/10 px-3 py-1.5 text-[12px] tracking-tight text-black/70 transition-colors hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70"
        >
          <Plus size={13} /> Регион
        </button>
        <button
          onClick={onResetAll}
          className="inline-flex items-center gap-1.5 rounded-xl border border-black/10 px-3 py-1.5 text-[12px] tracking-tight text-black/55 transition-colors hover:bg-black/[0.04] dark:border-white/12 dark:text-white/55"
        >
          <RotateCcw size={13} /> Сбросить всё
        </button>
      </div>

      {offMap.length > 0 && (
        <div className="flex flex-wrap justify-center gap-1.5">
          {offMap.map((r) => (
            <button
              key={r.region}
              onClick={() => setSel(r.region)}
              className="rounded-full bg-[#E3E7FC] px-2.5 py-1 text-[12px] tracking-tight text-[#0056FF] transition-colors hover:bg-[#d6ddfb] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"
            >
              {r.region}
            </button>
          ))}
        </div>
      )}

      <p className="text-[12px] tracking-tight text-black/40 dark:text-white/40">Нажмите регион, чтобы изменить название и районы.</p>
    </div>
  );

  /* ---------- bottom sheet (region editor) ---------- */
  const sheet = (
    <AnimatePresence>
      {selected && (
        <>
          <motion.div
            className="absolute inset-0 z-[60] bg-black/40 backdrop-blur-[2px]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={close}
          />
          <motion.div
            className="absolute inset-x-0 bottom-0 z-[61] mx-auto flex max-h-[86%] w-full max-w-[680px] flex-col rounded-t-[28px] border border-b-0 border-black/[0.06] bg-white shadow-[0_-30px_80px_-30px_rgba(15,23,42,0.5)] dark:border-white/[0.08] dark:bg-[#0F1117]"
            initial={reduce ? { opacity: 0 } : { y: "100%" }}
            animate={reduce ? { opacity: 1 } : { y: 0 }}
            exit={reduce ? { opacity: 0 } : { y: "100%" }}
            transition={{ type: "spring", stiffness: 280, damping: 32 }}
          >
            {/* grabber + header */}
            <div className="shrink-0 px-4 pt-2.5">
              <div className="mx-auto mb-2 h-1 w-10 rounded-full bg-black/15 dark:bg-white/20" />
              <div className="flex items-center justify-between gap-2 pb-2">
                <span className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/60 dark:text-white/60">
                  <MapPin size={14} className="text-[#0056FF]" /> Редактирование региона
                </span>
                <button
                  onClick={close}
                  className="grid h-8 w-8 place-items-center rounded-lg text-black/45 transition-colors hover:bg-black/[0.05] dark:text-white/45 dark:hover:bg-white/[0.07]"
                  title="Закрыть"
                >
                  <X size={17} />
                </button>
              </div>
            </div>

            {/* scrollable body */}
            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 pb-2 [&::-webkit-scrollbar]:hidden">
              <div className="space-y-3">
                <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Название региона" className={`${inputCls} text-[16px] font-medium`} />
                <div className="relative">
                  <Building2 size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35" />
                  <input value={center} onChange={(e) => setCenter(e.target.value)} placeholder="Административный центр (город)" className={`${inputCls} pl-9`} />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[13px] tracking-tight text-black/60 dark:text-white/60">Районы · {rows.length}</span>
                <button
                  onClick={addRow}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-black/10 px-2.5 py-1 text-[12px] tracking-tight text-black/70 transition-colors hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70"
                >
                  <Plus size={13} /> Район
                </button>
              </div>

              <div className="space-y-2">
                {rows.length === 0 && (
                  <div className="rounded-xl border border-dashed border-black/10 px-3 py-6 text-center text-[12px] tracking-tight text-black/40 dark:border-white/12 dark:text-white/35">
                    Районов пока нет, добавьте кнопкой выше.
                  </div>
                )}
                {rows.map((r) => (
                  <div key={r.id} className="flex items-center gap-2">
                    <input value={r.name} onChange={(e) => patchRow(r.id, "name", e.target.value)} placeholder="Район" className={inputCls} />
                    <input value={r.center} onChange={(e) => patchRow(r.id, "center", e.target.value)} placeholder="Город / центр" className={inputCls} />
                    <button
                      onClick={() => delRow(r.id)}
                      className="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-black/35 transition-colors hover:bg-red-500/10 hover:text-red-500 dark:text-white/35"
                      title="Удалить район"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* footer actions */}
            <div className="flex shrink-0 items-center justify-between gap-2 border-t border-black/[0.06] p-3 dark:border-white/[0.06]"
              style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}>
              <button
                onClick={onDeleteRegion}
                className="inline-flex items-center gap-1.5 rounded-xl px-2.5 py-2 text-[12px] tracking-tight text-red-500 transition-colors hover:bg-red-500/10"
              >
                <Trash2 size={14} /> Удалить регион
              </button>
              <div className="flex items-center gap-2">
                {dirty && (
                  <button onClick={resetDraft} className="inline-flex h-9 items-center rounded-xl px-3 text-[13px] tracking-tight text-black/55 transition-colors hover:bg-black/[0.04] dark:text-white/55">
                    Отменить
                  </button>
                )}
                <button
                  onClick={save}
                  disabled={!dirty}
                  className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#0056FF] px-4 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px] disabled:opacity-40"
                >
                  <Check size={15} /> Сохранить
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );

  return (
    <div className={`relative ${mobile ? "min-h-[70vh]" : "min-h-[560px]"} overflow-hidden`}>
      <div className="pt-2">{map}</div>
      {sheet}
    </div>
  );
}
