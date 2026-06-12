import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import {
  Search, FileText, Home, Bell, Shield, Wallet, Heart, Briefcase, Hammer,
  ArrowUpRight, AlertCircle, CalendarClock, MapPin, ChevronRight, Settings,
  Building2, Users, BookOpen, LayoutGrid, Sparkles, Clock, Check,
  Eye, BarChart3, TrendingUp, Plus, Newspaper, Pencil, Trash2,
  ShieldAlert, Flag, Ban, X,
} from "lucide-react";
import { Card, Pill, PrimaryButton, GhostButton, Logo } from "./belp-ui";
import { ContentEditor, type ContentKind, type ContentDraft } from "./content-editor";
import { useStore } from "../data/store";
import type { Article } from "../data/types";
import { RegionsEditor } from "./regions-editor";
import { LawEditor } from "./law-editor";
import { AuthoritiesEditor } from "./authorities-editor";

function NavItem({ icon, label, active, badge, onClick }: { icon: React.ReactNode; label: string; active?: boolean; badge?: string; onClick?: () => void }) {
  return (
    <button onClick={onClick} className={`relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left tracking-tight transition-colors ${active ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/65 hover:bg-black/[0.03] dark:text-white/65 dark:hover:bg-white/[0.04]"}`}>
      <span className="grid h-5 w-5 place-items-center">{icon}</span>
      <span className="flex-1 text-[14px]">{label}</span>
      {badge && <span className="rounded-full bg-[#0056FF] px-1.5 text-[10px] tracking-tight text-white">{badge}</span>}
    </button>
  );
}

