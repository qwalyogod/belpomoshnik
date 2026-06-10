import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "motion/react";
import { Plus, Trash2, Check, X, BookOpen, AlertCircle } from "lucide-react";
import { useStore } from "../data/store";
import type { LegalUpdate } from "../data/types";
import { Pill, Card } from "./belp-ui";

type Draft = {
  category: string;
  title: string;
  summary: string;
  bodyHtml: string;
  whoAffected: string;
  whatChanged: string;
  whatToDo: string;
  effectiveDate: string;
  sourceName: string;
  sourceUrl: string;
  priority: boolean;
};

const EMPTY: Draft = {
  category: "documents",
  title: "",
  summary: "",
  bodyHtml: "",
  whoAffected: "",
  whatChanged: "",
  whatToDo: "",
  effectiveDate: new Date().toISOString().slice(0, 10),
  sourceName: "",
  sourceUrl: "",
  priority: false,
};

const inp =
  "w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-[14px] tracking-tight text-black outline-none transition-colors placeholder:text-black/30 focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/25";
const lbl = "block mb-1 text-[12px] tracking-tight text-black/55 dark:text-white/55";

function toDraft(item: LegalUpdate): Draft {
  return {
    category: item.category,
    title: item.title,
    summary: item.summary,
    bodyHtml: item.bodyHtml ?? "",
    whoAffected: item.whoAffected,
    whatChanged: item.whatChanged,
    whatToDo: item.whatToDo,
    effectiveDate: item.effectiveDate,
    sourceName: item.source?.title ?? "",
    sourceUrl: item.source?.url ?? "",
    priority: item.priority,
  };
}

