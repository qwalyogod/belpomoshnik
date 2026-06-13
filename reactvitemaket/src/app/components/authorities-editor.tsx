import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { Plus, Trash2, Check, X, Building2, MapPin, Phone, Clock, Globe, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { useStore } from "../data/store";
import type { Institution } from "../data/types";
import { Card } from "./belp-ui";

type Draft = {
  name: string;
  address: string;
  hours: string;
  phone: string;
  region: string;
  district: string;
  city: string;
  settlement: string;
  type: string;
  email: string;
  websiteUrl: string;
};

const EMPTY: Draft = {
  name: "",
  address: "",
  hours: "",
  phone: "",
  region: "",
  district: "",
  city: "",
  settlement: "",
  type: "",
  email: "",
  websiteUrl: "",
};

const inp =
  "w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-[14px] tracking-tight text-black outline-none transition-colors placeholder:text-black/30 focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/25";
const lbl = "block mb-1 text-[12px] tracking-tight text-black/55 dark:text-white/55";

// ─────────────────────────────────────────────────────────────────────────────
// Регионы: 7 фиксированных корзин. Город Минск — отдельно от Минской области;
// у каждой области в одном списке и областной центр, и районы.
// ─────────────────────────────────────────────────────────────────────────────
const REGION_BUCKETS = [
  "Минск",
  "Минская область",
  "Брестская область",
  "Гродненская область",
  "Гомельская область",
  "Могилёвская область",
  "Витебская область",
] as const;

/** Приводит произвольное значение region из данных к одной из 7 корзин. */
function canonicalRegion(region?: string): string {
  const n = (region || "").toLowerCase().replace(/ё/g, "е").trim();
  if (!n) return "Без региона";
  // «Минская область» проверяем ДО города Минска.
  if (n.includes("минск") && n.includes("област")) return "Минская область";
  if (n === "минск" || n.includes("город минск") || n.replace(/[.\s]/g, "") === "гминск") return "Минск";
  if (n.includes("брест")) return "Брестская область";
  if (n.includes("гродн")) return "Гродненская область";
  if (n.includes("гомел")) return "Гомельская область";
  if (n.includes("могил")) return "Могилёвская область";
  if (n.includes("витеб")) return "Витебская область";
  return (region || "").trim() || "Без региона";
}

function toDraft(a: Institution): Draft {
  return {
    name: a.name,
    address: a.address,
    hours: a.hours ?? "",
    phone: a.phone ?? "",
    region: a.region ?? "",
    district: a.district ?? "",
    city: a.city ?? "",
    settlement: a.settlement ?? "",
    type: a.type ?? "",
    email: a.email ?? "",
    websiteUrl: a.websiteUrl ?? "",
  };
}

export function AuthoritiesEditor({ mobile = false }: { mobile?: boolean }) {
  const { authorities, addAuthority, updateAuthority, deleteAuthority } = useStore();
  const reduce = useReducedMotion();
  const [region, setRegion] = useState<string | null>(null);
  const [sel, setSel] = useState<string | "new" | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [search, setSearch] = useState("");

  // Группировка по регионам + счётчики.
  const byRegion = useMemo(() => {
    const m = new Map<string, number>();
    for (const a of authorities) {
      const k = canonicalRegion(a.region);
      m.set(k, (m.get(k) || 0) + 1);
    }
    return m;
  }, [authorities]);

  // Карточки регионов: сначала 7 известных в нужном порядке, затем прочие.
  const regionCards = useMemo(() => {
    const known = REGION_BUCKETS.filter((r) => byRegion.has(r)).map((r) => ({ key: r as string, count: byRegion.get(r)! }));
    const extras = [...byRegion.keys()]
      .filter((k) => !(REGION_BUCKETS as readonly string[]).includes(k))
      .sort()
      .map((k) => ({ key: k, count: byRegion.get(k)! }));
    return [...known, ...extras];
  }, [byRegion]);

  const selected = useMemo(
    () => (sel && sel !== "new" ? authorities.find((a) => a.id === sel) ?? null : null),
    [authorities, sel],
  );

  // Для редактирования существующего — подставляем его данные в форму.
  // Для "new" форму заполняет openNew() (с предзаполненным регионом).
  useEffect(() => {
    if (selected) setDraft(toDraft(selected));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel]);

  const dirty = useMemo(() => {
    if (sel === "new") return draft.name.trim().length > 0;
    if (!selected) return false;
    return JSON.stringify(draft) !== JSON.stringify(toDraft(selected));
  }, [draft, sel, selected]);

  // Учреждения выбранного региона + поиск внутри него.
  const regionItems = useMemo(
    () => (region ? authorities.filter((a) => canonicalRegion(a.region) === region) : []),
    [authorities, region],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return regionItems;
    return regionItems.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        (a.type ?? "").toLowerCase().includes(q) ||
        (a.district ?? "").toLowerCase().includes(q) ||
        (a.city ?? "").toLowerCase().includes(q) ||
        (a.settlement ?? "").toLowerCase().includes(q) ||
        (a.address ?? "").toLowerCase().includes(q),
    );
  }, [regionItems, search]);

  const openNew = () => {
    setDraft({ ...EMPTY, region: region && (REGION_BUCKETS as readonly string[]).includes(region) ? region : "" });
    setSel("new");
  };

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
      district: draft.district.trim() || undefined,
      city: draft.city.trim() || undefined,
      settlement: draft.settlement.trim() || undefined,
      type: draft.type.trim() || undefined,
      email: draft.email.trim() || undefined,
      websiteUrl: draft.websiteUrl.trim() || undefined,
    };
    if (sel === "new") addAuthority(item);
    else if (selected) updateAuthority(selected.id, item);
    setSel(null);
  };

  const pf = (k: keyof Draft, v: string) => setDraft((prev) => ({ ...prev, [k]: v }));

  const enterRegion = (key: string) => {
    setRegion(key);
    setSearch("");
  };

  // ── Форма (общая для desktop-модалки и mobile-шита) ────────────────────────
  const formHeader = (
    <div className="flex items-center justify-between gap-2 px-5 pt-4 pb-3">
      <span className="inline-flex items-center gap-1.5 text-[14px] tracking-tight text-black/70 dark:text-white/70">
        <Building2 size={15} className="text-[#0056FF]" />
        {sel === "new" ? "Новое учреждение" : "Редактирование учреждения"}
      </span>
      <button
        onClick={close}
        className="grid h-8 w-8 place-items-center rounded-lg text-black/45 transition-colors hover:bg-black/[0.05] dark:text-white/45 dark:hover:bg-white/[0.07]"
      >
        <X size={17} />
      </button>
    </div>
  );

  const formBody = (
    <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 pb-2 [&::-webkit-scrollbar]:hidden">
      <div>
        <label className={lbl}>Название учреждения</label>
        <div className="relative">
          <Building2 size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35" />
          <input value={draft.name} onChange={(e) => pf("name", e.target.value)} placeholder="РОВД Первомайского района" className={`${inp} pl-9 text-[15px] font-medium`} />
        </div>
      </div>

      <div>
        <label className={lbl}>Адрес</label>
        <div className="relative">
          <MapPin size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35" />
          <input value={draft.address} onChange={(e) => pf("address", e.target.value)} placeholder="ул. Ленина, 10, Минск" className={`${inp} pl-9`} />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className={lbl}>Регион</label>
          <input value={draft.region} onChange={(e) => pf("region", e.target.value)} placeholder="Минская область" className={inp} />
        </div>
        <div>
          <label className={lbl}>Район</label>
          <input value={draft.district} onChange={(e) => pf("district", e.target.value)} placeholder="Барановичский район" className={inp} />
        </div>
        <div>
          <label className={lbl}>Город</label>
          <input value={draft.city} onChange={(e) => pf("city", e.target.value)} placeholder="Минск" className={inp} />
        </div>
        <div>
          <label className={lbl}>Населённый пункт</label>
          <input value={draft.settlement} onChange={(e) => pf("settlement", e.target.value)} placeholder="Барановичи" className={inp} />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className={lbl}>Тип учреждения</label>
          <input value={draft.type} onChange={(e) => pf("type", e.target.value)} placeholder="citizenship_migration" className={inp} />
        </div>
        <div>
          <label className={lbl}>Email</label>
          <input value={draft.email} onChange={(e) => pf("email", e.target.value)} placeholder="info@example.by" className={inp} />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className={lbl}>Телефон</label>
          <div className="relative">
            <Phone size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35" />
            <input value={draft.phone} onChange={(e) => pf("phone", e.target.value)} placeholder="+375 17 200-00-00" className={`${inp} pl-9`} />
          </div>
        </div>
        <div>
          <label className={lbl}>Часы работы</label>
          <div className="relative">
            <Clock size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35" />
            <input value={draft.hours} onChange={(e) => pf("hours", e.target.value)} placeholder="Пн-Пт 9:00-18:00" className={`${inp} pl-9`} />
          </div>
        </div>
      </div>

      <div>
        <label className={lbl}>Сайт</label>
        <div className="relative">
          <Globe size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35" />
          <input value={draft.websiteUrl} onChange={(e) => pf("websiteUrl", e.target.value)} placeholder="https://example.gov.by/" className={`${inp} pl-9`} />
        </div>
      </div>
    </div>
  );

  const formFooter = (
    <div
      className="flex shrink-0 items-center justify-between gap-2 border-t border-black/[0.06] p-3 px-5 dark:border-white/[0.06]"
      style={{ paddingBottom: mobile ? "max(0.75rem, env(safe-area-inset-bottom))" : undefined }}
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
        <button onClick={close} className="inline-flex h-9 items-center rounded-xl px-3 text-[13px] tracking-tight text-black/55 transition-colors hover:bg-black/[0.04] dark:text-white/55">
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
  );

  // Модалка/шит рендерится в портал (document.body) — поэтому позиционируется
  // относительно вьюпорта, а не растущего списка. На desktop — центр экрана,
  // на mobile — нижний sheet.
  const formPortal = createPortal(
    <AnimatePresence>
      {sel && [
        <motion.div
          key="overlay"
          className="fixed inset-0 z-[200] bg-black/45 backdrop-blur-[2px]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={close}
        />,
        mobile ? (
          <motion.div
            key="sheet"
            className="fixed inset-x-0 bottom-0 z-[201] mx-auto flex max-h-[88%] w-full max-w-[680px] flex-col rounded-t-[28px] border border-b-0 border-black/[0.06] bg-white shadow-[0_-30px_80px_-30px_rgba(15,23,42,0.5)] dark:border-white/[0.08] dark:bg-[#0F1117]"
            initial={reduce ? { opacity: 0 } : { y: "100%" }}
            animate={reduce ? { opacity: 1 } : { y: 0 }}
            exit={reduce ? { opacity: 0 } : { y: "100%" }}
            transition={{ type: "spring", stiffness: 280, damping: 32 }}
          >
            <div className="mx-auto mb-1 mt-2.5 h-1 w-10 rounded-full bg-black/15 dark:bg-white/20" />
            {formHeader}
            {formBody}
            {formFooter}
          </motion.div>
        ) : (
          <motion.div key="modal" className="fixed inset-0 z-[201] grid place-items-center p-6" onClick={close}>
            <motion.div
              className="flex max-h-[88vh] w-full max-w-[720px] flex-col overflow-hidden rounded-3xl border border-black/[0.06] bg-white shadow-[0_40px_120px_-30px_rgba(15,23,42,0.55)] dark:border-white/[0.08] dark:bg-[#0F1117]"
              initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: 10 }}
              animate={reduce ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
              exit={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.97, y: 6 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              onClick={(e) => e.stopPropagation()}
            >
              {formHeader}
              {formBody}
              {formFooter}
            </motion.div>
          </motion.div>
        ),
      ]}
    </AnimatePresence>,
    document.body,
  );

  // ── Вид 1: выбор региона ───────────────────────────────────────────────────
  if (region === null) {
    return (
      <div className={mobile ? "min-h-[60vh]" : "min-h-[400px]"}>
        <div className="mb-1 flex items-baseline justify-between gap-2">
          <div className="text-[15px] font-medium tracking-tight text-black dark:text-white">Учреждения по регионам</div>
          <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">
            {authorities.length} в {regionCards.length} {regionCards.length === 1 ? "регионе" : "регионах"}
          </div>
        </div>
        <div className="mb-4 text-[12px] tracking-tight text-black/50 dark:text-white/50">
          Выберите область — внутри будет список всех её гос. учреждений (областной центр, города и районы вместе).
        </div>

        {regionCards.length === 0 ? (
          <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
            <div>
              <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <Building2 size={20} />
              </div>
              <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>Учреждений нет</div>
              <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">
                Проверьте подключение к серверу — список приходит из API.
              </div>
            </div>
          </div>
        ) : (
          <div className={`grid gap-3 ${mobile ? "grid-cols-1" : "sm:grid-cols-2 lg:grid-cols-3"}`}>
            {regionCards.map(({ key, count }) => (
              <button
                key={key}
                onClick={() => enterRegion(key)}
                className="group flex items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3.5 text-left shadow-[0_8px_24px_-18px_rgba(15,23,42,0.25)] transition-all hover:-translate-y-0.5 hover:border-[#0056FF]/30 hover:shadow-[0_16px_36px_-20px_rgba(0,86,255,0.4)] active:translate-y-0 dark:border-white/[0.06] dark:bg-[#0F1117]"
              >
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                  <Building2 size={18} />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[14px] font-medium tracking-tight text-black dark:text-white">{key}</span>
                  <span className="block text-[12px] tracking-tight text-black/45 dark:text-white/45">{count} учреждений</span>
                </span>
                <ChevronRight size={16} className="shrink-0 text-black/25 transition-colors group-hover:text-[#0056FF] dark:text-white/25" />
              </button>
            ))}
          </div>
        )}
        {formPortal}
      </div>
    );
  }

  // ── Вид 2: список учреждений выбранного региона ────────────────────────────
  return (
    <div className={mobile ? "min-h-[60vh]" : "min-h-[400px]"}>
      {/* breadcrumb + back */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button
          onClick={() => { setRegion(null); setSearch(""); }}
          className="inline-flex items-center gap-1 rounded-xl border border-black/[0.06] bg-[#F6F7FB] px-2.5 py-2 text-[13px] tracking-tight text-black/70 transition-colors hover:bg-black/[0.05] dark:border-white/[0.06] dark:bg-white/[0.04] dark:text-white/70"
        >
          <ChevronLeft size={15} /> Регионы
        </button>
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-black/[0.06] bg-[#F6F7FB] px-3 py-2 dark:border-white/[0.06] dark:bg-white/[0.04]">
          <Search size={14} className="shrink-0 text-black/40 dark:text-white/40" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Поиск в «${region}»...`}
            className="flex-1 bg-transparent text-[13px] tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40"
          />
        </div>
        <button
          onClick={openNew}
          className="inline-flex items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 py-2 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"
        >
          <Plus size={14} /> Добавить
        </button>
      </div>

      <div className="mb-3 flex items-center gap-2 text-[13px] tracking-tight">
        <span className="font-medium text-black dark:text-white">{region}</span>
        <span className="text-black/45 dark:text-white/45">· {filtered.length} из {regionItems.length}</span>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-black/10 p-8 text-center text-[13px] tracking-tight text-black/45 dark:border-white/12 dark:text-white/45">
          {regionItems.length === 0 ? "В этом регионе учреждений нет." : `Ничего не найдено по запросу «${search}»`}
        </div>
      ) : (
        <Card className="p-0">
          <div className="overflow-x-auto [&::-webkit-scrollbar]:hidden">
            <table className="w-full min-w-[640px]">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-[0.12em] text-black/40 dark:text-white/40">
                  <th className="px-5 py-3">Учреждение</th>
                  <th className="py-3">Тип / город</th>
                  <th className="py-3">Телефон</th>
                  <th className="py-3">Адрес</th>
                  <th className="py-3 pr-5" />
                </tr>
              </thead>
              <tbody className="text-[13px] tracking-tight text-black dark:text-white">
                {filtered.map((a) => (
                  <tr key={a.id} className="border-t border-black/[0.05] dark:border-white/[0.05]">
                    <td className="max-w-[220px] truncate px-5 py-3.5 font-[450]">{a.name}</td>
                    <td className="py-3.5 text-black/65 dark:text-white/65">
                      <div>{a.type || "—"}</div>
                      <div className="text-[11px] text-black/40 dark:text-white/40">{a.city || a.settlement || a.district || "—"}</div>
                    </td>
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
      {formPortal}
    </div>
  );
}