export function DesktopDashboard() {
  return (
    <div className="overflow-hidden rounded-[28px] border border-black/[0.06] bg-[#F6F7FB] shadow-[0_60px_140px_-40px_rgba(15,23,42,0.35)] dark:border-white/[0.06] dark:bg-[#07080C]">
      <div className="grid h-[760px] grid-cols-[260px_1fr]">
        {/* Sidebar */}
        <aside className="flex flex-col border-r border-black/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-[#0B0D13]">
          <Logo size={26} />
          <div className="mt-6 flex items-center gap-3 rounded-2xl bg-[#F6F7FB] px-3 py-2 dark:bg-white/[0.04]">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-[#0056FF] to-[#2277FF]" />
            <div className="min-w-0 flex-1">
              <div className="truncate tracking-tight text-black dark:text-white">Алексей И.</div>
              <div className="truncate text-[11px] tracking-tight text-black/50 dark:text-white/50">Минск · Первомайский</div>
            </div>
          </div>

          <nav className="mt-6 space-y-1">
            <div className="px-3 pb-1.5 text-[10px] uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Личный кабинет</div>
            <NavItem icon={<Home size={16} />} label="Главная" active />
            <NavItem icon={<FileText size={16} />} label="Мои ситуации" badge="3" />
            <NavItem icon={<Shield size={16} />} label="Документы" />
            <NavItem icon={<Bell size={16} />} label="Уведомления" badge="5" />
            <NavItem icon={<BookOpen size={16} />} label="Важное для вас" />
          </nav>
          <nav className="mt-6 space-y-1">
            <div className="px-3 pb-1.5 text-[10px] uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Инструменты</div>
            <NavItem icon={<Wallet size={16} />} label="Налоги" />
            <NavItem icon={<Home size={16} />} label="ЖКХ" />
            <NavItem icon={<Building2 size={16} />} label="Учреждения" />
          </nav>

          <div className="mt-auto">
            <Card className="p-3.5">
              <div className="flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                  <Sparkles size={14} />
                </span>
                <div className="text-[12px] tracking-tight text-black/70 dark:text-white/70">Ассистент готов помочь</div>
              </div>
              <button className="mt-3 w-full rounded-xl bg-[#0056FF] py-2 text-[13px] tracking-tight text-white">Спросить</button>
            </Card>
          </div>
        </aside>

        {/* Main */}
        <main className="flex flex-col overflow-hidden">
          {/* Top bar */}
          <div className="flex items-center gap-4 border-b border-black/[0.06] bg-white/70 px-8 py-4 backdrop-blur dark:border-white/[0.06] dark:bg-[#0B0D13]/70">
            <div className="flex flex-1 items-center gap-3 rounded-2xl border border-black/[0.06] bg-[#F6F7FB] px-4 py-2.5 dark:border-white/[0.06] dark:bg-white/[0.04]">
              <Search size={16} className="text-black/40 dark:text-white/40" />
              <input placeholder="Какая у вас ситуация? Например: открыть ИП в Минске" className="flex-1 bg-transparent text-[14px] tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
              <span className="rounded-md bg-black/[0.05] px-1.5 py-0.5 text-[10px] tracking-tight text-black/50 dark:bg-white/[0.08] dark:text-white/60">⌘ K</span>
            </div>
            <button className="grid h-10 w-10 place-items-center rounded-xl bg-white text-black shadow-sm dark:bg-white/[0.06] dark:text-white">
              <Bell size={16} />
            </button>
            <button className="grid h-10 w-10 place-items-center rounded-xl bg-white text-black shadow-sm dark:bg-white/[0.06] dark:text-white">
              <Settings size={16} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-8 py-7 [&::-webkit-scrollbar]:hidden">
            <div className="flex items-end justify-between">
              <div>
                <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Среда, 3 июня</div>
                <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30, lineHeight: 1.1 }}>
                  Добрый день, Алексей
                </div>
              </div>
              <div className="flex gap-2">
                <GhostButton className="h-10 px-4">Каталог</GhostButton>
                <PrimaryButton className="h-10 px-4">Создать план</PrimaryButton>
              </div>
            </div>

            {/* Hero situation */}
            <div className="mt-7 grid grid-cols-3 gap-5">
              <div className="col-span-2 overflow-hidden rounded-3xl p-6 text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
                style={{ background: "radial-gradient(120% 100% at 0% 0%, #2277FF 0%, #0056FF 45%, #001A66 100%)" }}>
                <div className="flex items-center justify-between">
                  <Pill tone="ghost"><span className="text-white/90">Активная ситуация</span></Pill>
                  <span className="text-[12px] tracking-tight text-white/70">Шаг 3 из 5 · обновлено сегодня</span>
                </div>
                <div className="mt-4 max-w-[440px] tracking-tight" style={{ fontSize: 26, lineHeight: 1.15 }}>
                  Восстановление паспорта
                </div>
                <div className="mt-1 max-w-[440px] text-[13px] tracking-tight text-white/75">
                  Следующее действие: подать заявление в РОВД по месту жительства. Возьмите справку и две фотографии.
                </div>
                <div className="mt-5 h-1.5 w-full overflow-hidden rounded-full bg-white/20">
                  <motion.div initial={{ width: 0 }} animate={{ width: "60%" }} transition={{ duration: 1 }} className="h-full rounded-full bg-white" />
                </div>
                <div className="mt-5 flex items-center gap-3">
                  <button className="rounded-xl bg-white px-4 py-2 text-[13px] tracking-tight text-[#0056FF]">Продолжить →</button>
                  <button className="rounded-xl border border-white/25 px-4 py-2 text-[13px] tracking-tight text-white">Открыть план</button>
                </div>
              </div>

              <Card className="p-5">
                <div className="flex items-center justify-between">
                  <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Ближайшие сроки</div>
                  <span className="text-[11px] tracking-tight text-[#0056FF]">Все</span>
                </div>
                <div className="mt-3 space-y-3">
                  {[
                    { t: "Оплата налога на недвижимость", d: "через 14 дней", warn: true },
                    { t: "Подача декларации 3-НДФЛ", d: "через 1 мес", warn: false },
                    { t: "Замена водительского", d: "через 6 мес", warn: false },
                  ].map((x) => (
                    <div key={x.t} className="flex items-start gap-3">
                      <span className={`mt-0.5 grid h-8 w-8 place-items-center rounded-xl ${x.warn ? "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300" : "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"}`}>
                        <CalendarClock size={15} />
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="truncate tracking-tight text-black dark:text-white">{x.t}</div>
                        <div className={`text-[12px] tracking-tight ${x.warn ? "text-amber-600 dark:text-amber-400" : "text-black/55 dark:text-white/55"}`}>Срок: {x.d}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Categories */}
            <div className="mt-7">
              <div className="flex items-center justify-between">
                <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 17 }}>Каталог помощи</div>
                <span className="text-[12px] tracking-tight text-[#0056FF]">Открыть все</span>
              </div>
              <div className="mt-3 grid grid-cols-6 gap-3">
                {[
                  { i: <FileText size={18} />, n: "Документы", c: 28 },
                  { i: <Home size={18} />, n: "ЖКХ", c: 14 },
                  { i: <Wallet size={18} />, n: "Налоги", c: 19 },
                  { i: <Heart size={18} />, n: "Семья", c: 22 },
                  { i: <Briefcase size={18} />, n: "Работа", c: 17 },
                  { i: <Hammer size={18} />, n: "Здоровье", c: 12 },
                ].map((c) => (
                  <Card key={c.n} interactive className="p-4">
                    <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{c.i}</span>
                    <div className="mt-7 tracking-tight text-black dark:text-white">{c.n}</div>
                    <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{c.c} материалов</div>
                  </Card>
                ))}
              </div>
            </div>

            {/* Legal + docs */}
            <div className="mt-7 grid grid-cols-3 gap-5">
              <Card className="col-span-2 p-5">
                <div className="flex items-center justify-between">
                  <div className="tracking-tight text-black dark:text-white">Важное для вас</div>
                  <span className="text-[12px] tracking-tight text-[#0056FF]">Все обновления</span>
                </div>
                <div className="mt-4 divide-y divide-black/[0.06] dark:divide-white/[0.06]">
                  {[
                    { t: "Налоги", title: "Новый порядок имущественного вычета для семей с детьми", d: "с 1 июля 2026", warn: true },
                    { t: "ЖКХ", title: "Изменение тарифов на отопление в г. Минск", d: "с 1 октября 2026", warn: false },
                    { t: "Документы", title: "Электронный паспорт: запуск второй очереди в Беларуси", d: "с 15 сентября 2026", warn: true },
                  ].map((x) => (
                    <div key={x.title} className="flex items-start gap-4 py-3.5 first:pt-0 last:pb-0">
                      <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                        <FileText size={15} />
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <Pill tone="lavender">{x.t}</Pill>
                          {x.warn && <Pill tone="warn"><AlertCircle size={10} /> Важное</Pill>}
                          <span className="text-[11px] tracking-tight text-black/40 dark:text-white/40">{x.d}</span>
                        </div>
                        <div className="mt-1.5 tracking-tight text-black dark:text-white">{x.title}</div>
                      </div>
                      <ArrowUpRight size={16} className="mt-1 text-black/35 dark:text-white/35" />
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="p-5">
                <div className="flex items-center justify-between">
                  <div className="tracking-tight text-black dark:text-white">Документы</div>
                  <span className="text-[12px] tracking-tight text-[#0056FF]">Хранилище</span>
                </div>
                <div className="mt-3 space-y-2">
                  {[
                    { n: "Паспорт", s: "Действует до 2031", ok: true },
                    { n: "Медкнижка", s: "Действует до 2027", ok: true },
                    { n: "Водительское", s: "6 мес до замены", ok: false },
                  ].map((d) => (
                    <div key={d.n} className="flex items-center gap-3 rounded-2xl bg-[#F6F7FB] px-3 py-2.5 dark:bg-white/[0.03]">
                      <span className={`grid h-9 w-9 place-items-center rounded-xl ${d.ok ? "bg-white text-[#0056FF] dark:bg-white/[0.06]" : "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300"}`}>
                        <Shield size={15} />
                      </span>
                      <div className="flex-1">
                        <div className="tracking-tight text-black dark:text-white">{d.n}</div>
                        <div className={`text-[11px] tracking-tight ${d.ok ? "text-black/45 dark:text-white/45" : "text-amber-600 dark:text-amber-400"}`}>{d.s}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

/* ---------------- ADMIN PANEL ---------------- */
// v1.1 (P10): admin analytics — реальные счётчики считаются из стора
// (admin.scenarios, articles, views). Если данных нет — пустые
// карточки с честной плашкой «нет данных», а не синтетические числа.
const EMPTY_ADMIN_ROWS: { c: string; t: string; st: string; a: string; u: string }[] = [];
const EMPTY_ADMIN_STATS = [
  { l: "Всего сценариев", v: "0", d: "из API" },
  { l: "Опубликовано", v: "0", d: "0%" },
  { l: "На проверке", v: "0", d: "ждут редактора" },
  { l: "Просмотры за 7 дней", v: "—", d: "пока нет данных" },
];
const WEEK_BASE = [
  { d: "Пн", v: 0 }, { d: "Вт", v: 0 }, { d: "Ср", v: 0 },
  { d: "Чт", v: 0 }, { d: "Пт", v: 0 }, { d: "Сб", v: 0 }, { d: "Вс", v: 0 },
];

export function AdminPanel({ editor = false, fill = false, mobile = false }: { editor?: boolean; fill?: boolean; mobile?: boolean } = {}) {
  const { admin, profile, role, articles, addArticle, updateArticle, removeArticle, isSubmitterBlocked, toggleBlockedSubmitter, uploadMedia, viewsDaily, categories, addCategory, updateCategory, deleteCategory, setAdminUserRole, setAdminUserActive, deleteAdminUser, currentUser } = useStore();
  const [section, setSection] = useState(editor ? "dashboard" : "scenarios");
  const [navPage, setNavPage] = useState(0);
  const [period, setPeriod] = useState<"7" | "30">("7");
  const [pubFilter, setPubFilter] = useState<"all" | ContentKind>("all");
  const [editing, setEditing] = useState<{ kind: ContentKind; mode: "create" | "edit"; initial?: Partial<ContentDraft>; id?: string; authorMeta?: Article["author"] } | null>(null);
  const navScrollRef = useRef<HTMLDivElement>(null);
  const openEditor = (kind: ContentKind) => setEditing({ kind, mode: "create" });
  const editArticle = (a: Article) => setEditing({
    kind: a.kind, mode: "edit", id: a.id, authorMeta: a.author,
    initial: {
      kind: a.kind, title: a.title, summary: a.summary, bodyHtml: a.bodyHtml, cover: a.cover,
      video: a.video, gallery: a.gallery, tags: a.tags, category: a.category,
      specialization: a.specialization, audience: a.audience, source: a.source,
      sourceUrl: a.sourceUrl, date: a.date, author: a.author.name,
    },
  });
  const handleSubmit = (draft: ContentDraft, action: "publish" | "draft" | "submit") => {
    // Local-first: persist the publication; backend sync comes later.
    const fields = {
      kind: draft.kind, title: draft.title.trim(), summary: draft.summary, bodyHtml: draft.bodyHtml,
      cover: draft.cover, video: draft.video, gallery: draft.gallery, tags: draft.tags,
      category: draft.category, specialization: draft.specialization, audience: draft.audience,
      source: draft.source, sourceUrl: draft.sourceUrl, date: draft.date,
      status: (action === "draft" ? "draft" : action === "submit" ? "review" : "published") as Article["status"],
    };
    if (editing?.mode === "edit" && editing.id) {
      // Editor reworked a citizen submission → record "при поддержке {редактор}".
      const patch: Partial<Article> = { ...fields };
      if (editing.authorMeta?.proposedBy) patch.author = { ...editing.authorMeta, name: profile.name };
      updateArticle(editing.id, patch);
      setEditing(null);
      setSection("publications");
      return;
    }
    addArticle({ ...fields, author: { name: draft.author || profile.name, role: role === "admin" ? "admin" : "editor" } });
    setEditing(null);
    setSection("publications");
  };
  const onNavScroll = () => {
    const el = navScrollRef.current;
    if (el && el.clientWidth) setNavPage(Math.round(el.scrollLeft / el.clientWidth));
  };
  const catLabel = (id: string) => categories.find((c) => c.id === id)?.name ?? id;
  const statusLabel = (s: string) => (s === "published" ? "Опубликовано" : s === "review" ? "На проверке" : s === "rejected" ? "Отклонено" : "Черновик");

  const apiRows = admin.scenarios.map((s) => ({
    c: catLabel(s.category),
    t: s.title,
    st: statusLabel(s.status),
    a: editor ? "Редактор" : "—",
    u: `${s.taskCount} задач`,
  }));
  const rows = apiRows;

  const total = admin.scenarios.length;
  const published = admin.scenarios.filter((s) => s.status === "published").length;
  const review = admin.scenarios.filter((s) => s.status === "review").length;
  // v1.1 (P10): реальные счётчики. Плашка «нет данных», если backend пустой.
  const hasRealData = admin.status === "api" && total > 0;
  const stats = hasRealData
    ? [
        { l: "Всего сценариев", v: String(total), d: "из API" },
        { l: "Опубликовано", v: String(published), d: `${Math.round((published / total) * 100)}%` },
        { l: "На проверке", v: String(review), d: "ждут редактора" },
        { l: "Черновики", v: String(total - published - review), d: "в работе" },
      ]
    : EMPTY_ADMIN_STATS;

  const tone = (s: string) => s === "Опубликовано" ? "ok" : s === "На проверке" ? "lavender" : s === "Отклонено" ? "warn" : "ghost";
  const moderationCount = articles.filter((a) => a.status === "review").length;

  const SECTIONS: { id: string; icon: React.ReactNode; label: string; short: string; badge?: string; sys?: boolean }[] = [
    { id: "dashboard", icon: <BarChart3 size={15} />, label: "Обзор", short: "Обзор" },
    { id: "publications", icon: <Newspaper size={15} />, label: "Публикации", short: "Публик.", badge: articles.length ? String(articles.length) : undefined },
    { id: "moderation", icon: <ShieldAlert size={15} />, label: "Модерация", short: "Модер.", badge: moderationCount ? String(moderationCount) : undefined },
    { id: "categories", icon: <LayoutGrid size={15} />, label: "Категории", short: "Категории" },
    { id: "scenarios", icon: <FileText size={15} />, label: "Сценарии", short: "Сценарии", badge: total ? String(total) : undefined },
    { id: "law", icon: <BookOpen size={15} />, label: "Правовые обновления", short: "Право" },
    { id: "authorities", icon: <Building2 size={15} />, label: "Учреждения", short: "Учрежд." },
    { id: "extremist", icon: <ShieldAlert size={15} />, label: "Экстремистский реестр", short: "Экстр." },
    { id: "users", icon: <Users size={15} />, label: "Пользователи и роли", short: "Люди", sys: true },
    { id: "regions", icon: <MapPin size={15} />, label: "Регионы и города", short: "Регионы", sys: true },
    { id: "rules", icon: <Bell size={15} />, label: "Правила уведомлений", short: "Правила", sys: true },
    { id: "audit", icon: <Clock size={15} />, label: "Журнал действий", short: "Журнал", sys: true },
  ];
  const visible = SECTIONS.filter(s => !s.sys || !editor);
  const current = visible.find(s => s.id === section) ?? visible[0];

  // Keep the paged mobile nav aligned to the active section (and avoid an
  // off-page initial scroll position on mount).
  useEffect(() => {
    const el = navScrollRef.current;
    if (!mobile || !el || !el.clientWidth) return;
    const idx = visible.findIndex((s) => s.id === section);
    const page = idx < 0 ? 0 : Math.floor(idx / 4);
    el.scrollTo({ left: page * el.clientWidth, behavior: "smooth" });
    setNavPage(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [section, mobile, editor]);

  // ---- Editorial dashboard (representative analytics until tracking lands) ----
  const fmt = (n: number) => Math.round(n).toLocaleString("ru-RU");
  const todayLabel = new Date().toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
  const periodMul = period === "30" ? 4.3 : 1;
  // Real article views once content exists; representative demo numbers until then.
  const realPublished = articles.filter((a) => a.status === "published");
  const realReview = articles.filter((a) => a.status === "review").length;
  const hasReal = realPublished.length > 0;
  // v1.1 (P10): реальные просмотры из `a.views` если они есть. Никаких
  // синтетических псевдослучайных чисел на пустых данных.
  const baseMaterials = hasReal
    ? realPublished.map((a) => ({ title: a.title, status: "Опубликовано", views: a.views }))
    : [];
  const viewMul = hasReal ? 1 : periodMul; // real views are cumulative, not per-period
  const topMaterials = [...baseMaterials]
    .sort((a, b) => b.views - a.views)
    .slice(0, 5)
    .map((m) => ({ ...m, views: Math.round(m.views * viewMul) }));
  const totalViews = baseMaterials.reduce((s, m) => s + m.views, 0) * viewMul;
  const avgViews = baseMaterials.length ? totalViews / baseMaterials.length : 0;
  const maxTop = topMaterials[0]?.views || 1;
  const shortWeekday = (iso: string) => {
    const wd = new Date(`${iso}T00:00:00`).toLocaleDateString("ru-RU", { weekday: "short" });
    return wd.charAt(0).toUpperCase() + wd.slice(1);
  };
  const hasWeekReal = viewsDaily.some((d) => d.count > 0);
  // v1.1 (P10): если реальных просмотров нет — week остаётся пустым,
  // а не заполняется синтетикой.
  const week = hasWeekReal
    ? viewsDaily.map((d) => ({ d: shortWeekday(d.date), v: d.count }))
    : WEEK_BASE;
  const maxWeek = Math.max(1, ...week.map((d) => d.v));
  const pubCount = hasReal ? realPublished.length : total ? published : 118;
  const revCount = hasReal ? realReview : total ? review : 17;
  const analyticsNote = hasWeekReal
    ? "Просмотры и дневной график — реальные (счётчик при открытии материала)."
    : hasReal
      ? "Просмотры — реальные. Дневной график — демонстрационный (накапливается по дням)."
      : "Демо-данные аналитики до накопления реальных просмотров.";
  const dashKpis = [
    { l: hasReal ? "Просмотры всего" : "Просмотры за период", v: fmt(totalViews), d: hasReal ? "по материалам" : period === "30" ? "за 30 дней" : "за 7 дней", icon: <Eye size={15} />, up: hasReal ? "" : "+12%" },
    { l: "Опубликовано", v: String(pubCount), d: "материалов", icon: <Check size={15} />, up: "" },
    { l: "На модерации", v: String(revCount), d: "ждут вас", icon: <Clock size={15} />, up: "" },
    { l: "Средний охват", v: fmt(avgViews), d: "на материал", icon: <BarChart3 size={15} />, up: "" },
  ];

  const dashboardBody = (
    <>
      <div className="overflow-hidden rounded-2xl bg-gradient-to-br from-[#0B2A86] via-[#0846C6] to-[#0056FF] p-5 text-white sm:p-6">
        <div className="text-[12px] tracking-tight text-white/70">Редакция · {todayLabel}</div>
        <div className="mt-1 tracking-tight" style={{ fontSize: 22 }}>Здравствуйте, {profile.name}</div>
        <div className="mt-1.5 max-w-[54ch] text-[13px] leading-relaxed tracking-tight text-white/80">
          За {period === "30" ? "30 дней" : "неделю"} ваши материалы посмотрели {fmt(totalViews)} раз.{" "}
          {revCount ? `${revCount} на модерации ждут решения.` : "Новых материалов на модерации нет."}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {dashKpis.map((k) => (
          <Card key={k.l} className="p-4">
            <div className="flex items-center justify-between">
              <span className="grid h-8 w-8 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{k.icon}</span>
              {k.up && <span className="text-[11px] tracking-tight text-emerald-600 dark:text-emerald-400">{k.up}</span>}
            </div>
            <div className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>{k.v}</div>
            <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{k.l}</div>
            <div className="text-[11px] tracking-tight text-black/40 dark:text-white/40">{k.d}</div>
          </Card>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 15 }}>Просмотры по дням</div>
              <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">Динамика за неделю</div>
            </div>
            <span className="flex items-center gap-1 text-[12px] tracking-tight text-emerald-600 dark:text-emerald-400"><TrendingUp size={13} /> рост</span>
          </div>
          <div className="mt-6 flex h-44 gap-2 sm:gap-3">
            {week.map((d, i) => (
              <div key={d.d} className="flex flex-1 flex-col items-center gap-2">
                <div className="flex w-full flex-1 items-end justify-center">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${Math.max(6, (d.v / maxWeek) * 100)}%` }}
                    transition={{ duration: 0.5, delay: i * 0.05, ease: "easeOut" }}
                    className="w-full max-w-[34px] rounded-t-lg bg-gradient-to-t from-[#0056FF] to-[#5C92FF]"
                    title={fmt(d.v)}
                  />
                </div>
                <span className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{d.d}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 15 }}>Топ материалов</div>
          <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">По просмотрам за период</div>
          <div className="mt-4 space-y-3">
            {topMaterials.map((m, i) => (
              <div key={m.title}>
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-[13px] tracking-tight text-black dark:text-white">{i + 1}. {m.title}</span>
                  <span className="shrink-0 text-[12px] tabular-nums tracking-tight text-black/55 dark:text-white/55">{fmt(m.views)}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.08]">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${(m.views / maxTop) * 100}%` }} transition={{ duration: 0.5, delay: i * 0.06, ease: "easeOut" }} className="h-full rounded-full bg-[#0056FF]" />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-3 text-[11px] tracking-tight text-black/35 dark:text-white/35">{analyticsNote}</div>
    </>
  );

  const scenariosBody = (
    <>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.l} className="p-4">
            <div className="text-[12px] tracking-tight text-black/50 dark:text-white/50">{s.l}</div>
            <div className="mt-2 tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>{s.v}</div>
            <div className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{s.d}</div>
          </Card>
        ))}
      </div>
      <Card className="mt-5 p-0">
        <div className="flex items-center gap-2 overflow-x-auto border-b border-black/[0.06] px-4 py-3 dark:border-white/[0.06] sm:px-5 [&::-webkit-scrollbar]:hidden">
          {["Все","Опубликовано","На проверке","Черновик"].map((t, i) => (
            <span key={t} className={`shrink-0 rounded-full px-3 py-1.5 text-[12px] tracking-tight ${i===0 ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/55 dark:text-white/55"}`}>{t}</span>
          ))}
          <div className="ml-auto hidden items-center gap-2 rounded-xl bg-[#F6F7FB] px-3 py-1.5 text-[12px] dark:bg-white/[0.04] sm:flex">
            <Search size={13} className="text-black/40 dark:text-white/40" />
            <input placeholder="Поиск" className="bg-transparent tracking-tight outline-none dark:text-white" />
          </div>
        </div>
        <div className="overflow-x-auto [&::-webkit-scrollbar]:hidden">
          <table className="w-full min-w-[520px]">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-[0.12em] text-black/40 dark:text-white/40">
                <th className="px-5 py-3">Категория</th>
                <th className="py-3">Название</th>
                <th className="py-3">Статус</th>
                <th className="py-3">Автор</th>
                <th className="py-3">Обновлено</th>
                <th className="py-3"></th>
              </tr>
            </thead>
            <tbody className="text-[13px] tracking-tight text-black dark:text-white">
              {rows.map((r, ri) => (
                <tr key={`${r.t}-${ri}`} className="border-t border-black/[0.05] dark:border-white/[0.05]">
                  <td className="px-5 py-3.5"><Pill tone="lavender">{r.c}</Pill></td>
                  <td className="py-3.5">{r.t}</td>
                  <td className="py-3.5"><Pill tone={tone(r.st) as any}>{r.st === "Опубликовано" && <Check size={11} />}{r.st}</Pill></td>
                  <td className="py-3.5 text-black/65 dark:text-white/65">{r.a}</td>
                  <td className="py-3.5 text-black/50 dark:text-white/50">{r.u}</td>
                  <td className="py-3.5 pr-5 text-right"><ChevronRight size={15} className="inline text-black/35 dark:text-white/35" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );

  const placeholderBody = (
    <div className="grid h-full place-items-center p-8 text-center">
      <div>
        <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{current.icon}</div>
        <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>{current.label}</div>
        <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">Раздел подключается к backend. CRUD добавляется поэтапно.</div>
      </div>
    </div>
  );

  // P7: каркас раздела «Экстремистский контент» — отдельная страница.
  // В админ-окне показываем короткое описание + кнопку перехода на /extremist.
  const extremistLinkBody = (
    <div className="grid h-full place-items-center p-8 text-center">
      <div className="max-w-[480px]">
        <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-red-50 text-red-500 dark:bg-red-500/15 dark:text-red-300">
          <ShieldAlert size={20} />
        </div>
        <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>Экстремистский реестр</div>
        <div className="mt-2 text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">
          Юридически чувствительный раздел. Содержит только записи с проверенным
          официальным источником и датой проверки. Каркас открывается на отдельной странице.
        </div>
        <a
          href="/extremist"
          onClick={(e) => { e.preventDefault(); window.history.pushState({}, "", "/extremist"); window.dispatchEvent(new PopStateEvent("popstate")); }}
          className="mt-5 inline-flex h-10 items-center gap-1.5 rounded-xl bg-[#0056FF] px-4 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)]"
        >
          Открыть раздел →
        </a>
      </div>
    </div>
  );

  // ---- Publications (editor / UGC output) ----
  const kindLabel = (k: ContentKind) => (k === "news" ? "Новости" : k === "scenario" ? "Жизненный сценарий" : "Проблема");
  const authorLabel = (a: Article) => {
    const m = a.author;
    if (m.proposedBy) {
      const who = m.anonymous ? "Аноним" : m.proposedBy;
      return m.name && m.name !== m.proposedBy ? `Предложено: ${who} · при поддержке ${m.name}` : `Предложено: ${who}`;
    }
    return `Автор: ${m.name}`;
  };
  const pubRows = articles.filter((a) => pubFilter === "all" || a.kind === pubFilter);

  const publicationsBody = (
    <>
      <div className="mb-4 flex items-center gap-2 overflow-x-auto [&::-webkit-scrollbar]:hidden">
        {([["all", "Все"], ["news", "Новости"], ["scenario", "Жизненные сценарии"], ["problem", "Проблемы"]] as const).map(([id, label]) => {
          const cnt = id === "all" ? articles.length : articles.filter((a) => a.kind === id).length;
          return (
            <button key={id} onClick={() => setPubFilter(id)} className={`shrink-0 rounded-full px-3 py-1.5 text-[12px] tracking-tight transition-colors ${pubFilter === id ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/55 hover:bg-black/[0.04] dark:text-white/55 dark:hover:bg-white/[0.05]"}`}>{label}{cnt ? ` · ${cnt}` : ""}</button>
          );
        })}
      </div>
      {pubRows.length === 0 ? (
        <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
          <div>
            <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"><Newspaper size={20} /></div>
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{articles.length ? "Нет публикаций этого типа" : "Пока нет публикаций"}</div>
            <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">Создайте материал через редактор контента.</div>
            <button onClick={() => openEditor("news")} className="mx-auto mt-4 inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 text-[13px] tracking-tight text-white transition-all hover:bg-[#0049DB] active:translate-y-[1px]"><Plus size={15} /> Новая публикация</button>
          </div>
        </div>
      ) : (
        <Card className="p-0">
          <div className="overflow-x-auto [&::-webkit-scrollbar]:hidden">
            <table className="w-full min-w-[660px]">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-[0.12em] text-black/40 dark:text-white/40">
                  <th className="px-5 py-3">Тип</th><th className="py-3">Название</th><th className="py-3">Автор</th><th className="py-3">Статус</th><th className="py-3">Дата</th><th className="py-3 pr-5"></th>
                </tr>
              </thead>
              <tbody className="text-[13px] tracking-tight text-black dark:text-white">
                {pubRows.map((a) => (
                  <tr key={a.id} className="border-t border-black/[0.05] dark:border-white/[0.05]">
                    <td className="px-5 py-3.5"><Pill tone="lavender">{kindLabel(a.kind)}</Pill></td>
                    <td className="max-w-[240px] truncate py-3.5">{a.title || "Без названия"}</td>
                    <td className="py-3.5 text-black/65 dark:text-white/65">{authorLabel(a)}</td>
                    <td className="py-3.5"><Pill tone={tone(statusLabel(a.status)) as any}>{a.status === "published" && <Check size={11} />}{statusLabel(a.status)}</Pill></td>
                    <td className="py-3.5 text-black/50 dark:text-white/50">{a.date}</td>
                    <td className="whitespace-nowrap py-3.5 pr-5 text-right">
                      <button onClick={() => editArticle(a)} className="mr-1 inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[12px] tracking-tight text-[#0056FF] transition-colors hover:bg-[#0056FF]/[0.08] dark:text-[#7FA8FF]"><Pencil size={13} /> Изменить</button>
                      <button onClick={() => removeArticle(a.id)} title="Удалить" className="inline-flex items-center rounded-lg px-2 py-1 text-red-500 transition-colors hover:bg-red-500/[0.08]"><Trash2 size={13} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  );

  // ---- Moderation queue (UGC submissions awaiting an editor decision) ----
  const queue = articles.filter((a) => a.status === "review");
  const moderationBody = (
    queue.length === 0 ? (
      <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
        <div>
          <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400"><Check size={20} /></div>
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>Очередь пуста</div>
          <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">Предложения граждан появятся здесь на проверку.</div>
        </div>
      </div>
    ) : (
      <div className="space-y-3">
        {queue.map((a) => {
          const blocked = !!a.author.proposerId && isSubmitterBlocked(a.author.proposerId);
          return (
            <Card key={a.id} className="p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
                    <Pill tone="lavender">{kindLabel(a.kind)}</Pill>
                    {a.reported && <Pill tone="warn"><Flag size={11} /> Жалоба</Pill>}
                    {blocked && <Pill tone="warn"><Ban size={11} /> Отправитель заблокирован</Pill>}
                  </div>
                  <div className="truncate tracking-tight text-black dark:text-white" style={{ fontSize: 15 }}>{a.title || "Без названия"}</div>
                  {a.summary && <div className="mt-0.5 line-clamp-2 max-w-[60ch] text-[13px] tracking-tight text-black/55 dark:text-white/55">{a.summary}</div>}
                  <div className="mt-1.5 text-[12px] tracking-tight text-black/45 dark:text-white/45">
                    Предложил: {a.author.proposedBy || "—"}{a.author.anonymous && " (просил анонимность)"} · {a.date}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  <button onClick={() => updateArticle(a.id, { status: "published", reported: false })} className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-[#0056FF] px-2.5 text-[12px] tracking-tight text-white hover:bg-[#0049DB]"><Check size={13} /> Опубликовать</button>
                  <button onClick={() => editArticle(a)} className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-black/10 px-2.5 text-[12px] tracking-tight text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70"><Pencil size={13} /> Изменить</button>
                  <button onClick={() => updateArticle(a.id, { status: "rejected" })} className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-black/10 px-2.5 text-[12px] tracking-tight text-black/60 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/60"><X size={13} /> Отклонить</button>
                  {role === "admin" && a.author.proposerId ? (
                    <button onClick={() => toggleBlockedSubmitter(a.author.proposerId!)} className={`inline-flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-[12px] tracking-tight transition-colors ${blocked ? "border-emerald-500/40 text-emerald-600 hover:bg-emerald-500/[0.08] dark:text-emerald-400" : "border-red-500/40 text-red-500 hover:bg-red-500/[0.08]"}`}><Ban size={13} /> {blocked ? "Разблокировать" : "Заблокировать"}</button>
                  ) : (
                    <button onClick={() => updateArticle(a.id, { reported: !a.reported })} className={`inline-flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-[12px] tracking-tight transition-colors ${a.reported ? "border-amber-500/40 text-amber-600 dark:text-amber-400" : "border-black/10 text-black/60 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/60"}`}><Flag size={13} /> {a.reported ? "Жалоба отправлена" : "Пожаловаться"}</button>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    )
  );

  // ---- Admin reference sections (real data) ----
  const roleLabel = (r: string) => ({ citizen: "Гражданин", content_editor: "Редактор", platform_admin: "Администратор", editor: "Редактор", admin: "Администратор", guest: "Гость" } as Record<string, string>)[r] ?? r;
  const fmtDateTime = (v: string) => { const d = new Date(v); return isNaN(d.getTime()) ? v : d.toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }); };
  const sectionEmpty = (icon: React.ReactNode, title: string, note: string) => (
    <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
      <div>
        <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{icon}</div>
        <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{title}</div>
        <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">{note}</div>
      </div>
    </div>
  );

  const [catEditing, setCatEditing] = useState<string | null>(null);
  const [catDraft, setCatDraft] = useState("");
  const startCatEdit = (id: string, name: string) => { setCatEditing(id); setCatDraft(name); };
  const saveCat = (id: string) => { updateCategory(id, catDraft); setCatEditing(null); };
  const categoriesBody = (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div className="text-[13px] tracking-tight text-black/55 dark:text-white/55">{categories.length} категорий</div>
        <button
          onClick={() => { const n = window.prompt("Название новой категории"); if (n?.trim()) addCategory(n.trim()); }}
          className="inline-flex items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 py-2 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"
        >
          <Plus size={14} /> Категория
        </button>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {categories.map((c) => {
          const cnt = admin.scenarios.filter((s) => catLabel(s.category) === c.name).length + articles.filter((a) => a.category === c.name).length;
          const isEditing = catEditing === c.id;
          return (
            <Card key={c.id} className="p-4">
              <div className="flex items-start justify-between gap-1">
                <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"><LayoutGrid size={16} /></div>
                <button
                  onClick={() => { if (window.confirm(`Удалить категорию «${c.name}»?`)) deleteCategory(c.id); }}
                  className="grid h-6 w-6 place-items-center rounded-lg text-black/25 transition-colors hover:bg-red-500/10 hover:text-red-500 dark:text-white/25"
                  title="Удалить"
                >
                  <Trash2 size={13} />
                </button>
              </div>
              {isEditing ? (
                <div className="mt-2 flex items-center gap-1">
                  <input
                    autoFocus
                    value={catDraft}
                    onChange={(e) => setCatDraft(e.target.value)}
                    onBlur={() => saveCat(c.id)}
                    onKeyDown={(e) => { if (e.key === "Enter") saveCat(c.id); if (e.key === "Escape") setCatEditing(null); }}
                    className="min-w-0 flex-1 rounded-lg border border-[#0056FF] bg-white px-2 py-1 text-[13px] tracking-tight text-black outline-none dark:bg-white/[0.04] dark:text-white"
                  />
                </div>
              ) : (
                <div
                  className="mt-3 cursor-text tracking-tight text-black dark:text-white hover:text-[#0056FF] dark:hover:text-[#7FA8FF]"
                  onClick={() => startCatEdit(c.id, c.name)}
                  title="Нажмите, чтобы переименовать"
                >
                  {c.name}
                </div>
              )}
              <div className="mt-0.5 text-[12px] tracking-tight text-black/45 dark:text-white/45">{cnt} материалов</div>
            </Card>
          );
        })}
      </div>
    </div>
  );

  const authoritiesBody = <AuthoritiesEditor mobile={mobile} />;

  const regionsBody = <RegionsEditor mobile={mobile} />;

  // P11: значения — точно те, что принимает бэкенд (UserRoleUpdate pattern).
  // В UI подписи могут отличаться, но value идёт прямо в PATCH /users/{id}/role.
  const uniqueRoles = [
    { value: "citizen", label: "Гражданин" },
    { value: "content_editor", label: "Редактор" },
    { value: "platform_admin", label: "Администратор" },
  ];
  // Бэкенд для уже загруженных пользователей присылает role_id в этих же
  // терминах. Если когда-нибудь придёт локальный/мок-юзер с устаревшим
  // значением ("admin"/"editor") — смаппим в бэковое.
  const LEGACY_ROLE_MAP: Record<string, string> = {
    admin: "platform_admin",
    editor: "content_editor",
  };
  const roleValue = (raw: string) => {
    const normalized = LEGACY_ROLE_MAP[raw] ?? raw;
    return uniqueRoles.some(r => r.value === normalized) ? normalized : "citizen";
  };
  const usersBody = admin.users.length === 0 ? sectionEmpty(<Users size={20} />, "Доступно администратору", "Список пользователей и ролей виден только администратору платформы.") : (
    <Card className="p-0">
      <div className="overflow-x-auto [&::-webkit-scrollbar]:hidden">
        <table className="w-full min-w-[640px]">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-[0.12em] text-black/40 dark:text-white/40">
              <th className="px-5 py-3">Имя</th>
              <th className="py-3">Email</th>
              <th className="py-3">Роль</th>
              <th className="py-3">Статус</th>
              <th className="py-3 pr-5" />
            </tr>
          </thead>
          <tbody className="text-[13px] tracking-tight text-black dark:text-white">
            {admin.users.map((u) => (
              <tr key={u.id} className="border-t border-black/[0.05] dark:border-white/[0.05]">
                <td className="px-5 py-3.5">{u.name || "—"}</td>
                <td className="py-3.5 text-black/55 dark:text-white/55">{u.email}</td>
                <td className="py-3.5">
                  <select
                    value={roleValue(u.role)}
                    onChange={(e) => setAdminUserRole(u.id, e.target.value)}
                    className="rounded-lg border border-black/10 bg-white px-2 py-1 text-[12px] tracking-tight text-black outline-none dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
                  >
                    {uniqueRoles.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                  </select>
                </td>
                <td className="py-3.5">
                  <Pill tone={u.isActive ? "ok" : "warn"}>{u.isActive ? "Активен" : "Заблокирован"}</Pill>
                </td>
                <td className="whitespace-nowrap py-3.5 pr-5 text-right">
                  <div className="inline-flex items-center gap-2">
                    <button
                      onClick={() => setAdminUserActive(u.id, !u.isActive)}
                      disabled={u.email === currentUser.email}
                      title={u.email === currentUser.email ? "Нельзя заблокировать самого себя" : ""}
                      className={`inline-flex h-7 items-center gap-1.5 rounded-lg border px-2.5 text-[12px] tracking-tight transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${u.isActive ? "border-red-500/30 text-red-500 hover:bg-red-500/[0.08]" : "border-emerald-500/30 text-emerald-600 hover:bg-emerald-500/[0.08] dark:text-emerald-400"}`}
                    >
                      <Ban size={12} /> {u.isActive ? "Заблокировать" : "Разблокировать"}
                    </button>
                    <button
                      onClick={() => {
                        if (window.confirm(`Удалить пользователя ${u.email}? Это действие нельзя отменить.`)) {
                          deleteAdminUser(u.id);
                        }
                      }}
                      disabled={u.email === currentUser.email}
                      title={u.email === currentUser.email ? "Нельзя удалить самого себя" : ""}
                      className="inline-flex h-7 items-center gap-1.5 rounded-lg border border-black/10 px-2.5 text-[12px] tracking-tight text-black/55 transition-colors hover:border-red-500/40 hover:bg-red-500/[0.08] hover:text-red-500 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/10 dark:text-white/55"
                    >
                      <Trash2 size={12} /> Удалить
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );

  const auditBody = admin.auditLogs.length === 0 ? sectionEmpty(<Clock size={20} />, "Журнал пуст", "Действия редакторов и админов будут записываться здесь.") : (
    <div className="space-y-2.5">
      {admin.auditLogs.map((e) => (
        <Card key={e.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Pill tone={e.eventType === "delete" ? "warn" : e.eventType === "create" ? "ok" : "lavender"}>{e.eventType || "действие"}</Pill>
              <span className="truncate tracking-tight text-black dark:text-white">{e.action}</span>
            </div>
            <div className="mt-1 text-[12px] tracking-tight text-black/45 dark:text-white/45">{e.actor} · {roleLabel(e.roleId)}</div>
          </div>
          <span className="shrink-0 text-[12px] tabular-nums tracking-tight text-black/45 dark:text-white/45">{fmtDateTime(e.createdAt)}</span>
        </Card>
      ))}
    </div>
  );

  type RuleState = { enabled: boolean; days: number };
  const [ruleStates, setRuleStates] = useState<Record<string, RuleState>>(() => {
    try { const s = window.localStorage.getItem("belp.rules"); return s ? JSON.parse(s) : {}; } catch { return {}; }
  });
  const toggleRule = (key: string, def: RuleState) => {
    const next = { ...ruleStates, [key]: { ...(ruleStates[key] ?? def), enabled: !(ruleStates[key]?.enabled ?? def.enabled) } };
    setRuleStates(next);
    try { window.localStorage.setItem("belp.rules", JSON.stringify(next)); } catch { /* ok */ }
  };
  const setRuleDays = (key: string, def: RuleState, days: number) => {
    const next = { ...ruleStates, [key]: { ...(ruleStates[key] ?? def), days } };
    setRuleStates(next);
    try { window.localStorage.setItem("belp.rules", JSON.stringify(next)); } catch { /* ok */ }
  };
  const RULE_TYPES = [
    { key: "doc_expiry", l: "Истечение срока документа", d: "Уведомление за N дней до окончания срока.", daysLabel: "За сколько дней", def: { enabled: true, days: 60 } },
    { key: "tax_due", l: "Срок уплаты налога", d: "Напоминание о приближении срока уплаты.", daysLabel: "За сколько дней", def: { enabled: true, days: 14 } },
    { key: "utility_counter", l: "Показания счётчиков ЖКХ", d: "Ежемесячное напоминание о передаче показаний.", daysLabel: "День месяца (1-28)", def: { enabled: true, days: 25 } },
    { key: "situation_deadline", l: "Дедлайн по ситуации", d: "Напоминание о незавершённых задачах сценария.", daysLabel: "За сколько дней до дедлайна", def: { enabled: true, days: 3 } },
  ];
  const rulesBody = (
    <div className="space-y-3">
      <div className="mb-2 text-[13px] tracking-tight text-black/55 dark:text-white/55">
        Управление правилами автоматических уведомлений для всех пользователей.
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {RULE_TYPES.map((r) => {
          const st: RuleState = ruleStates[r.key] ?? r.def;
          return (
            <Card key={r.key} className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl transition-colors ${st.enabled ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "bg-black/[0.04] text-black/35 dark:bg-white/[0.04] dark:text-white/35"}`}>
                    <Bell size={16} />
                  </div>
                  <div>
                    <div className="tracking-tight text-black dark:text-white">{r.l}</div>
                    <div className="mt-0.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">{r.d}</div>
                  </div>
                </div>
                <div
                  role="switch"
                  aria-checked={st.enabled}
                  onClick={() => toggleRule(r.key, r.def)}
                  className={`relative mt-0.5 h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors ${st.enabled ? "bg-[#0056FF]" : "bg-black/20 dark:bg-white/20"}`}
                >
                  <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${st.enabled ? "translate-x-4" : "translate-x-0.5"}`} />
                </div>
              </div>
              {st.enabled && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{r.daysLabel}:</span>
                  <input
                    type="number"
                    min={1}
                    max={365}
                    value={st.days}
                    onChange={(e) => setRuleDays(r.key, r.def, Number(e.target.value) || r.def.days)}
                    className="w-16 rounded-lg border border-black/10 bg-white px-2 py-1 text-center text-[13px] tabular-nums tracking-tight text-black outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
                  />
                  <span className="text-[12px] tracking-tight text-black/45 dark:text-white/45">дней</span>
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );

  const content = (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/[0.06] bg-white/70 px-5 py-3.5 backdrop-blur dark:border-white/[0.06] dark:bg-[#0B0D13]/70 sm:px-7">
        <div>
          <div className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{editor ? "Редактор" : "Контент"} / {current.label}</div>
          <div className="mt-0.5 tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>{section === "scenarios" ? "Жизненные сценарии" : section === "dashboard" ? (editor ? "Обзор редакции" : "Обзор") : current.label}</div>
        </div>
        {section === "dashboard" && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 rounded-xl bg-[#F6F7FB] p-1 dark:bg-white/[0.04]">
              {([["7", "7 дней"], ["30", "30 дней"]] as const).map(([v, l]) => (
                <button key={v} onClick={() => setPeriod(v)} className={`rounded-lg px-3 py-1.5 text-[12px] tracking-tight transition-colors ${period === v ? "bg-white text-[#0056FF] shadow-sm dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/55 dark:text-white/55"}`}>{l}</button>
              ))}
            </div>
            <button onClick={() => openEditor("news")} className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"><Plus size={15} /> Новая публикация</button>
          </div>
        )}
        {section === "scenarios" && (
          <div className="flex items-center gap-2">
            <GhostButton className="h-9 px-3 text-[13px]">Импорт</GhostButton>
            <button onClick={() => openEditor("scenario")} className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"><Plus size={15} /> Новая ситуация</button>
          </div>
        )}
        {section === "publications" && (
          <button onClick={() => openEditor("news")} className="inline-flex h-9 items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"><Plus size={15} /> Новая публикация</button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-4 [&::-webkit-scrollbar]:hidden sm:p-7">
        {section === "dashboard" ? dashboardBody
          : section === "publications" ? publicationsBody
          : section === "moderation" ? moderationBody
          : section === "scenarios" ? scenariosBody
          : section === "categories" ? categoriesBody
          : section === "law" ? <LawEditor mobile={mobile} />
          : section === "authorities" ? authoritiesBody
          : section === "regions" ? regionsBody
          : section === "users" ? usersBody
          : section === "audit" ? auditBody
          : section === "rules" ? rulesBody
          : section === "extremist" ? extremistLinkBody
          : placeholderBody}
      </div>
    </div>
  );

  if (editing) {
    return (
      <div className={`overflow-hidden bg-[#F6F7FB] dark:bg-[#07080C] ${fill ? "h-full" : "rounded-[28px] border border-black/[0.06] shadow-[0_60px_140px_-40px_rgba(15,23,42,0.35)] dark:border-white/[0.06]"}`}>
        <ContentEditor
          kind={editing.kind}
          mode={editing.mode}
          initial={editing.initial}
          authorName={profile.name}
          uploadFile={uploadMedia}
          mobile={mobile}
          onClose={() => setEditing(null)}
          onSubmit={handleSubmit}
        />
      </div>
    );
  }

  return (
    <div className={`overflow-hidden bg-[#F6F7FB] dark:bg-[#07080C] ${fill ? "h-full" : "rounded-[28px] border border-black/[0.06] shadow-[0_60px_140px_-40px_rgba(15,23,42,0.35)] dark:border-white/[0.06]"}`}>
      {mobile ? (
        <div className="flex h-full flex-col">
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">{content}</div>
          <div className="shrink-0 border-t border-black/[0.06] bg-white pb-1.5 pt-2 dark:border-white/[0.06] dark:bg-[#0B0D13]">
            {(() => {
              const pages: typeof visible[] = [];
              for (let i = 0; i < visible.length; i += 4) pages.push(visible.slice(i, i + 4));
              return (
                <>
                  <div ref={navScrollRef} onScroll={onNavScroll} className="flex snap-x snap-mandatory overflow-x-auto scroll-smooth [&::-webkit-scrollbar]:hidden">
                    {pages.map((pg, pi) => (
                      <div key={pi} className="flex w-full shrink-0 snap-center justify-evenly px-2">
                        {pg.map(s => {
                          const on = section === s.id;
                          return (
                            <button key={s.id} onClick={() => setSection(s.id)} className={`flex flex-col items-center gap-0.5 rounded-xl px-2 py-1 ${on ? "text-[#0056FF] dark:text-[#7FA8FF]" : "text-black/55 dark:text-white/55"}`}>
                              <span className={`grid h-9 w-9 place-items-center rounded-xl transition-colors ${on ? "bg-[#E3E7FC] dark:bg-[#0E1A3A]" : ""}`}>{s.icon}</span>
                              <span className="text-[10px] tracking-tight">{s.short}</span>
                            </button>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                  {pages.length > 1 && (
                    <div className="mt-2 flex items-center justify-center gap-1.5">
                      {pages.map((_, pi) => (
                        <span key={pi} className={`h-1.5 rounded-full transition-all duration-300 ease-out ${pi === navPage ? "w-6 bg-[#0056FF]" : "w-2 bg-black/15 dark:bg-white/20"}`} />
                      ))}
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        </div>
      ) : (
        <div className={`grid grid-cols-[240px_1fr] ${fill ? "h-full" : "h-[680px]"}`}>
          <aside className="overflow-y-auto border-r border-black/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-[#0B0D13] [&::-webkit-scrollbar]:hidden">
            <div className="flex items-center gap-2">
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-black text-white tracking-tight">{editor ? "E" : "A"}</span>
              <span className="tracking-tight text-black dark:text-white">{editor ? "Редактор · Белпомощник" : "Админ · Белпомощник"}</span>
            </div>
            <div className="mt-6 space-y-1">
              <div className="px-3 pb-1.5 text-[10px] uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Контент</div>
              {visible.filter(s => !s.sys).map(s => <NavItem key={s.id} icon={s.icon} label={s.label} badge={s.badge} active={section === s.id} onClick={() => setSection(s.id)} />)}
            </div>
            {!editor && (
              <div className="mt-5 space-y-1">
                <div className="px-3 pb-1.5 text-[10px] uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Система</div>
                {visible.filter(s => s.sys).map(s => <NavItem key={s.id} icon={s.icon} label={s.label} active={section === s.id} onClick={() => setSection(s.id)} />)}
              </div>
            )}
          </aside>
          {content}
        </div>
      )}
    </div>
  );
}