export function LawEditor({ mobile = false }: { mobile?: boolean }) {
  const { legal, categories, addLegal, updateLegal, deleteLegal, resetLegal } = useStore();
  const reduce = useReducedMotion();
  const [sel, setSel] = useState<string | "new" | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY);

  const selected = useMemo(
    () => (sel && sel !== "new" ? legal.find((l) => l.id === sel) ?? null : null),
    [legal, sel],
  );

  useEffect(() => {
    if (sel === "new") { setDraft(EMPTY); return; }
    if (selected) setDraft(toDraft(selected));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sel]);

  const dirty = useMemo(() => {
    if (sel === "new") return draft.title.trim().length > 0;
    if (!selected) return false;
    return JSON.stringify(draft) !== JSON.stringify(toDraft(selected));
  }, [draft, sel, selected]);

  const close = () => {
    if (dirty && !window.confirm("Закрыть без сохранения?")) return;
    setSel(null);
  };

  const save = () => {
    const item = {
      category: draft.category as LegalUpdate["category"],
      title: draft.title.trim() || "Без названия",
      summary: draft.summary.trim(),
      bodyHtml: draft.bodyHtml.trim(),
      whoAffected: draft.whoAffected.trim(),
      whatChanged: draft.whatChanged.trim(),
      whatToDo: draft.whatToDo.trim(),
      effectiveDate: draft.effectiveDate,
      source: {
        id: `src-${Date.now()}`,
        title: draft.sourceName.trim() || "Источник",
        url: draft.sourceUrl.trim(),
        description: "",
        checkedAt: new Date().toISOString().slice(0, 10),
      },
      priority: draft.priority,
      matchesProfile: false,
    };
    if (sel === "new") addLegal(item);
    else if (selected) updateLegal(selected.id, item);
    setSel(null);
  };

  const p = (k: keyof Draft, v: string | boolean) => setDraft((prev) => ({ ...prev, [k]: v }));
  const catName = (id: string) => categories.find((c) => c.id === id)?.name ?? id;

  return (
    <div className={`relative ${mobile ? "min-h-[70vh]" : "min-h-[400px]"} overflow-hidden`}>
      {/* toolbar */}
      <div className="mb-4 flex items-center justify-between">
        <div className="text-[13px] tracking-tight text-black/55 dark:text-white/55">
          {legal.length} обновлений
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.confirm("Сбросить все правовые обновления к исходным?") && resetLegal()}
            className="inline-flex items-center gap-1.5 rounded-xl border border-black/10 px-3 py-2 text-[12px] tracking-tight text-black/55 transition-colors hover:bg-black/[0.04] dark:border-white/12 dark:text-white/55"
          >
            Сбросить
          </button>
          <button
            onClick={() => setSel("new")}
            className="inline-flex items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 py-2 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"
          >
            <Plus size={14} /> Добавить
          </button>
        </div>
      </div>

      {/* table */}
      {legal.length === 0 ? (
        <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
          <div>
            <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
              <BookOpen size={20} />
            </div>
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>
              Нет правовых обновлений
            </div>
            <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">
              Добавьте первое через кнопку выше.
            </div>
          </div>
        </div>
      ) : (
        <Card className="p-0">
          <div className="overflow-x-auto [&::-webkit-scrollbar]:hidden">
            <table className="w-full min-w-[600px]">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-[0.12em] text-black/40 dark:text-white/40">
                  <th className="px-5 py-3">Категория</th>
                  <th className="py-3">Заголовок</th>
                  <th className="py-3">Дата</th>
                  <th className="py-3">Статус</th>
                  <th className="py-3 pr-5" />
                </tr>
              </thead>
              <tbody className="text-[13px] tracking-tight text-black dark:text-white">
                {legal.map((item) => (
                  <tr key={item.id} className="border-t border-black/[0.05] dark:border-white/[0.05]">
                    <td className="px-5 py-3.5">
                      <Pill tone="lavender">{catName(item.category)}</Pill>
                    </td>
                    <td className="max-w-[280px] truncate py-3.5">{item.title}</td>
                    <td className="py-3.5 text-black/55 dark:text-white/55">{item.effectiveDate}</td>
                    <td className="py-3.5">
                      {item.priority ? (
                        <Pill tone="warn">
                          <AlertCircle size={11} /> Важное
                        </Pill>
                      ) : (
                        <Pill tone="ghost">Обычное</Pill>
                      )}
                    </td>
                    <td className="whitespace-nowrap py-3.5 pr-5 text-right">
                      <button
                        onClick={() => setSel(item.id)}
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
              className="absolute inset-x-0 bottom-0 z-[61] mx-auto flex max-h-[92%] w-full max-w-[720px] flex-col rounded-t-[28px] border border-b-0 border-black/[0.06] bg-white shadow-[0_-30px_80px_-30px_rgba(15,23,42,0.5)] dark:border-white/[0.08] dark:bg-[#0F1117]"
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
                    <BookOpen size={14} className="text-[#0056FF]" />
                    {sel === "new" ? "Новое правовое обновление" : "Редактирование обновления"}
                  </span>
                  <button
                    onClick={close}
                    className="grid h-8 w-8 place-items-center rounded-lg text-black/45 transition-colors hover:bg-black/[0.05] dark:text-white/45 dark:hover:bg-white/[0.07]"
                  >
                    <X size={17} />
                  </button>
                </div>
              </div>

              {/* scrollable form */}
              <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 pb-2 [&::-webkit-scrollbar]:hidden">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className={lbl}>Категория</label>
                    <select
                      value={draft.category}
                      onChange={(e) => p("category", e.target.value)}
                      className={inp}
                    >
                      {categories.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className={lbl}>Дата вступления в силу</label>
                    <input
                      type="date"
                      value={draft.effectiveDate}
                      onChange={(e) => p("effectiveDate", e.target.value)}
                      className={inp}
                    />
                  </div>
                </div>

                <div>
                  <label className={lbl}>Заголовок</label>
                  <input
                    value={draft.title}
                    onChange={(e) => p("title", e.target.value)}
                    placeholder="Название правового обновления"
                    className={`${inp} text-[15px] font-medium`}
                  />
                </div>

                <div>
                  <label className={lbl}>Краткое описание</label>
                  <textarea
                    value={draft.summary}
                    onChange={(e) => p("summary", e.target.value)}
                    placeholder="Суть изменения в 1-2 предложениях"
                    rows={2}
                    className={`${inp} resize-none`}
                  />
                </div>

                <div>
                  <label className={lbl}>Тело статьи (HTML)</label>
                  <textarea
                    value={draft.bodyHtml}
                    onChange={(e) => p("bodyHtml", e.target.value)}
                    placeholder="<p>Что произошло...</p><h3>Что изменилось</h3><ul><li>...</li></ul>"
                    rows={7}
                    className={`${inp} resize-y font-mono text-[12px]`}
                  />
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className={lbl}>Кого касается</label>
                    <textarea
                      value={draft.whoAffected}
                      onChange={(e) => p("whoAffected", e.target.value)}
                      placeholder="Кого затрагивает это изменение"
                      rows={2}
                      className={`${inp} resize-none`}
                    />
                  </div>
                  <div>
                    <label className={lbl}>Что изменилось</label>
                    <textarea
                      value={draft.whatChanged}
                      onChange={(e) => p("whatChanged", e.target.value)}
                      placeholder="Суть нормативных изменений"
                      rows={2}
                      className={`${inp} resize-none`}
                    />
                  </div>
                </div>

                <div>
                  <label className={lbl}>Что сделать гражданину</label>
                  <textarea
                    value={draft.whatToDo}
                    onChange={(e) => p("whatToDo", e.target.value)}
                    placeholder="Рекомендуемые практические шаги"
                    rows={2}
                    className={`${inp} resize-none`}
                  />
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className={lbl}>Источник (орган)</label>
                    <input
                      value={draft.sourceName}
                      onChange={(e) => p("sourceName", e.target.value)}
                      placeholder="Министерство / ведомство"
                      className={inp}
                    />
                  </div>
                  <div>
                    <label className={lbl}>URL источника</label>
                    <input
                      value={draft.sourceUrl}
                      onChange={(e) => p("sourceUrl", e.target.value)}
                      placeholder="portal.gov.by"
                      className={inp}
                    />
                  </div>
                </div>

                <label className="flex cursor-pointer items-center gap-2.5">
                  <div
                    role="switch"
                    aria-checked={draft.priority}
                    onClick={() => p("priority", !draft.priority)}
                    className={`relative h-5 w-9 rounded-full transition-colors ${draft.priority ? "bg-[#0056FF]" : "bg-black/20 dark:bg-white/20"}`}
                  >
                    <div
                      className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${draft.priority ? "translate-x-4" : "translate-x-0.5"}`}
                    />
                  </div>
                  <span className="text-[13px] tracking-tight text-black/70 dark:text-white/70">
                    Приоритетное (помечается как важное)
                  </span>
                </label>
              </div>

              {/* footer */}
              <div
                className="flex shrink-0 items-center justify-between gap-2 border-t border-black/[0.06] p-3 dark:border-white/[0.06]"
                style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
              >
                {sel !== "new" && selected ? (
                  <button
                    onClick={() => {
                      if (window.confirm(`Удалить обновление «${selected.title}»?`)) {
                        deleteLegal(selected.id);
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
