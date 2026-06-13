import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Plus, Trash2, Pencil, X, ShieldAlert, Search, ExternalLink } from "lucide-react";
import { useStore } from "../data/store";
import { apiClient } from "../services/api";

type Entry = {
  id: number;
  title: string;
  category: string;
  source_url: string;
  source_name: string;
  short_description: string;
  status: "draft" | "published";
  media_urls: string;
  attachment_urls: string;
  filters_json: string;
  included_at: string | null;
  last_checked_at: string | null;
};

type Draft = {
  id?: number;
  title: string;
  category: string;
  source_url: string;
  source_name: string;
  short_description: string;
  status: "draft" | "published";
};

const EMPTY: Draft = {
  title: "",
  category: "registry",
  source_url: "",
  source_name: "Министерство юстиции РБ",
  short_description: "",
  status: "draft",
};

const CATEGORIES = [
  { id: "registry", label: "Реестр" },
  { id: "news", label: "Новость" },
  { id: "explanation", label: "Разъяснение" },
];

const inp =
  "w-full rounded-xl border border-black/10 bg-white px-3 py-2 text-[14px] tracking-tight text-black outline-none transition-colors placeholder:text-black/30 focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/25";
const lbl = "mb-1 block text-[12px] tracking-tight text-black/55 dark:text-white/55";

function fmtDate(s: string | null) {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleDateString("ru-RU");
  } catch {
    return s;
  }
}

