import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { Plus, Trash2, Check, X, Building2, MapPin, Phone, Clock } from "lucide-react";
import { useStore } from "../data/store";
import type { Institution } from "../data/types";
import { Card } from "./belp-ui";

type Draft = {
  name: string;
  address: string;
  hours: string;
  phone: string;
  region: string;
  city: string;
};

const EMPTY: Draft = { name: "", address: "", hours: "", phone: "", region: "", city: "" };

const inp =
  "w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-[14px] tracking-tight text-black outline-none transition-colors placeholder:text-black/30 focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/25";
const lbl = "block mb-1 text-[12px] tracking-tight text-black/55 dark:text-white/55";

function toDraft(a: Institution): Draft {
  return {
    name: a.name,
    address: a.address,
    hours: a.hours ?? "",
    phone: a.phone ?? "",
    region: a.region ?? "",
    city: a.city ?? "",
  };
}

export function AuthoritiesEditor({ mobile = false }: { mobile?: boolean }) {
  const { authorities, addAuthority, updateAuthority, deleteAuthority } = useStore();
  const reduce = useReducedMotion();
  const [sel, setSel] = useState<string | "new" | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [search, setSearch] = useState("");

  const selected = useMemo(
    () => (sel && sel !== "new" ? authorities.find((a) => a.id === sel) ?? null : null),
    [authorities, sel],
  );

  useEffect(() => {
    if (sel === "new") { setDraft(EMPTY); return; }
    if (selected) setDraft(toDraft(selected));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel]);

  const dirty = useMemo(() => {
    if (sel === "new") return draft.name.trim().length > 0;
    if (!selected) return false;
    return JSON.stringify(draft) !== JSON.stringify(toDraft(selected));
  }, [draft, sel, selected]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return authorities;
    return authorities.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        (a.city ?? "").toLowerCase().includes(q) ||
        (a.address ?? "").toLowerCase().includes(q),
    );
  }, [authorities, search]);

  const close = () => {
    if (dirty && !window.confirm("Закрыть без сохранения?")) return;
    setSel(null);
  };

  const save = () => {
    const item = {
      name: draft.name.trim() || "Учреждение",
      address: draft.address.trim(),
      hours: draft.hours.trim() || undefined,
      phone: draft.phone.trim() || undefined,
      region: draft.region.trim() || undefined,
      city: draft.city.trim() || undefined,
    };
    if (sel === "new") addAuthority(item);
    else if (selected) updateAuthority(selected.id, item);
    setSel(null);
  };

  const pf = (k: keyof Draft, v: string) => setDraft((prev) => ({ ...prev, [k]: v }));

  return (
    <div className={`relative ${mobile ? "min-h-[70vh]" : "min-h-[400px]"} overflow-hidden`}>
      {/* toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-black/[0.06] bg-[#F6F7FB] px-3 py-2 dark:border-white/[0.06] dark:bg-white/[0.04]">
          <Building2 size={14} className="shrink-0 text-black/40 dark:text-white/40" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск учреждений..."
            className="flex-1 bg-transparent text-[13px] tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40"
          />
        </div>
        <button
          onClick={() => setSel("new")}
          className="inline-flex items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 py-2 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"
        >
          <Plus size={14} /> Добавить
        </button>
      </div>

      {/* count */}
      <div className="mb-3 text-[12px] tracking-tight text-black/45 dark:text-white/45">
        {filtered.length} из {authorities.length} учреждений
      </div>

      {/* table */}
      {authorities.length === 0 ? (
        <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
          <div>
            <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
              <Building2 size={20} />
            </div>
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>
              Учреждений нет
            </div>
            <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">
              Добавьте первое через кнопку выше.
            </div>
          </div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-black/10 p-8 text-center text-[13px] tracking-tight text-black/45 dark:border-white/12 dark:text-white/45">
          Ничего не найдено по запросу «{search}»
        </div>
      ) : (
        <Card className="p-0">
          <div className="overflow-x-auto [&::-webkit-scrollbar]:hidden">
            <table className="w-full min-w-[640px]">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-[0.12em] text-black/40 dark:text-white/40">
                  <th className="px-5 py-3">Учреждение</th>
                  <th className="py-3">Город</th>
                  <th className="py-3">Телефон</th>
                  <th className="py-3">Адрес</th>
                  <th className="py-3 pr-5" />
                </tr>
              </thead>
              <tbody className="text-[13px] tracking-tight text-black dark:text-white">
                {filtered.map((a) => (
                  <tr key={a.id} className="border-t border-black/[0.05] dark:border-white/[0.05]">
                    <td className="max-w-[200px] truncate px-5 py-3.5 font-[450]">{a.name}</td>
                    <td className="py-3.5 text-black/65 dark:text-white/65">{a.city || "—"}</td>
                    <td className="py-3.5 text-black/55 dark:text-white/55">{a.phone || "—"}</td>
                    <td className="max-w-[220px] truncate py-3.5 text-black/50 dark:text-white/50">{a.address || "—"}</td>
                    <td className="whitespace-nowrap py-3.5 pr-5 text-right">
                      <button
                        onClick={() => setSel(a.id)}
                        className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[12px] tracking-tight text-[#0056FF] transition-colors hover:bg-[#0056FF]/[0.08] dark:text-[#7FA8FF]"
                      >
                        Изменить
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* bottom sheet */}
      <AnimatePresence>
        {sel && (
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
                    <Building2 size={14} className="text-[#0056FF]" />
                    {sel === "new" ? "Новое учреждение" : "Редактирование учреждения"}
                  </span>
                  <button
                    onClick={close}
                    className="grid h-8 w-8 place-items-center rounded-lg text-black/45 transition-colors hover:bg-black/[0.05] dark:text-white/45 dark:hover:bg-white/[0.07]"
                  >
                    <X size={17} />
                  </button>
                </div>
              </div>

              {/* form */}
              <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 pb-2 [&::-webkit-scrollbar]:hidden">
                <div>
                  <label className={lbl}>Название учреждения</label>
                  <div className="relative">
                    <Building2
                      size={14}
                      className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35"
                    />
                    <input
                      value={draft.name}
                      onChange={(e) => pf("name", e.target.value)}
                      placeholder="РОВД Первомайского района"
                      className={`${inp} pl-9 text-[15px] font-medium`}
                    />
                  </div>
                </div>

                <div>
                  <label className={lbl}>Адрес</label>
                  <div className="relative">
                    <MapPin
                      size={14}
                      className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35"
                    />
                    <input
                      value={draft.address}
                      onChange={(e) => pf("address", e.target.value)}
                      placeholder="ул. Ленина, 10, Минск"
                      className={`${inp} pl-9`}
                    />
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className={lbl}>Регион</label>
                    <input
                      value={draft.region}
                      onChange={(e) => pf("region", e.target.value)}
                      placeholder="Минская область"
                      className={inp}
                    />
                  </div>
                  <div>
                    <label className={lbl}>Город</label>
                    <input
                      value={draft.city}
                      onChange={(e) => pf("city", e.target.value)}
                      placeholder="Минск"
                      className={inp}
                    />
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className={lbl}>Телефон</label>
                    <div className="relative">
                      <Phone
                        size={14}
                        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35"
                      />
                      <input
                        value={draft.phone}
                        onChange={(e) => pf("phone", e.target.value)}
                        placeholder="+375 17 200-00-00"
                        className={`${inp} pl-9`}
                      />
                    </div>
                  </div>
                  <div>
                    <label className={lbl}>Часы работы</label>
                    <div className="relative">
                      <Clock
                        size={14}
                        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35"
                      />
                      <input
                        value={draft.hours}
                        onChange={(e) => pf("hours", e.target.value)}
                        placeholder="Пн-Пт 9:00-18:00"
                        className={`${inp} pl-9`}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* footer */}
              <div
                className="flex shrink-0 items-center justify-between gap-2 border-t border-black/[0.06] p-3 dark:border-white/[0.06]"
                style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
              >
                {sel !== "new" && selected ? (
                  <button
                    onClick={() => {
                      if (window.confirm(`Удалить учреждение «${selected.name}»?`)) {
                        deleteAuthority(selected.id);
                        setSel(null);
                      }
                    }}
                    className="inline-flex items-center gap-1.5 rounded-xl px-2.5 py-2 text-[12px] tracking-tight text-red-500 transition-colors hover:bg-red-500/10"
                  >
                    <Trash2 size={14} /> Удалить
                  </button>
                ) : (
                  <div />
                )}
                <div className="flex items-center gap-2">
                  <button
                    onClick={close}
                    className="inline-flex h-9 items-center rounded-xl px-3 text-[13px] tracking-tight text-black/55 transition-colors hover:bg-black/[0.04] dark:text-white/55"
                  >
                    Отменить
                  </button>
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
    </div>
  );
}