export function ExtremistEditor({ mobile = false }: { mobile?: boolean }) {
  const { authSession } = useStore();
  const token = authSession?.access_token;
  const [items, setItems] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Draft | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "draft" | "published">("all");
  const [saving, setSaving] = useState(false);

  const reload = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getAdminExtremistEntries<Entry[]>(token);
      setItems(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить записи");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const open = (e?: Entry) => {
    if (e) {
      setEditing({
        id: e.id,
        title: e.title,
        category: e.category,
        source_url: e.source_url,
        source_name: e.source_name ?? "",
        short_description: e.short_description ?? "",
        status: (e.status === "published" ? "published" : "draft") as Draft["status"],
      });
    } else {
      setEditing(EMPTY);
    }
  };

  const close = () => setEditing(null);

  const save = async () => {
    if (!editing || !token) return;
    if (!editing.title.trim()) {
      alert("Введите название");
      return;
    }
    if (!editing.source_url.trim()) {
      alert("Введите URL официального источника (обязательно)");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: editing.title.trim(),
        category: editing.category,
        source_url: editing.source_url.trim(),
        source_name: editing.source_name.trim() || undefined,
        short_description: editing.short_description.trim() || undefined,
        status: editing.status,
      };
      if (editing.id) {
        await apiClient.updateExtremistEntry<Entry>(token, editing.id, payload);
      } else {
        await apiClient.createExtremistEntry<Entry>(token, payload);
      }
      await reload();
      setEditing(null);
    } catch (e) {
      alert(`Не удалось сохранить: ${e instanceof Error ? e.message : "неизвестная ошибка"}`);
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: number) => {
    if (!token) return;
    if (!window.confirm("Удалить запись? Это действие нельзя отменить.")) return;
    try {
      await apiClient.deleteExtremistEntry(token, id);
      await reload();
    } catch (e) {
      alert(`Не удалось удалить: ${e instanceof Error ? e.message : "неизвестная ошибка"}`);
    }
  };

  const filtered = items.filter((e) => {
    if (statusFilter !== "all" && e.status !== statusFilter) return false;
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      e.title.toLowerCase().includes(q) ||
      (e.source_name ?? "").toLowerCase().includes(q) ||
      (e.source_url ?? "").toLowerCase().includes(q)
    );
  });

  return (
    <div className={`relative ${mobile ? "min-h-[70vh]" : "min-h-[400px]"}`}>
      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="flex flex-1 items-center gap-2 rounded-xl border border-black/[0.06] bg-[#F6F7FB] px-3 py-2 dark:border-white/[0.06] dark:bg-white/[0.04]">
          <Search size={14} className="shrink-0 text-black/40 dark:text-white/40" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по записям..."
            className="flex-1 bg-transparent text-[13px] tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40"
          />
        </div>
        <div className="flex items-center gap-1 rounded-xl border border-black/[0.06] bg-white p-1 dark:border-white/[0.06] dark:bg-white/[0.04]">
          {(["all", "published", "draft"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-lg px-2.5 py-1.5 text-[12px] tracking-tight transition-colors ${
                statusFilter === s
                  ? "bg-[#0056FF] text-white"
                  : "text-black/65 hover:bg-black/[0.04] dark:text-white/65 dark:hover:bg-white/[0.04]"
              }`}
            >
              {s === "all" ? "Все" : s === "published" ? "Опубликовано" : "Черновики"}
            </button>
          ))}
        </div>
        <button
          onClick={() => open()}
          className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"
        >
          <Plus size={15} /> Запись
        </button>
      </div>

      {error && (
        <div className="mb-3 rounded-xl border border-red-200/60 bg-red-50 px-3 py-2 text-[12px] text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
          {error}
        </div>
      )}

      {loading && items.length === 0 ? (
        <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
          <div className="text-[13px] tracking-tight text-black/55 dark:text-white/55">Загрузка...</div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
          <div>
            <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
              <ShieldAlert size={20} />
            </div>
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>
              {items.length === 0 ? "Записей ещё нет" : "Ничего не найдено"}
            </div>
            <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">
              {items.length === 0
                ? "Добавьте первую запись экстремистского реестра — только с проверенным source_url."
                : "Попробуйте изменить фильтр или поиск."}
            </div>
          </div>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-black/[0.06] dark:border-white/[0.06]">
          <table className="w-full text-left text-[13px]">
            <thead className="bg-[#F6F7FB] text-[12px] uppercase tracking-[0.06em] text-black/55 dark:bg-white/[0.04] dark:text-white/55">
              <tr>
                <th className="px-4 py-3 font-medium">Название</th>
                <th className="px-4 py-3 font-medium">Категория</th>
                <th className="px-4 py-3 font-medium">Источник</th>
                <th className="px-4 py-3 font-medium">Статус</th>
                <th className="px-4 py-3 font-medium">Обновлено</th>
                <th className="px-4 py-3 font-medium text-right">Действия</th>
              </tr>
            </thead>
            <tbody className="text-black dark:text-white">
              {filtered.map((e) => (
                <tr key={e.id} className="border-t border-black/[0.05] dark:border-white/[0.05]">
                  <td className="max-w-[280px] truncate px-4 py-3.5">{e.title}</td>
                  <td className="px-4 py-3.5 text-black/65 dark:text-white/65">
                    {CATEGORIES.find((c) => c.id === e.category)?.label ?? e.category}
                  </td>
                  <td className="max-w-[200px] truncate px-4 py-3.5 text-black/55 dark:text-white/55">
                    {e.source_name || new URL(e.source_url, "https://minjust.gov.by").hostname}
                  </td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] tracking-tight ${
                        e.status === "published"
                          ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300"
                          : "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300"
                      }`}
                    >
                      {e.status === "published" ? "Опубликовано" : "Черновик"}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-black/55 dark:text-white/55">
                    {fmtDate(e.last_checked_at ?? e.included_at)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3.5 text-right">
                    <a
                      href={e.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mr-1 inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[12px] tracking-tight text-[#0056FF] transition-colors hover:bg-[#0056FF]/[0.08] dark:text-[#7FA8FF]"
                      title="Открыть источник"
                    >
                      <ExternalLink size={13} />
                    </a>
                    <button
                      onClick={() => open(e)}
                      className="mr-1 inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[12px] tracking-tight text-[#0056FF] transition-colors hover:bg-[#0056FF]/[0.08] dark:text-[#7FA8FF]"
                    >
                      <Pencil size={13} /> Изменить
                    </button>
                    <button
                      onClick={() => remove(e.id)}
                      className="inline-flex items-center rounded-lg px-2 py-1 text-red-500 transition-colors hover:bg-red-500/[0.08]"
                      title="Удалить"
                    >
                      <Trash2 size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Editor modal */}
      <AnimatePresence>
        {editing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4 backdrop-blur-sm"
            onClick={close}
          >
            <motion.div
              initial={{ scale: 0.96, y: 8 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.96, y: 8 }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
              className="w-full max-w-[560px] rounded-3xl bg-white p-6 shadow-2xl dark:bg-[#0F1117]"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-4 flex items-center justify-between">
                <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>
                  {editing.id ? "Изменить запись" : "Новая запись реестра"}
                </div>
                <button
                  onClick={close}
                  className="grid h-8 w-8 place-items-center rounded-full text-black/55 hover:bg-black/[0.05] dark:text-white/55 dark:hover:bg-white/[0.05]"
                  aria-label="Закрыть"
                >
                  <X size={16} />
                </button>
              </div>
              <div className="space-y-3">
                <div>
                  <label className={lbl}>Название *</label>
                  <input
                    className={inp}
                    value={editing.title}
                    onChange={(e) => setEditing((d) => d && { ...d, title: e.target.value })}
                    placeholder="Например: Канал N в реестре"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className={lbl}>Категория</label>
                    <select
                      className={inp}
                      value={editing.category}
                      onChange={(e) => setEditing((d) => d && { ...d, category: e.target.value })}
                    >
                      {CATEGORIES.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className={lbl}>Статус</label>
                    <select
                      className={inp}
                      value={editing.status}
                      onChange={(e) =>
                        setEditing((d) => d && { ...d, status: e.target.value as Draft["status"] })
                      }
                    >
                      <option value="draft">Черновик</option>
                      <option value="published">Опубликовано</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className={lbl}>URL официального источника *</label>
                  <input
                    className={inp}
                    value={editing.source_url}
                    onChange={(e) => setEditing((d) => d && { ...d, source_url: e.target.value })}
                    placeholder="https://minjust.gov.by/..."
                  />
                </div>
                <div>
                  <label className={lbl}>Название источника</label>
                  <input
                    className={inp}
                    value={editing.source_name}
                    onChange={(e) => setEditing((d) => d && { ...d, source_name: e.target.value })}
                    placeholder="Министерство юстиции РБ"
                  />
                </div>
                <div>
                  <label className={lbl}>Краткое описание</label>
                  <textarea
                    className={inp + " min-h-[80px] resize-y"}
                    value={editing.short_description}
                    onChange={(e) =>
                      setEditing((d) => d && { ...d, short_description: e.target.value })
                    }
                    placeholder="Кратко поясните, почему запись в реестре"
                  />
                </div>
              </div>
              <div className="mt-6 flex items-center justify-end gap-2">
                <button
                  onClick={close}
                  className="rounded-xl border border-black/10 bg-white px-4 py-2 text-[13px] tracking-tight text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:bg-white/[0.04] dark:text-white/70"
                >
                  Отмена
                </button>
                <button
                  onClick={save}
                  disabled={saving}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-[#0056FF] px-4 py-2 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] disabled:opacity-50"
                >
                  <Check size={14} /> {saving ? "Сохранение..." : "Сохранить"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
