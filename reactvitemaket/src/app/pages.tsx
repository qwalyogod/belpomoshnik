import React, { useCallback, useContext, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useOutletContext, useParams } from "react-router";
import { ShellContext, MobileTopBar } from "./App";
import { useStore, DOC_TYPE_LABEL, maskDocumentNumber } from "./data/store";
import { cityForDistrict } from "./data/geo";
import {
  Search, FileText, Home, Building2, Briefcase, Hammer, Heart, Shield, Wallet,
  Plus, Check, Lock, MapPin, CalendarClock, ChevronRight, AlertCircle, Clock,
  ArrowUpRight, ArrowRight, X, ScanLine, Eye, EyeOff, Baby, Award, BookOpen, Star, Trash2,
  Bell, ChevronLeft, Edit3, Newspaper, Sparkles, ExternalLink, AlertTriangle, Camera, StickyNote, ListChecks, RefreshCw, ImagePlus
} from "lucide-react";
import { Card, Pill, PrimaryButton, GhostButton, Logo, LocationPicker, RegionSearch, DistrictSearch, CitySearch } from "./components/belp-ui";
import { motion } from "motion/react";
import {
  CategoryId, Problem, Scenario, UserDocument, ExtremistEntry, ExtremistCategory, ExtremistStatus, ExtremistContentType,
  EXTREMIST_CATEGORY_LABEL, EXTREMIST_STATUS_LABEL, EXTREMIST_CONTENT_TYPE_LABEL,
  NoteCategory, NOTE_CATEGORIES,
} from "./data/types";
import { OFFICIAL_SOURCES } from "./data/mock";
import { matchesQuery } from "./services/search";
import { apiClient } from "./services/api";
import { ProfileEditModal, ProposeButton, MyContributions, EditorialFeed, DocumentCardModal } from "./components/extra-screens";
import { AvatarCropper, validateAvatarFile } from "./components/avatar-cropper";

function PageSearch({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  return (
    <div className="flex h-11 items-center gap-2.5 rounded-2xl border border-black/[0.06] bg-white px-4 dark:border-white/[0.06] dark:bg-white/[0.04]">
      <Search size={16} className="shrink-0 text-black/40 dark:text-white/40" />
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="min-w-0 flex-1 bg-transparent text-[14px] tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
      {value && <button onClick={() => onChange("")} className="shrink-0 text-black/35 hover:text-black/60 dark:text-white/35"><X size={15} /></button>}
    </div>
  );
}

// Helper to get category icons
const CatIcon = ({ cat, size = 20 }: { cat: string, size?: number }) => {
  switch (cat) {
    case "family": return <Heart size={size} />;
    case "documents": return <FileText size={size} />;
    case "work": return <Briefcase size={size} />;
    case "housing": return <Home size={size} />;
    case "taxes": return <Wallet size={size} />;
    case "health": return <Hammer size={size} />;
    case "auto": return <MapPin size={size} />;
    default: return <FileText size={size} />;
  }
};

const catLabel = (id: string) => {
  return ({
    documents: "Документы", family: "Семья", work: "Работа", business: "ИП и бизнес",
    housing: "Жильё и ЖКХ", taxes: "Налоги", health: "Здоровье", auto: "Авто",
  } as Record<string,string>)[id] ?? id;
}

const employmentLabel = (id?: string) => {
  if (!id) return "—";
  return ({
    employee: "Наёмный работник", ip: "ИП", student: "Студент",
    pensioner: "Пенсионер", unemployed: "Безработный", self_employed: "Самозанятый",
  } as Record<string, string>)[id] ?? id;
};

const roleLabel = (id: string) => {
  return ({
    guest: "Гость",
    citizen: "Гражданин",
    editor: "Редактор",
    admin: "Администратор",
  } as Record<string,string>)[id] ?? id;
}

type CatalogMode = "all" | "problem" | "scenario";
type CatalogItem = {
  id: string;
  kind: "problem" | "scenario";
  title: string;
  category: CategoryId;
  description: string;
  meta: string;
  route: string;
};

const catalogModes: { id: CatalogMode; title: string; description: string }[] = [
  { id: "all", title: "Все", description: "Проблемы и жизненные сценарии" },
  { id: "problem", title: "Проблемы", description: "Быстрые справочные карточки" },
  { id: "scenario", title: "Жизненные сценарии", description: "Пошаговые личные планы" },
];

const normalizeCatalogMode = (value: string | null, fallback: CatalogMode): CatalogMode => {
  return value === "problem" || value === "scenario" || value === "all" ? value : fallback;
};

const scenarioTaskCount = (scenario: Scenario) => {
  return scenario.taskCount ?? scenario.stages.reduce((total, stage) => total + stage.tasks.length, 0);
};

const toCatalogItems = (problems: Problem[], scenarios: Scenario[]): CatalogItem[] => {
  const problemItems: CatalogItem[] = problems.map((problem) => ({
    id: problem.id,
    kind: "problem",
    title: problem.title,
    category: problem.category,
    description: problem.shortDescription,
    meta: `Быстрая справка · ${problem.steps.length} шагов`,
    route: `/problem-detail/${problem.id}`,
  }));
  const scenarioItems: CatalogItem[] = scenarios.map((scenario) => ({
    id: scenario.id,
    kind: "scenario",
    title: scenario.title,
    category: scenario.category,
    description: scenario.shortDescription,
    meta: `Пошаговый план · ${scenario.estimatedTime} · ${scenarioTaskCount(scenario)} задач`,
    route: `/scenarios/${scenario.id}`,
  }));
  return [...problemItems, ...scenarioItems];
};

export function CatalogPage() {
  const { isMobile } = useContext(ShellContext);
  const { scenarios, problems, categories } = useStore();
  const navigate = useNavigate();
  const location = useLocation();
  const initialParams = new URLSearchParams(location.search);
  const defaultMode = location.pathname.startsWith("/scenarios") ? "scenario" : "all";
  const [q, setQ] = useState("");
  const [activeCat, setActiveCat] = useState(() => initialParams.get("category") ?? "all");
  const [activeMode, setActiveMode] = useState<CatalogMode>(() => normalizeCatalogMode(initialParams.get("type"), defaultMode));

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const nextDefault = location.pathname.startsWith("/scenarios") ? "scenario" : "all";
    setQ(params.get("q") ?? "");
    setActiveCat(params.get("category") ?? "all");
    setActiveMode(normalizeCatalogMode(params.get("type"), nextDefault));
  }, [location.pathname, location.search]);

  const updateCatalogUrl = (next: { q?: string; category?: string; type?: CatalogMode }) => {
    const nextQuery = next.q ?? q;
    const nextCategory = next.category ?? activeCat;
    const nextMode = next.type ?? activeMode;
    setQ(nextQuery);
    setActiveCat(nextCategory);
    setActiveMode(nextMode);

    const params = new URLSearchParams();
    if (nextQuery.trim()) params.set("q", nextQuery.trim());
    if (nextCategory !== "all") params.set("category", nextCategory);
    if (nextMode !== "all") params.set("type", nextMode);
    const queryString = params.toString();
    navigate(`/catalog${queryString ? `?${queryString}` : ""}`, { replace: true });
  };

  const catalogItems = toCatalogItems(problems, scenarios);
  const filtered = catalogItems.filter(item => {
    if (activeMode !== "all" && item.kind !== activeMode) return false;
    if (activeCat !== "all" && item.category !== activeCat) return false;
    if (q && !matchesQuery(q, [item.title, item.description, catLabel(item.category), item.kind === "problem" ? "проблема" : "жизненный сценарий"])) return false;
    return true;
  });
  const pageTitle = activeMode === "problem" ? "Каталог проблем" : activeMode === "scenario" ? "Жизненные сценарии" : "Каталог помощи";
  const pageLead = activeMode === "problem"
    ? "Короткие справочные карточки для вопросов, где нужен быстрый ответ и список действий."
    : activeMode === "scenario"
      ? "Длительные жизненные сценарии: этапы, задачи, документы, сроки и персональный прогресс."
      : "Выберите короткую проблему или жизненный сценарий. Проблема даёт быстрый план, сценарий создаёт личную ситуацию с задачами.";
  const searchPlaceholder = activeMode === "problem" ? "Найти проблему" : activeMode === "scenario" ? "Найти сценарий" : "Найти проблему или сценарий";

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title={pageTitle} onBack={() => navigate(-1)} />
        <div className="px-5">
          <div className="mb-4 rounded-3xl border border-black/[0.06] bg-white p-4 dark:border-white/[0.06] dark:bg-[#0F1117]">
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>{pageTitle}</div>
            <div className="mt-1 text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">{pageLead}</div>
          </div>
          <div className="flex items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3 dark:border-white/[0.06] dark:bg-[#0F1117]">
            <Search size={16} className="text-black/40 dark:text-white/40" />
            <input placeholder={searchPlaceholder} value={q} onChange={e => updateCatalogUrl({ q: e.target.value })} className="flex-1 bg-transparent tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {catalogModes.map(mode => (
              <button key={mode.id} onClick={() => updateCatalogUrl({ type: mode.id })} className={`rounded-2xl px-3 py-2 text-center text-[12px] tracking-tight transition-colors ${activeMode === mode.id ? "bg-[#0056FF] text-white" : "bg-white text-black/65 dark:bg-white/[0.06] dark:text-white/65"}`}>
                {mode.title}
              </button>
            ))}
          </div>
          <div className="mt-3">
            <ProposeButton kind={activeMode === "problem" ? "problem" : "scenario"} className="w-full justify-center" />
          </div>
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden">
            <button onClick={() => updateCatalogUrl({ category: "all" })} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${activeCat==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
            {categories.map(c => (
              <button key={c.id} onClick={() => updateCatalogUrl({ category: c.id })} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${activeCat===c.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{c.name}</button>
            ))}
          </div>
          {filtered.length === 0 && <div className="mt-10 text-center text-[13px] text-black/55 dark:text-white/55">Материалы не найдены. Попробуйте изменить тип, категорию или запрос.</div>}
          <div className="mt-5 grid grid-cols-1 gap-3">
            {filtered.map((item, i) => (
              <button key={`${item.kind}-${item.id}`} onClick={() => navigate(item.route)} className="block text-left w-full">
                <Card interactive className="p-4 flex gap-4 items-center">
                  <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl"
                    style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>
                    <CatIcon cat={item.category} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[11px] text-[#0056FF] mb-1">{item.kind === "problem" ? "Проблема" : "Жизненный сценарий"} · {catLabel(item.category)}</div>
                    <div className="tracking-tight text-black dark:text-white leading-tight">{item.title}</div>
                    <div className="mt-1 line-clamp-2 text-[12px] tracking-tight text-black/50 dark:text-white/50">{item.meta}</div>
                  </div>
                </Card>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Desktop
  return (
    <div className="p-8">
      <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Каталог</div>
      <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>{pageTitle}</div>
      <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">
        {pageLead}
      </p>
      
      <div className="mt-6 grid max-w-[820px] grid-cols-3 gap-3">
        {catalogModes.map(mode => (
          <button key={mode.id} onClick={() => updateCatalogUrl({ type: mode.id })} className={`rounded-3xl border px-4 py-4 text-left transition-colors ${activeMode === mode.id ? "border-[#0056FF] bg-[#E3E7FC] text-[#0056FF] dark:border-[#7FA8FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "border-black/[0.06] bg-white text-black/70 hover:bg-black/[0.02] dark:border-white/[0.06] dark:bg-white/[0.04] dark:text-white/70 dark:hover:bg-white/[0.06]"}`}>
            <div className="text-[14px] font-medium tracking-tight">{mode.title}</div>
            <div className="mt-1 text-[12px] tracking-tight opacity-70">{mode.description}</div>
          </button>
        ))}
      </div>

      <div className="mt-6 flex gap-3 items-center max-w-[720px]">
        <div className="flex flex-1 items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3 dark:border-white/[0.06] dark:bg-[#0F1117]">
          <Search size={16} className="text-black/40 dark:text-white/40" />
          <input placeholder={searchPlaceholder} value={q} onChange={e => updateCatalogUrl({ q: e.target.value })} className="flex-1 bg-transparent tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
        </div>
        <ProposeButton kind={activeMode === "problem" ? "problem" : "scenario"} className="shrink-0 self-stretch" />
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <button onClick={() => updateCatalogUrl({ category: "all" })} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${activeCat==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
        {categories.map(c => (
          <button key={c.id} onClick={() => updateCatalogUrl({ category: c.id })} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${activeCat===c.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{c.name}</button>
        ))}
      </div>
      
      <div className="mt-8"><EditorialFeed kind={activeMode === "problem" ? "problem" : "scenario"} title={activeMode === "problem" ? "Проблемы от редакции и пользователей" : "Жизненные сценарии от редакции и пользователей"} /></div>
      {filtered.length === 0 && <div className="mt-10 text-[14px] text-black/55 dark:text-white/55">Материалы не найдены. Попробуйте изменить тип, категорию или запрос.</div>}
      
      <div className="mt-6 grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((item, i) => (
          <button key={`${item.kind}-${item.id}`} className="text-left" onClick={() => navigate(item.route)}>
            <Card interactive className="p-5 flex flex-col h-full">
              <div className="grid h-12 w-12 place-items-center rounded-2xl" style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>
                <CatIcon cat={item.category} />
              </div>
              <div className="mt-8 tracking-tight text-black dark:text-white" style={{ fontSize: 16, lineHeight: 1.2 }}>{item.title}</div>
              <div className="mt-1 text-[12px] tracking-tight text-[#0056FF]">{item.kind === "problem" ? "Проблема" : "Жизненный сценарий"} · {catLabel(item.category)}</div>
              <div className="mt-3 line-clamp-3 text-[13px] tracking-tight text-black/60 dark:text-white/60">{item.description}</div>
              <div className="mt-4 flex flex-col gap-1 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                <span>{item.meta}</span>
                <span>{item.kind === "problem" ? "Открыть карточку проблемы" : "Открыть сценарий"}</span>
              </div>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}

export function SituationsPage() {
  const { isMobile } = useContext(ShellContext);
  const { situations, scenarioById, situationProgress } = useStore();
  const navigate = useNavigate();
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");

  const filtered = situations.filter(s => {
    if (filter === "active" && s.status !== "in_progress") return false;
    if (filter === "done" && s.status !== "done") return false;
    const sc = scenarioById(s.scenarioId);
    if (!matchesQuery(query, [sc?.title, sc ? catLabel(sc.category) : ""])) return false;
    return true;
  });

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Мои ситуации" onBack={() => navigate(-1)} right={
          <button onClick={() => navigate('/catalog')} className="grid h-10 w-10 place-items-center rounded-full bg-[#0056FF] text-white shadow-sm"><Plus size={16} /></button>
        } />
        <div className="px-5">
          <div className="mb-3"><PageSearch value={query} onChange={setQuery} placeholder="Поиск по ситуациям" /></div>
          <div className="flex gap-2 overflow-x-auto pb-1 mb-4 [&::-webkit-scrollbar]:hidden">
            <button onClick={() => setFilter("all")} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${filter==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
            <button onClick={() => setFilter("active")} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${filter==="active" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Активные</button>
            <button onClick={() => setFilter("done")} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${filter==="done" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Завершенные</button>
          </div>
          
          {filtered.length === 0 && (
            <div className="mt-10 text-center">
              <div className="text-[13px] text-black/55 dark:text-white/55 mb-4">У вас пока нет ситуаций. Выберите сценарий, чтобы начать.</div>
              <PrimaryButton onClick={() => navigate('/catalog')}>Выбрать сценарий</PrimaryButton>
            </div>
          )}

          <div className="space-y-3">
            {filtered.map(s => {
              const sc = scenarioById(s.scenarioId);
              if (!sc) return null;
              const p = situationProgress(s);
              return (
                <button key={s.id} onClick={() => navigate(`/situations/${s.id}`)} className="block w-full text-left">
                  <Card interactive className="p-4">
                    <div className="flex items-center justify-between">
                      <Pill tone={s.status === "done" ? "ok" : "royal"}>{s.status === "done" ? "Завершено" : "В процессе"}</Pill>
                    </div>
                    <div className="mt-2 tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{sc.title}</div>
                    <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55 mt-1">{catLabel(sc.category)}</div>
                    <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
                      <div className="h-full rounded-full" style={{ width: `${p}%`, background: p === 100 ? "#10B981" : "linear-gradient(90deg,#0056FF,#2277FF)" }} />
                    </div>
                  </Card>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Desktop
  return (
    <div className="p-8">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Процессы</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Мои ситуации</div>
          <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">Следите за прогрессом и выполняйте задачи по шагам</p>
        </div>
        <PrimaryButton onClick={() => navigate('/catalog')} className="gap-2 px-5"><Plus size={16}/> Выбрать сценарий</PrimaryButton>
      </div>

      <div className="mt-6 max-w-[420px]"><PageSearch value={query} onChange={setQuery} placeholder="Поиск по ситуациям" /></div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button onClick={() => setFilter("all")} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${filter==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
        <button onClick={() => setFilter("active")} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${filter==="active" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Активные</button>
        <button onClick={() => setFilter("done")} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${filter==="done" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Завершенные</button>
      </div>

      {filtered.length === 0 && (
        <div className="mt-10 text-[14px] text-black/55 dark:text-white/55">Ситуации не найдены.</div>
      )}

      <div className="mt-6 grid grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map(s => {
          const sc = scenarioById(s.scenarioId);
          if (!sc) return null;
          const p = situationProgress(s);
          return (
            <button key={s.id} onClick={() => navigate(`/situations/${s.id}`)} className="text-left block w-full">
              <Card interactive className="p-5 h-full flex flex-col">
                <div className="flex items-center gap-2 mb-4">
                  <Pill tone={s.status === "done" ? "ok" : "royal"}>{s.status === "done" ? "Завершено" : "В процессе"}</Pill>
                  <span className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{p}%</span>
                </div>
                <div className="tracking-tight text-black dark:text-white flex-1" style={{ fontSize: 18, lineHeight: 1.2 }}>{sc.title}</div>
                <div className="mt-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">{catLabel(sc.category)}</div>
                <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
                  <div className="h-full rounded-full" style={{ width: `${p}%`, background: p === 100 ? "#10B981" : "linear-gradient(90deg,#0056FF,#2277FF)" }} />
                </div>
              </Card>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function DocumentsPage() {
  const { isMobile } = useContext(ShellContext);
  const { documents, settings, role } = useStore();
  const navigate = useNavigate();
  const context = useOutletContext<{ onAddDoc?: () => void }>();
  const onAddDoc = context?.onAddDoc ?? (() => undefined);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  // v0.3: открытая карточка документа (read-only preview + PDF upload)
  const [cardId, setCardId] = useState<string | null>(null);

  const filtered = documents.filter(d => {
    if (filter === "active" && d.status !== "active") return false;
    if (filter === "expired" && d.status !== "expired") return false;
    if (!matchesQuery(query, [d.title, d.number, DOC_TYPE_LABEL[d.type]])) return false;
    return true;
  });

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Документы" onBack={() => navigate(-1)} right={
          <button onClick={onAddDoc} className="grid h-10 w-10 place-items-center rounded-full bg-[#0056FF] text-white shadow-sm"><Plus size={16} /></button>
        } />
        <div className="px-5">
          <div className="mb-3 rounded-2xl border border-amber-200/60 bg-amber-50 px-3 py-2 text-[11px] leading-relaxed text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
            <strong className="font-medium">Демо-режим.</strong> Сканы не шифруются. Не загружайте реальные паспортные данные.
          </div>
          <div className="mb-3"><PageSearch value={query} onChange={setQuery} placeholder="Поиск по документам" /></div>
          <div className="flex gap-2 overflow-x-auto pb-1 mb-4 [&::-webkit-scrollbar]:hidden">
            <button onClick={() => setFilter("all")} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${filter==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
            <button onClick={() => setFilter("active")} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${filter==="active" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Активные</button>
            <button onClick={() => setFilter("expired")} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${filter==="expired" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Истекли</button>
          </div>

          <div className="space-y-3">
            {filtered.map((d) => (
              <button
                key={d.id}
                onClick={() => setCardId(d.id)}
                className="block w-full text-left"
              >
                <Card className="flex items-center gap-3 p-4">
                  <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                    <FileText size={18} />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="tracking-tight text-black dark:text-white truncate">{d.title}</div>
                    <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55 truncate">
                      {maskDocumentNumber(d.number, !settings.privacy.maskDocuments)}
                    </div>
                  </div>
                  {d.status === 'expired' ? (
                    <span className="text-[11px] text-red-500 bg-red-50 dark:bg-red-500/20 px-2 py-1 rounded">Истёк</span>
                  ) : d.expiresAt ? (
                    <span className="text-[11px] text-black/50 dark:text-white/50 px-2 py-1">до {d.expiresAt}</span>
                  ) : null}
                </Card>
              </button>
            ))}
            {filtered.length === 0 && <div className="text-center mt-8 text-[13px] text-black/55">Документы не найдены</div>}
          </div>
          
          <button onClick={onAddDoc} className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-black/15 bg-transparent py-4 text-[14px] tracking-tight text-black/55 dark:border-white/15 dark:text-white/55">
            <ScanLine size={16} /> Добавить документ
          </button>
        </div>
        <DocumentCardModal
          open={cardId !== null}
          onClose={() => setCardId(null)}
          docId={cardId}
          onEdit={role === "guest" ? undefined : (id) => context?.onAddDoc?.()}
        />
      </div>
    );
  }

  // Desktop
  return (
    <div className="p-8">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Хранилище</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Документы</div>
          <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">Храните данные документов и следите за сроками</p>
        </div>
        <PrimaryButton onClick={onAddDoc} className="gap-2 px-5"><Plus size={16}/> Добавить документ</PrimaryButton>
      </div>

      <div className="mt-5 rounded-2xl border border-amber-200/60 bg-amber-50 px-4 py-3 text-[12px] leading-relaxed text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
        <strong className="font-medium">Демо-режим.</strong> Сканы хранятся локально и не шифруются. Не загружайте реальные паспортные данные.
      </div>

      <div className="mt-6 max-w-[420px]"><PageSearch value={query} onChange={setQuery} placeholder="Поиск по документам" /></div>
      <div className="mt-4 flex flex-wrap gap-2">
        <button onClick={() => setFilter("all")} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${filter==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
        <button onClick={() => setFilter("active")} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${filter==="active" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Активные</button>
        <button onClick={() => setFilter("expired")} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${filter==="expired" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Истекли</button>
      </div>

      <div className="mt-6 grid grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map(d => (
          <button key={d.id} onClick={() => setCardId(d.id)} className="block text-left">
            <Card className="p-5">
              <div className="flex items-start justify-between">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                  <FileText size={18} />
                </div>
                {d.status === "expired" && <Pill tone="warn">Истёк</Pill>}
                {d.status === "expiring" && <Pill tone="warn">Скоро истекает</Pill>}
                {d.status === "active" && <Pill tone="ok">Активен</Pill>}
              </div>
              <div className="mt-4 tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{d.title}</div>
              <div className="mt-1 font-mono text-[13px] tracking-wider text-black/55 dark:text-white/55">
                {maskDocumentNumber(d.number, !settings.privacy.maskDocuments)}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-[12px] text-black/55 dark:text-white/55">
                <div><div>Выдан</div><div className="mt-0.5 text-black dark:text-white">{d.issuedAt}</div></div>
                {d.expiresAt && <div><div>Годен до</div><div className="mt-0.5 text-black dark:text-white">{d.expiresAt}</div></div>}
              </div>
              <div className="mt-4 flex gap-2">
                 <GhostButton className="flex-1 py-1.5 text-[12px]">Открыть</GhostButton>
              </div>
            </Card>
          </button>
        ))}
        {filtered.length === 0 && <div className="col-span-full mt-4 text-[14px] text-black/55 dark:text-white/55">Документы не найдены.</div>}
      </div>
      <DocumentCardModal
        open={cardId !== null}
        onClose={() => setCardId(null)}
        docId={cardId}
        onEdit={role === "guest" ? undefined : (id) => context?.onAddDoc?.()}
      />
    </div>
  );
}

export function LegalPage() {
  const { isMobile } = useContext(ShellContext);
  const { legal } = useStore();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const filtered = legal.filter(it => matchesQuery(query, [it.title, it.summary, catLabel(it.category), it.whoAffected]));

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Закон-апдейты" onBack={() => navigate(-1)} />
        <div className="px-5 space-y-3">
          <PageSearch value={query} onChange={setQuery} placeholder="Поиск по новостям" />
          <ProposeButton kind="news" className="w-full justify-center" />
          <EditorialFeed kind="news" />
          {filtered.map((it) => (
            <button key={it.id} onClick={() => navigate(`/law-detail/${it.id}`)} className="block w-full text-left">
              <Card interactive className="p-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <Pill tone="lavender">{catLabel(it.category)}</Pill>
                  {it.priority && <Pill tone="warn"><AlertCircle size={11} /> Важное</Pill>}
                </div>
                <div className="mt-2.5 tracking-tight text-black dark:text-white" style={{ fontSize: 16, lineHeight: 1.25 }}>{it.title}</div>
                <div className="mt-1 text-[13px] text-black/60 dark:text-white/60 line-clamp-2">{it.summary}</div>
                <div className="mt-3 flex items-center justify-between text-[12px] tracking-tight text-black/50 dark:text-white/50">
                  <span className="inline-flex items-center gap-1.5"><Clock size={12} /> {it.effectiveDate}</span>
                </div>
              </Card>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Правовые обновления</div>
      <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Закон-апдейты</div>
      <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">Коротко о важных изменениях, которые могут вас касаться.</p>

      <div className="mt-6 flex max-w-[640px] items-center gap-3">
        <div className="flex-1"><PageSearch value={query} onChange={setQuery} placeholder="Поиск по новостям" /></div>
        <ProposeButton kind="news" className="shrink-0" />
      </div>
      <div className="mt-8"><EditorialFeed kind="news" /></div>
      {filtered.length === 0 && <div className="mt-8 text-[14px] text-black/55 dark:text-white/55">Ничего не найдено.</div>}
      <div className="mt-6 grid grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((it) => (
          <button key={it.id} onClick={() => navigate(`/law-detail/${it.id}`)} className="text-left w-full block">
            <Card interactive className="p-5 h-full flex flex-col">
              <div className="flex items-center gap-2 flex-wrap mb-3">
                <Pill tone="lavender">{catLabel(it.category)}</Pill>
                {it.priority && <Pill tone="warn"><AlertCircle size={11} /> Важное</Pill>}
              </div>
              <div className="tracking-tight text-black dark:text-white flex-1" style={{ fontSize: 17, lineHeight: 1.25 }}>{it.title}</div>
              <div className="mt-2 text-[13px] text-black/60 dark:text-white/60">{it.summary}</div>
              <div className="mt-4 flex items-center justify-between text-[12px] tracking-tight text-black/50 dark:text-white/50">
                <span className="inline-flex items-center gap-1.5"><Clock size={12} /> с {it.effectiveDate}</span>
              </div>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}

const ONBOARDING_STEPS = [
  { icon: <Search size={22} />, badge: "01", title: "Найдите проблему", desc: "Опишите ситуацию или выберите готовую категорию." },
  { icon: <Check size={22} />, badge: "02", title: "Получите план", desc: "Белпомощник соберёт шаги, документы, сроки и куда обращаться." },
  { icon: <Bell size={22} />, badge: "03", title: "Следите за сроками", desc: "Напоминания помогут не пропустить задачи и документы." },
  { icon: <Award size={22} />, badge: "04", title: "Ведите прогресс", desc: "Отмечайте выполненное и смотрите, как ситуация движется к завершению." },
];

/* ============================================================
   v1.0: WelcomePage — лендинг для гостя (вместо обычного дашборда).
   Гость, зашедший на /, редиректится на /welcome и видит эту страницу.
   После регистрации/логина возвращается на / (дашборд).
   ============================================================ */
export function WelcomePage() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);

  const publicSteps = [
    { title: "Найдите проблему", desc: "Для быстрых вопросов откройте карточку: что сделать сейчас, какие документы нужны и куда обращаться.", icon: <Search size={20} /> },
    { title: "Выберите жизненный сценарий", desc: "Если ситуация длительная, создайте личный план с этапами, задачами и сроками.", icon: <FileText size={20} /> },
    { title: "Ведите прогресс", desc: "Отмечайте выполненное, храните документы и получайте напоминания о сроках.", icon: <Check size={20} /> },
  ];

  return (
    <div className="relative min-h-[100dvh] overflow-hidden bg-[#F6F7FB] text-black dark:bg-[#07080C] dark:text-white">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-x-0 top-0 h-[560px] bg-[radial-gradient(circle_at_18%_12%,rgba(0,86,255,0.18),transparent_34%),radial-gradient(circle_at_78%_24%,rgba(34,119,255,0.14),transparent_32%),linear-gradient(180deg,rgba(255,255,255,0.92),rgba(246,247,251,0.78)_46%,rgba(246,247,251,1))] dark:bg-[radial-gradient(circle_at_18%_12%,rgba(0,86,255,0.32),transparent_34%),radial-gradient(circle_at_78%_24%,rgba(127,168,255,0.12),transparent_32%),linear-gradient(180deg,rgba(7,8,12,0.96),rgba(7,8,12,0.86)_46%,rgba(7,8,12,1))]" />
        <div className="absolute left-1/2 top-28 h-px w-[min(980px,90vw)] -translate-x-1/2 bg-gradient-to-r from-transparent via-[#0056FF]/20 to-transparent" />
      </div>

      <div className="relative mx-auto max-w-[1240px] px-5 pb-24 pt-[calc(env(safe-area-inset-top)+1.5rem)] sm:px-8 lg:pt-[calc(env(safe-area-inset-top)+2rem)]">
        <section className="grid gap-10 pb-12 pt-4 lg:grid-cols-[minmax(0,1fr)_440px] lg:items-center lg:pb-20 lg:pt-10">
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-[#0056FF]/15 bg-[#E3E7FC] px-3 py-1.5 text-[12px] tracking-tight text-[#0056FF] dark:border-[#7FA8FF]/20 dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
              <Sparkles size={12} /> гражданский помощник · Беларусь
            </span>
            <h1 className="mt-6 max-w-[15ch] text-[40px] font-medium leading-[1.02] tracking-tight sm:text-[64px] lg:text-[76px]">
              Проблема превращается в <span className="bg-gradient-to-r from-[#0056FF] via-[#2277FF] to-[#7FA8FF] bg-clip-text text-transparent">понятный план</span>
            </h1>
            <p className="mt-6 max-w-[60ch] text-[16px] leading-relaxed tracking-tight text-black/65 dark:text-white/65 sm:text-[18px]">
              Белпомощник помогает разобраться с документами, сроками, учреждениями и личными задачами. Быстрая проблема открывается как справочная карточка, а жизненный сценарий превращается в вашу ситуацию с прогрессом.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <PrimaryButton onClick={() => navigate("/register")} className="px-7 sm:w-auto">Создать аккаунт</PrimaryButton>
              <GhostButton onClick={() => navigate("/login")} className="px-7">Войти</GhostButton>
            </div>

            <div className="mt-8 grid max-w-[680px] grid-cols-3 gap-3">
              {[
                ["3", "типа помощи"],
                ["24/7", "локальный доступ"],
                ["0.1", "beta-версия"],
              ].map(([value, label]) => (
                <div key={label} className="rounded-3xl border border-black/[0.06] bg-white/70 p-4 shadow-[0_16px_44px_-34px_rgba(15,23,42,0.5)] backdrop-blur dark:border-white/[0.08] dark:bg-white/[0.05]">
                  <div className="text-[24px] font-medium tracking-tight text-[#0056FF] dark:text-[#7FA8FF]">{value}</div>
                  <div className="mt-1 text-[12px] tracking-tight text-black/50 dark:text-white/50">{label}</div>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.08 }} className="relative">
            <div className="absolute -inset-4 rounded-[36px] bg-[#0056FF]/8 blur-2xl dark:bg-[#0056FF]/18" />
            <Card className="relative overflow-hidden p-5 sm:p-6">
              <div className="absolute right-0 top-0 h-40 w-40 rounded-bl-[72px] bg-[#E3E7FC] dark:bg-[#0E1A3A]" />
              <div className="relative">
                <div className="flex items-center justify-between">
                  <Pill tone="lavender">Пример личного плана</Pill>
                  <span className="text-[12px] tracking-tight text-black/40 dark:text-white/40">68%</span>
                </div>
                <h2 className="mt-5 max-w-[14ch] tracking-tight" style={{ fontSize: 30, lineHeight: 1.08 }}>Рождение ребёнка</h2>
                <p className="mt-2 text-[13px] leading-relaxed text-black/55 dark:text-white/55">
                  Этапы, задачи, документы, учреждения и напоминания собраны в один личный маршрут.
                </p>
                <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.08]">
                  <motion.div initial={{ width: 0 }} animate={{ width: "68%" }} transition={{ duration: 0.9, delay: 0.2 }} className="h-full rounded-full bg-[#0056FF]" />
                </div>
                <div className="mt-5 space-y-2.5">
                  {[
                    ["Получить медицинскую справку", "Выполнено", true],
                    ["Обратиться в ЗАГС", "Следующий шаг", false],
                    ["Подать заявление на пособие", "После свидетельства", false],
                  ].map(([title, status, done]) => (
                    <div key={title} className="flex items-center gap-3 rounded-2xl border border-black/[0.06] bg-white/80 p-3 dark:border-white/[0.06] dark:bg-white/[0.04]">
                      <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-xl ${done ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300" : "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"}`}>
                        {done ? <Check size={16} /> : <Clock size={16} />}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[13px] tracking-tight text-black dark:text-white">{title}</span>
                        <span className="block text-[11px] tracking-tight text-black/45 dark:text-white/45">{status}</span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </motion.div>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          {[
            { title: "Проблема", body: "Короткий справочный ответ: что сделать сейчас, какие документы нужны и куда обратиться.", icon: <AlertCircle size={18} /> },
            { title: "Жизненный сценарий", body: "Готовый пошаговый маршрут для длительной ситуации: этапы, задачи, сроки и источники.", icon: <FileText size={18} /> },
            { title: "Моя ситуация", body: "Личный экземпляр сценария, где можно отмечать задачи и видеть прогресс.", icon: <Check size={18} /> },
          ].map((item) => (
            <Card key={item.title} className="p-5">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{item.icon}</span>
              <div className="mt-5 tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>{item.title}</div>
              <p className="mt-2 text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">{item.body}</p>
            </Card>
          ))}
        </section>

        <section className="mt-16">
          <div className="flex flex-col justify-between gap-4 rounded-[32px] border border-black/[0.06] bg-white p-6 shadow-[0_24px_70px_-48px_rgba(15,23,42,0.5)] dark:border-white/[0.06] dark:bg-white/[0.04] sm:flex-row sm:items-end sm:p-8">
            <div>
              <div className="text-[12px] uppercase tracking-[0.14em] text-[#0056FF]">Доступно без регистрации</div>
              <h2 className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Каталог помощи и новости</h2>
              <p className="mt-2 max-w-[560px] text-[14px] leading-relaxed text-black/55 dark:text-white/55">
                Смотрите проблемы и жизненные сценарии в каталоге и читайте закон-апдейты простыми словами — всё открыто без аккаунта. Регистрация нужна только для личных планов, документов и напоминаний.
              </p>
            </div>
            <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
              <button onClick={() => navigate("/catalog")} className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[#0056FF] px-5 py-3 text-[14px] font-medium text-white shadow-[0_18px_42px_-22px_rgba(0,86,255,0.85)]">
                Открыть каталог <ArrowRight size={15} />
              </button>
              <button onClick={() => navigate("/news")} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-black/[0.08] bg-white px-5 py-3 text-[14px] font-medium tracking-tight text-black/70 transition-colors hover:bg-black/[0.03] dark:border-white/[0.1] dark:bg-white/[0.04] dark:text-white/70">
                Новости
              </button>
            </div>
          </div>
        </section>

        <section className="mt-16 grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
          <div className="text-[12px] uppercase tracking-[0.14em] text-[#0056FF]">Как это работает</div>
            <h2 className="mt-1 max-w-[12ch] tracking-tight text-black dark:text-white" style={{ fontSize: 34, lineHeight: 1.08 }}>Три шага до результата</h2>
            <p className="mt-3 max-w-[42ch] text-[14px] leading-relaxed text-black/55 dark:text-white/55">
              Пользовательский путь построен вокруг практического действия, а не вокруг длинного текста.
            </p>
          </div>
          <div className="space-y-3">
            {publicSteps.map((step, i) => (
              <button
                key={i}
                onClick={() => setActiveStep(i)}
                className={`flex w-full items-start gap-3 rounded-2xl border p-4 text-left transition-all ${activeStep === i ? "border-[#0056FF] bg-[#E3E7FC] dark:bg-[#0E1A3A]" : "border-black/[0.06] bg-white dark:border-white/[0.06] dark:bg-white/[0.04]"}`}
              >
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#0056FF] text-white">{step.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 15 }}>{i + 1}. {step.title}</div>
                  <div className="mt-0.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">{step.desc}</div>
                </div>
                <span className="text-[10px] uppercase tracking-[0.14em] text-black/30 dark:text-white/30">{String(i + 1).padStart(2, "0")}</span>
              </button>
            ))}
          </div>
        </section>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="mt-16 overflow-hidden rounded-[32px] border border-[#0056FF]/15 bg-white p-1 shadow-[0_32px_90px_-58px_rgba(0,86,255,0.7)] dark:border-[#7FA8FF]/15 dark:bg-white/[0.04]">
          <div
            className="grid gap-7 rounded-[26px] p-7 text-white sm:p-10 lg:grid-cols-[1fr_360px] lg:items-center"
            style={{ background: "radial-gradient(120% 100% at 0% 0%, #2277FF 0%, #0056FF 45%, #001A66 100%)" }}
          >
            <div>
              <div className="text-[12px] uppercase tracking-[0.14em] text-white/70">Готовы начать?</div>
              <h3 className="mt-2 max-w-[18ch] tracking-tight" style={{ fontSize: 34, lineHeight: 1.08 }}>
                Создайте личную ситуацию и ведите её по шагам.
              </h3>
              <p className="mt-3 max-w-[58ch] text-[14px] leading-relaxed text-white/80">
                Регистрация открывает сохранение прогресса, личные документы, уведомления и быстрый доступ к своим ситуациям.
              </p>
              <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                <button onClick={() => navigate("/register")} className="rounded-2xl bg-white px-6 py-3 text-[14px] font-semibold tracking-tight text-[#0056FF] shadow-[0_8px_24px_-8px_rgba(0,0,0,0.25)]">
                  Создать аккаунт
                </button>
                <button onClick={() => navigate("/login")} className="rounded-2xl border border-white/30 bg-white/10 px-6 py-3 text-[14px] font-semibold tracking-tight text-white backdrop-blur">
                  У меня уже есть аккаунт
                </button>
              </div>
            </div>
            <div className="rounded-3xl border border-white/15 bg-white/10 p-5 backdrop-blur">
              <div className="text-[13px] font-medium tracking-tight text-white">Справочный характер</div>
              <p className="mt-2 text-[12px] leading-relaxed text-white/75">
                Информация помогает ориентироваться, но перед подачей документов требования нужно уточнять на официальных ресурсах.
              </p>
            </div>
          </div>
        </motion.div>

        <div className="mt-12 flex flex-col items-center gap-2 text-[12px] text-black/40 dark:text-white/40 sm:flex-row sm:justify-between">
          <div>© 2026 Белпомощник · Беларусь</div>
          <div className="flex gap-4">
            <button onClick={() => navigate("/about")} className="hover:text-black dark:hover:text-white">О приложении</button>
            <button onClick={() => navigate("/login")} className="hover:text-black dark:hover:text-white">Войти</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const finish = (to: string) => {
    try { localStorage.setItem("belp.onboarded", "1"); } catch { /* ignore */ }
    navigate(to);
  };
  return (
    <div className="relative min-h-[100dvh] overflow-hidden">
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-[#0056FF]/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 top-40 h-80 w-80 rounded-full bg-[#2277FF]/10 blur-3xl" />
      <div className="relative mx-auto flex min-h-[100dvh] max-w-[1100px] flex-col justify-center px-5 pb-12 pt-[calc(env(safe-area-inset-top)+3rem)] sm:px-8">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="flex items-center justify-between">
            <Logo size={30} />
            <span className="rounded-full bg-[#E3E7FC] px-3 py-1.5 text-[12px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">mobile-first · РБ</span>
          </div>
          <h1 className="mt-10 max-w-[16ch] text-[34px] font-medium leading-[1.05] tracking-tight text-black dark:text-white sm:text-[52px]">
            Помощник, который превращает проблему в понятный план
          </h1>
          <p className="mt-4 max-w-[60ch] text-[15px] leading-relaxed tracking-tight text-black/60 dark:text-white/60 sm:text-[17px]">
            Найдите жизненную ситуацию, получите чек-лист, сроки, документы и напоминания без канцелярита. Паспорт, ЖКХ, налоги, прописка — по шагам.
          </p>
        </motion.div>

        <div className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {ONBOARDING_STEPS.map((s, i) => (
            <motion.div key={s.badge} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.1 + i * 0.08 }}>
              <Card className="flex h-full flex-col p-5">
                <div className="flex items-center justify-between">
                  <span className="grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{s.icon}</span>
                  <span className="text-[18px] font-semibold tracking-tight text-black/15 dark:text-white/20">{s.badge}</span>
                </div>
                <div className="mt-4 tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{s.title}</div>
                <div className="mt-1 text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">{s.desc}</div>
              </Card>
            </motion.div>
          ))}
        </div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.45 }} className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
          <PrimaryButton onClick={() => finish("/")} className="px-7 sm:w-auto">Начать</PrimaryButton>
          <GhostButton onClick={() => finish("/login")} className="px-7">У меня уже есть аккаунт</GhostButton>
        </motion.div>
      </div>
    </div>
  );
}

export function NewsPage() {
  const { isMobile } = useContext(ShellContext);
  const navigate = useNavigate();
  const { articles, legal } = useStore();
  const [preferredSourceIds, setPreferredSourceIds] = usePreferredSourceIds();

  // v0.7: объединяем «Новости» (статьи с kind='news') и «Закон-апдейты»
  // (массив legal) в одну ленту с фильтр-чипами. Подписка на закон-апдейты
  // уже есть в settings.notifications.legal.
  type FilterKey = "all" | "news" | "law";
  const [filter, setFilter] = useState<FilterKey>("all");
  // P6: фильтр по sourceId (id из OFFICIAL_SOURCES).
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [sourceQuery, setSourceQuery] = useState("");

  // Helper: sourceId для конкретной записи (news|article или law).
  // Для law: приоритет sourceIds[0], иначе матч OFFICIAL_SOURCES по домену url.
  // Для article: sourceIds[0] или sourceUrl-матч по домену.
  const resolveSourceId = (record: { sourceIds?: string[]; sourceUrl?: string; sourceUrlDomain?: string }): string | null => {
    if (record.sourceIds && record.sourceIds.length > 0) return record.sourceIds[0];
    const normalizeHost = (value: string): string => {
      const raw = value.trim();
      if (!raw) return "";
      try {
        const withProtocol = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
        return new URL(withProtocol).hostname.replace(/^www\./, "").toLowerCase();
      } catch {
        return raw.replace(/^https?:\/\//i, "").replace(/^www\./, "").split("/")[0].toLowerCase();
      }
    };
    const targetHost = normalizeHost(record.sourceUrlDomain ?? record.sourceUrl ?? "");
    if (!targetHost) return null;
    const hit = OFFICIAL_SOURCES.find((s) => {
      const sourceHost = normalizeHost(s.url);
      return targetHost === sourceHost || targetHost.endsWith(`.${sourceHost}`) || sourceHost.endsWith(`.${targetHost}`);
    });
    return hit?.id ?? null;
  };

  const newsList = articles
    .filter((a) => a.status === "published" && a.kind === "news")
    .map((a) => ({
      kind: "news" as const,
      id: a.id,
      title: a.title,
      summary: a.summary ?? "",
      date: a.publishedAt ?? a.updatedAt ?? "",
      sourceIds: a.sourceIds,
      sourceUrl: a.sourceUrl,
    }));

  const lawList = legal.map((l) => {
    const domain = (() => {
      try { return new URL(l.source.url).hostname.replace(/^www\./, ""); } catch { return l.source.url; }
    })();
    return {
      kind: "law" as const,
      id: l.id,
      title: l.title,
      summary: l.summary ?? "",
      date: l.effectiveDate ?? "",
      sourceUrl: l.source.url,
      sourceTitle: l.source.title,
      sourceUrlDomain: domain,
      sourceIds: l.sourceIds,
      priority: l.priority,
    };
  });

  // Привязка sourceId после построения, чтобы NewsCard показывал плашку источника.
  const enrichSource = <T extends { sourceIds?: string[]; sourceUrlDomain?: string; sourceUrl?: string }>(it: T): T & { sourceId: string | null } => {
    const sourceId = resolveSourceId(it);
    return { ...it, sourceId };
  };
  const newsWithSource = newsList.map(enrichSource);
  const lawWithSource = lawList.map(enrichSource);

  const baseCombined =
    filter === "news" ? newsWithSource
    : filter === "law" ? lawWithSource
    : [...newsWithSource, ...lawWithSource].sort((a, b) => (b.date ?? "").localeCompare(a.date ?? ""));

  // Применяем фильтр по источнику.
  const combined = sourceFilter
    ? baseCombined.filter(it => it.sourceId === sourceFilter)
    : baseCombined;

  // Приоритетная сортировка: preferred sources → выше.
  const preferredSet = new Set(preferredSourceIds);
  const sorted = preferredSourceIds.length === 0
    ? combined
    : [...combined].sort((a, b) => {
        const ap = a.sourceId && preferredSet.has(a.sourceId) ? 1 : 0;
        const bp = b.sourceId && preferredSet.has(b.sourceId) ? 1 : 0;
        if (ap !== bp) return bp - ap;
        return (b.date ?? "").localeCompare(a.date ?? "");
      });

  const filterCounts = {
    all: newsWithSource.length + lawWithSource.length,
    news: newsWithSource.length,
    law: lawWithSource.length,
  };

  const filterChips = ([
    { key: "all" as const, label: "Все" },
    { key: "news" as const, label: "Новости" },
    { key: "law" as const, label: "Закон-апдейт" },
  ]).map((c) => (
    <button
      key={c.key}
      onClick={() => setFilter(c.key)}
      className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${filter === c.key ? "bg-[#0056FF] text-white" : "bg-white text-black/70 hover:bg-black/[0.04] dark:bg-white/[0.06] dark:text-white/70 dark:hover:bg-white/[0.08]"}`}
    >
      {c.label} {filterCounts[c.key] > 0 ? <span className="ml-1 opacity-60">{filterCounts[c.key]}</span> : null}
    </button>
  ));
  const extremistChip = (
    <button
      type="button"
      onClick={() => navigate("/extremist")}
      className="shrink-0 rounded-full bg-red-50 px-3.5 py-2 text-[12px] tracking-tight text-red-700 transition-colors hover:bg-red-100 dark:bg-red-500/10 dark:text-red-200 dark:hover:bg-red-500/15"
    >
      Экстремистские материалы
    </button>
  );

  // P6: топ-3 источника, у которых есть хотя бы один материал.
  const sourceCount = new Map<string, number>();
  [...newsWithSource, ...lawWithSource].forEach(it => {
    if (!it.sourceId) return;
    sourceCount.set(it.sourceId, (sourceCount.get(it.sourceId) ?? 0) + 1);
  });
  const featuredSources = [...sourceCount.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([id]) => OFFICIAL_SOURCES.find(s => s.id === id))
    .filter((s): s is NonNullable<typeof s> => Boolean(s));
  const visibleSources = OFFICIAL_SOURCES.filter((s) =>
    matchesQuery(sourceQuery, [s.title, s.description, s.type, s.url]),
  );

  const sourcePills = (
    <div className="-mx-5 flex gap-2 overflow-x-auto px-5 pb-1 [&::-webkit-scrollbar]:hidden">
      <button
        onClick={() => setSourcesOpen(true)}
        className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${sourceFilter === null ? "bg-black text-white dark:bg-white dark:text-black" : "bg-white text-black/65 hover:bg-black/[0.04] dark:bg-white/[0.06] dark:text-white/65 dark:hover:bg-white/[0.08]"}`}
      >
        Все источники
      </button>
      {featuredSources.map(s => (
        <button
          key={s.id}
          onClick={() => setSourceFilter(prev => prev === s.id ? null : s.id)}
          className={`shrink-0 inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${sourceFilter === s.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 hover:bg-black/[0.04] dark:bg-white/[0.06] dark:text-white/70 dark:hover:bg-white/[0.08]"}`}
          title={s.description}
        >
          <span className={`grid h-4 w-4 shrink-0 place-items-center rounded-full ${sourceFilter === s.id ? "bg-white/20" : "bg-[#E3E7FC] dark:bg-[#0E1A3A]"}`}>
            <Shield size={9} className={sourceFilter === s.id ? "text-white" : "text-[#0056FF] dark:text-[#7FA8FF]"} />
          </span>
          <span className="max-w-[180px] truncate">{s.title}</span>
          {preferredSourceIds.includes(s.id) && <Star size={11} className={sourceFilter === s.id ? "text-white" : "text-amber-500"} fill="currentColor" />}
        </button>
      ))}
    </div>
  );

  const sourcesSection = (
    <div>
      <div className="mb-2 flex items-center justify-between pl-1">
        <div className="inline-flex items-center gap-1.5 text-[12px] tracking-tight text-black/45 dark:text-white/45">
          <Shield size={12} className="text-[#0056FF]" /> Официальные источники
        </div>
        {sourceFilter && (
          <button
            onClick={() => setSourceFilter(null)}
            className="text-[11px] tracking-tight text-black/45 underline-offset-2 hover:underline dark:text-white/45"
          >
            Сбросить
          </button>
        )}
      </div>
      {sourcePills}
    </div>
  );

  const sourcesModal = sourcesOpen && (
    <div className="fixed inset-0 z-[130] flex items-end justify-center bg-black/35 p-0 backdrop-blur-sm sm:items-center sm:p-4" onClick={() => setSourcesOpen(false)}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[88dvh] w-full max-w-[780px] overflow-y-auto rounded-t-[28px] bg-white p-5 shadow-2xl dark:bg-[#0F1117] sm:rounded-[28px] sm:p-6 [&::-webkit-scrollbar]:hidden"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="inline-flex items-center gap-1.5 text-[12px] uppercase tracking-[0.14em] text-[#0056FF]">
              <Shield size={13} /> Официальные источники
            </div>
            <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>
              Реестр источников
            </div>
            <p className="mt-1 max-w-[56ch] text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">
              Выберите источник, чтобы отфильтровать новости и закон-апдейты. Звёздочка поднимает материалы источника выше в ленте.
            </p>
          </div>
          <button onClick={() => setSourcesOpen(false)} className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-black/[0.04] text-black/65 dark:bg-white/[0.06] dark:text-white/70">
            <X size={15} />
          </button>
        </div>
        <div className="mt-5 flex flex-col gap-2 sm:flex-row">
          <div className="min-w-0 flex-1">
            <PageSearch value={sourceQuery} onChange={setSourceQuery} placeholder="Найти источник, ведомство или сайт" />
          </div>
          <button
            onClick={() => { setSourceFilter(null); setSourcesOpen(false); }}
            className="h-11 rounded-2xl border border-black/10 px-4 text-[13px] tracking-tight text-black/65 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/65 dark:hover:bg-white/[0.06]"
          >
            Показать все материалы
          </button>
        </div>
        <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {visibleSources.map((s) => {
            const selected = sourceFilter === s.id;
            const preferred = preferredSourceIds.includes(s.id);
            return (
              <div key={s.id} className={`rounded-2xl border p-4 transition-colors ${selected ? "border-[#0056FF] bg-[#E3E7FC]/70 dark:bg-[#0E1A3A]" : "border-black/[0.06] bg-white dark:border-white/[0.08] dark:bg-white/[0.03]"}`}>
                <div className="flex items-start justify-between gap-2">
                  <Pill tone="lavender">{SOURCE_TYPE_LABEL[s.type] ?? s.type}</Pill>
                  <button
                    onClick={() => setPreferredSourceIds(s.id)}
                    className={`grid h-8 w-8 place-items-center rounded-full ${preferred ? "bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300" : "bg-black/[0.04] text-black/35 dark:bg-white/[0.06] dark:text-white/35"}`}
                    title={preferred ? "Убрать из приоритетных" : "Сделать приоритетным"}
                  >
                    <Star size={15} fill={preferred ? "currentColor" : "none"} />
                  </button>
                </div>
                <div className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 15, lineHeight: 1.25 }}>{s.title}</div>
                <div className="mt-1 line-clamp-2 text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">{s.description}</div>
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                  <a href={s.url} target="_blank" rel="noreferrer" className="inline-flex min-w-0 items-center gap-1.5 text-[12px] tracking-tight text-[#0056FF]">
                    <ArrowUpRight size={13} />
                    <span className="truncate">{s.url.replace(/^https?:\/\//, "").replace(/\/$/, "")}</span>
                  </a>
                  <button
                    onClick={() => { setSourceFilter(s.id); setSourcesOpen(false); }}
                    className="rounded-xl bg-[#0056FF] px-3 py-1.5 text-[12px] tracking-tight text-white"
                  >
                    Фильтровать
                  </button>
                </div>
              </div>
            );
          })}
        </div>
        {visibleSources.length === 0 && (
          <div className="mt-5 rounded-2xl border border-dashed border-black/10 p-6 text-center text-[13px] tracking-tight text-black/45 dark:border-white/12 dark:text-white/45">
            Источники по запросу не найдены.
          </div>
        )}
      </div>
    </div>
  );

  const empty = combined.length === 0 && (
    <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
      <div>
        <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"><Newspaper size={20} /></div>
        <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>Пока нет материалов</div>
        <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">Редакционные публикации и закон-апдейты появятся здесь.</div>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Новости" onBack={() => navigate(-1)} />
        <div className="space-y-4 px-5">
          <ProposeButton kind="news" className="w-full justify-center" />
          {sourcesSection}
          <div className="flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden">
            {filterChips}
            {extremistChip}
          </div>
          <div className="grid grid-cols-1 gap-3 min-[560px]:grid-cols-2">
            {sorted.map((item, i) => (
              <NewsCard
                key={`${item.kind}-${i}-${item.title}`}
                item={item}
                navigate={navigate}
                source={item.sourceId ? OFFICIAL_SOURCES.find(s => s.id === item.sourceId) : undefined}
                onTogglePreferred={item.sourceId ? () => setPreferredSourceIds(item.sourceId!) : undefined}
                isPreferred={item.sourceId ? preferredSourceIds.includes(item.sourceId) : false}
              />
            ))}
          </div>
          {empty}
        </div>
        {sourcesModal}
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Лента</div>
      <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Новости и закон-апдейты</div>
      <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">Редакционные материалы и релевантные изменения в законодательстве, подобранные под профиль.</p>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <ProposeButton kind="news" />
        <div className="flex flex-wrap gap-2">
          {filterChips}
          {extremistChip}
        </div>
      </div>
      <div className="mt-6 max-w-[920px]">{sourcesSection}</div>
      <div className="mt-8 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {sorted.map((item, i) => (
          <NewsCard
            key={`${item.kind}-${i}-${item.title}`}
            item={item}
            navigate={navigate}
            source={item.sourceId ? OFFICIAL_SOURCES.find(s => s.id === item.sourceId) : undefined}
            onTogglePreferred={item.sourceId ? () => setPreferredSourceIds(item.sourceId!) : undefined}
            isPreferred={item.sourceId ? preferredSourceIds.includes(item.sourceId) : false}
          />
        ))}
      </div>
      {empty}
      {sourcesModal}
    </div>
  );
}

function NewsCard({
  item, navigate, source, onTogglePreferred, isPreferred,
}: {
  item:
    | { kind: "news"; id: string; title: string; summary: string; date: string; sourceId: string | null }
    | { kind: "law"; id: string; title: string; summary: string; date: string; sourceUrl?: string; priority?: boolean; sourceId: string | null; sourceTitle?: string };
  navigate: (path: string) => void;
  source?: { id: string; title: string; url: string; type: string };
  onTogglePreferred?: () => void;
  isPreferred?: boolean;
}) {
  const isLaw = item.kind === "law";
  // Карточка должна быть «кликабельной» (навигация на детальную), но внутри неё
  // живут настоящие <button> (звезда) и <a target="_blank"> (источник) — это
  // interactive content, который запрещено вкладывать в <button>. Используем
  // <div role="button"> + Enter/Space на keyDown для клавиатурной доступности.
  const go = () => navigate(isLaw ? `/law-detail/${item.id}` : "/news");
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={go}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } }}
      className="block w-full text-left cursor-pointer"
    >
      <Card className="flex h-full w-full flex-col p-5">
        <div className="flex items-center gap-2">
          <Pill tone={isLaw ? "warn" : "lavender"}>
            {isLaw ? "Закон-апдейт" : "Новость"}
          </Pill>
          {isLaw && item.priority && <Pill tone="warn"><AlertCircle size={11} /> Важное</Pill>}
        </div>
        <div className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 16, lineHeight: 1.25 }}>{item.title}</div>
        {item.summary && <div className="mt-1 line-clamp-3 text-[13px] tracking-tight text-black/55 dark:text-white/55">{item.summary}</div>}
        {/* P6: плашка источника */}
        {source && (
          <div className="mt-3 flex items-center gap-1.5 rounded-xl bg-[#F6F7FB] px-2.5 py-1.5 text-[11px] tracking-tight text-black/60 dark:bg-white/[0.04] dark:text-white/60">
            <Shield size={11} className="shrink-0 text-[#0056FF] dark:text-[#7FA8FF]" />
            <span className="min-w-0 flex-1 truncate">{source.title}</span>
            {onTogglePreferred && (
              <button
                onClick={(e) => { e.stopPropagation(); onTogglePreferred(); }}
                className={`shrink-0 grid h-5 w-5 place-items-center rounded-full transition-colors ${isPreferred ? "text-amber-500" : "text-black/25 hover:text-amber-500 dark:text-white/25"}`}
                title={isPreferred ? "Убрать из предпочтений" : "В предпочтения"}
                aria-label="Предпочтение источника"
              >
                <Star size={12} fill={isPreferred ? "currentColor" : "none"} />
              </button>
            )}
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="shrink-0 inline-flex items-center text-[#0056FF] hover:underline dark:text-[#7FA8FF]"
              title="Открыть источник"
            >
              <ArrowUpRight size={11} />
            </a>
          </div>
        )}
        <div className="mt-auto flex items-center justify-between gap-3 pt-3">
          {item.date && <div className="text-[11px] tracking-tight text-black/40 dark:text-white/40">{item.date}</div>}
          <span className="inline-flex items-center gap-1 text-[11px] tracking-tight text-[#0056FF]">
            Подробнее <ExternalLink size={11} />
          </span>
        </div>
      </Card>
    </div>
  );
}

/** P6: localStorage-хук для предпочтительных источников (без бэка). */
const PREFERRED_SOURCES_KEY = "belp.preferredSourceIds";
function usePreferredSourceIds(): [string[], (id: string) => void] {
  const [ids, setIds] = useState<string[]>(() => {
    try {
      const raw = window.localStorage.getItem(PREFERRED_SOURCES_KEY);
      const parsed = raw ? (JSON.parse(raw) as unknown) : [];
      return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === "string") : [];
    } catch { return []; }
  });
  const toggle = useCallback((id: string) => {
    setIds(prev => {
      const next = prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id];
      try { window.localStorage.setItem(PREFERRED_SOURCES_KEY, JSON.stringify(next)); } catch { /* ignore */ }
      return next;
    });
  }, []);
  return [ids, toggle];
}

const SOURCE_TYPE_LABEL: Record<string, string> = { law: "Закон", government_portal: "Госпортал", ministry: "Министерство", tax: "Налоги", registry: "Реестр" };

export function SourcesPage() {
  const { isMobile } = useContext(ShellContext);
  const navigate = useNavigate();
  const grid = (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {OFFICIAL_SOURCES.map((s) => (
        <a key={s.id} href={s.url} target="_blank" rel="noreferrer" className="block">
          <Card interactive className="flex h-full flex-col p-4">
            <div className="flex items-center justify-between gap-2">
              <Pill tone="lavender">{SOURCE_TYPE_LABEL[s.type] ?? s.type}</Pill>
              <span className="inline-flex items-center gap-1 text-[11px] tracking-tight text-emerald-600 dark:text-emerald-400"><Check size={11} /> проверен {s.lastChecked}</span>
            </div>
            <div className="mt-2.5 tracking-tight text-black dark:text-white" style={{ fontSize: 15, lineHeight: 1.25 }}>{s.title}</div>
            <div className="mt-1 line-clamp-2 text-[13px] tracking-tight text-black/55 dark:text-white/55">{s.description}</div>
            <div className="mt-auto pt-3 inline-flex items-center gap-1.5 text-[12px] tracking-tight text-[#0056FF]"><ArrowUpRight size={13} /> {s.url.replace(/^https?:\/\//, "").replace(/\/$/, "")}</div>
          </Card>
        </a>
      ))}
    </div>
  );

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Источники" onBack={() => navigate(-1)} />
        <div className="px-5 space-y-3">
          <p className="text-[13px] tracking-tight text-black/55 dark:text-white/55">Официальные источники, на которые опирается приложение.</p>
          {grid}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Справочно</div>
      <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Официальные источники</div>
      <p className="mt-2 max-w-[600px] tracking-tight text-black/60 dark:text-white/60">Государственные порталы и ведомства, на данные которых опирается «Белпомощник». Перед подачей документов уточняйте актуальные требования на официальных ресурсах.</p>
      <div className="mt-8">{grid}</div>
    </div>
  );
}

export function LawDetailPage() {
  const { isMobile } = useContext(ShellContext);
  const params = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { legal, publicContentStatus, publicContentError } = useStore();
  const item = legal.find(l => l.id === params?.id);
  const [retryNonce, setRetryNonce] = React.useState(0);
  // Если элемента нет в сторе, но мы ещё грузим — показываем скелетон.
  const isLoading = !item && publicContentStatus === "loading" && retryNonce === 0;
  // Если элемента нет и загрузка упала — показываем сообщение с кнопкой.
  const isMissing = !item && !isLoading;

  if (isLoading) {
    return (
      <div className={`${isMobile ? "h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden" : "p-8 max-w-[800px]"}`}>
        {isMobile ? (
          <MobileTopBar title="Детали" onBack={() => navigate(-1)} />
        ) : (
          <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55">
            <ChevronLeft size={14} /> Назад
          </button>
        )}
        <div className={isMobile ? "px-5" : ""}>
          <div className="mt-2 h-6 w-32 animate-pulse rounded-full bg-black/[0.06] dark:bg-white/[0.08]" />
          <div className="mt-4 h-8 w-3/4 animate-pulse rounded-lg bg-black/[0.06] dark:bg-white/[0.08]" />
          <div className="mt-3 h-4 w-1/3 animate-pulse rounded-md bg-black/[0.05] dark:bg-white/[0.06]" />
          <div className="mt-6 space-y-3">
            <div className="h-4 w-full animate-pulse rounded bg-black/[0.05] dark:bg-white/[0.06]" />
            <div className="h-4 w-5/6 animate-pulse rounded bg-black/[0.05] dark:bg-white/[0.06]" />
            <div className="h-4 w-2/3 animate-pulse rounded bg-black/[0.05] dark:bg-white/[0.06]" />
          </div>
          <div className="mt-4 text-[13px] tracking-tight text-black/45 dark:text-white/45">Загружаем материал…</div>
        </div>
      </div>
    );
  }

  if (isMissing) {
    return (
      <div className={`${isMobile ? "h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden" : "p-8 max-w-[800px]"}`}>
        {isMobile ? (
          <MobileTopBar title="Детали" onBack={() => navigate(-1)} />
        ) : (
          <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55">
            <ChevronLeft size={14} /> Назад
          </button>
        )}
        <div className={isMobile ? "px-5" : ""}>
          <div className="mt-6 grid place-items-center rounded-3xl border border-dashed border-black/10 p-10 text-center dark:border-white/12">
            <div>
              <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <Newspaper size={20} />
              </div>
              <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>
                Новость не найдена
              </div>
              <div className="mt-2 max-w-[420px] text-[13px] tracking-tight text-black/55 dark:text-white/55">
                {publicContentError
                  ? "Не удалось загрузить материалы с сервера. Проверьте подключение и попробуйте снова."
                  : "Этот материал пока недоступен. Возможно, он ещё не опубликован."}
              </div>
              <button
                onClick={() => setRetryNonce(n => n + 1)}
                className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-[#0056FF] px-4 py-2 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"
              >
                <RefreshCw size={13} /> Попробовать снова
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const lawBodyHtml = item?.bodyHtml?.trim();

  return (
    <div className={`${isMobile ? "h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden" : "p-8 max-w-[800px]"} space-y-6`}>
      {isMobile ? (
         <MobileTopBar title="Детали" onBack={() => navigate(-1)} />
      ) : (
        <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55">
          <ChevronLeft size={14} /> Назад
        </button>
      )}

      <div className={isMobile ? "px-5" : ""}>
        <div>
          <Pill tone="lavender">{catLabel(item!.category)}</Pill>
          <h1 className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: isMobile ? 26 : 32, lineHeight: 1.1 }}>{item!.title}</h1>
          <div className="mt-3 flex gap-4 text-[13px] text-black/55 dark:text-white/55">
            <span className="flex items-center gap-1.5"><Clock size={14} /> с {item!.effectiveDate}</span>
          </div>
        </div>

        {lawBodyHtml && (
          <Card className="mt-6 p-5">
            <div
              className="prose max-w-none text-[14px] leading-relaxed tracking-tight text-black/75 [&_h3]:mt-5 [&_h3]:text-[16px] [&_h3]:font-medium [&_h3]:text-black [&_li]:my-1 [&_ul]:pl-5 dark:text-white/75 dark:[&_h3]:text-white"
              dangerouslySetInnerHTML={{ __html: lawBodyHtml }}
            />
          </Card>
        )}

        <Card className="mt-6 p-5">
          <div className="font-medium text-[15px] mb-1">Что изменилось?</div>
          <p className="text-[14px] text-black/70 dark:text-white/70 leading-relaxed whitespace-pre-wrap">{item!.whatChanged || item!.summary}</p>

          <div className="mt-6 font-medium text-[15px] mb-1">Кого это касается?</div>
          <p className="text-[14px] text-black/70 dark:text-white/70 leading-relaxed whitespace-pre-wrap">{item!.whoAffected || "Всех граждан РБ"}</p>

          <div className="mt-6 font-medium text-[15px] mb-1">Что сделать?</div>
          <p className="text-[14px] text-black/70 dark:text-white/70 leading-relaxed whitespace-pre-wrap">{item!.whatToDo}</p>
        </Card>

        <div className="mt-6 rounded-2xl border border-amber-200/60 bg-amber-50 p-4 text-[13px] tracking-tight text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
          Материал основан на официальных источниках. Перед подачей документов сверяйте актуальную редакцию и требования на сайте первоисточника.
        </div>
      </div>
    </div>
  );
}

export function NotificationsPage() {
  const { isMobile } = useContext(ShellContext);
  const { notifications, markAllRead, markRead } = useStore();
  const navigate = useNavigate();

  const targetFor = (it: { kind: string; link?: { page: string; id?: string | number } }): string => {
    if (it.link?.page) {
      if (it.link.id != null) return `/${it.link.page}/${it.link.id}`;
      return `/${it.link.page}`;
    }
    switch (it.kind) {
      case "task_due":         return "/situations";
      case "step_done":        return "/situations";
      case "document_expiring": return "/documents";
      case "legal_update":     return "/news";
      default:                  return "/news";
    }
  };

  const onClickNotif = (it: { id: string; read: boolean; kind: string; link?: { page: string; id?: string | number } }) => {
    if (!it.read) markRead(it.id);
    navigate(targetFor(it));
  };

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Уведомления" onBack={() => navigate(-1)} right={
          <button onClick={markAllRead} className="grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"><Check size={15} className="text-black dark:text-white" /></button>
        } />
        <div className="px-5 space-y-3">
          {notifications.map((it) => (
            <button key={it.id} onClick={() => onClickNotif(it)} className="block w-full text-left">
              <Card className={`flex items-start gap-3 p-4 ${it.read ? 'opacity-60' : ''}`}>
                <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${
                  (it.kind === "task_due" || it.kind === "document_expiring") ? "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300" :
                  it.kind === "step_done" ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300" :
                  "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"
                }`}><Bell size={15} /></span>
                <div className="flex-1">
                  <div className="tracking-tight text-black dark:text-white leading-tight mb-1">{it.title}</div>
                  <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{it.body}</div>
                </div>
              </Card>
            </button>
          ))}
          {notifications.length === 0 && <div className="text-center mt-10 text-[13px] text-black/55 dark:text-white/55">Уведомлений пока нет.</div>}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-[800px]">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">События</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Уведомления</div>
        </div>
        <GhostButton onClick={markAllRead}>Прочитать все</GhostButton>
      </div>

      <div className="mt-6 space-y-3">
        {notifications.map((it) => (
          <button key={it.id} onClick={() => onClickNotif(it)} className="block w-full text-left">
            <Card className={`flex items-start gap-4 p-5 ${it.read ? 'opacity-60' : ''}`}>
              <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${
                (it.kind === "task_due" || it.kind === "document_expiring") ? "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300" :
                it.kind === "step_done" ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300" :
                "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"
              }`}><Bell size={18} /></span>
              <div className="flex-1">
                <div className="tracking-tight text-black dark:text-white font-medium">{it.title}</div>
                <div className="mt-1 text-[13px] tracking-tight text-black/60 dark:text-white/60">{it.body}</div>
                <div className="mt-3 text-[11px] text-black/40 dark:text-white/40">{it.createdAt}</div>
              </div>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ============================================================
   v1.1 (P4): подкомпоненты ProfilePage (аватар, заметки, адреса,
   предпочтения источников). Гость видит только базовый блок.
   ============================================================ */

function ProfileAvatar({ size = "lg" }: { size?: "lg" | "md" }) {
  const { profile, currentUser, uploadAvatar, removeAvatar } = useStore();
  const fileRef = useRef<HTMLInputElement>(null);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dim = size === "lg" ? "h-24 w-24" : "h-14 w-14";
  const fontSize = size === "lg" ? "text-3xl" : "text-lg";
  const canEdit = currentUser.role !== "guest";
  const avatar = profile?.avatarDataUrl;
  // Если аватарки нет — показываем первую букву имени на синем фоне.
  // Fallback: имя → первая буква email → нейтральный «П».
  const initial = (() => {
    const trimmed = (profile?.name ?? currentUser.name ?? "").trim();
    if (trimmed) return trimmed[0]!.toUpperCase();
    const mail = (profile?.email ?? currentUser.email ?? "").trim();
    if (mail) {
      const at = mail.indexOf("@");
      const head = (at > 0 ? mail.slice(0, at) : mail).trim();
      if (head) return head[0]!.toUpperCase();
    }
    return "П";
  })();

  const onFile = (file?: File | null) => {
    if (!file) return;
    const validationError = validateAvatarFile(file);
    if (validationError) { setError(validationError); return; }
    setError(null);
    setPendingFile(file); // открываем редактор-кропер
  };

  const handleRemove = async () => {
    setMenuOpen(false);
    setError(null);
    setBusy(true);
    try { await removeAvatar(); }
    catch (e) { setError(e instanceof Error ? e.message : "Не удалось удалить фото."); }
    finally { setBusy(false); }
  };

  return (
    <div className="flex flex-col items-center gap-1.5">
      {/* relative-обёртка — якорь для контекстного меню (вне overflow-hidden круга) */}
      <div className="relative">
        <div className={`relative shrink-0 ${dim} rounded-full overflow-hidden bg-gradient-to-br from-[#0056FF] to-[#2277FF] flex items-center justify-center text-white ${fontSize} font-medium`}>
          {avatar
            ? <img src={avatar} alt="avatar" className="h-full w-full object-cover" />
            : <span>{initial}</span>}
          {canEdit && (
            <button
              onClick={() => setMenuOpen(v => !v)}
              className="absolute inset-0 grid place-items-center bg-black/35 opacity-0 transition-opacity hover:opacity-100"
              title="Изменить фото"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
            >
              <Camera size={size === "lg" ? 22 : 16} className="text-white" />
            </button>
          )}
        </div>

        {canEdit && (
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => { onFile(e.target.files?.[0] || null); e.target.value = ""; }}
          />
        )}

        {/* Контекстное меню: выбрать новое фото / удалить текущее */}
        {menuOpen && (
          <>
            <div className="fixed inset-0 z-[90]" onClick={() => setMenuOpen(false)} />
            <div role="menu" className="absolute left-0 top-[calc(100%+8px)] z-[95] w-52 rounded-2xl border border-black/[0.08] bg-white p-1.5 shadow-[0_24px_60px_-30px_rgba(15,23,42,0.5)] dark:border-white/[0.08] dark:bg-[#0F1117]">
              <button
                role="menuitem"
                onClick={() => { setMenuOpen(false); fileRef.current?.click(); }}
                className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.04] dark:text-white dark:hover:bg-white/[0.05]"
              >
                <ImagePlus size={16} className="text-black/45 dark:text-white/45" /> Выбрать новое фото
              </button>
              {avatar && (
                <button
                  role="menuitem"
                  onClick={handleRemove}
                  className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-[14px] tracking-tight text-red-500 transition-colors hover:bg-red-50 dark:hover:bg-red-500/10"
                >
                  <Trash2 size={16} /> Удалить фото
                </button>
              )}
            </div>
          </>
        )}
      </div>

      {busy && <span className="text-[11px] text-black/40 dark:text-white/40">Сохранение…</span>}
      {error && <span className="max-w-[180px] text-center text-[11px] leading-tight text-red-500">{error}</span>}

      {pendingFile && (
        <AvatarCropper
          file={pendingFile}
          onCancel={() => setPendingFile(null)}
          onApply={async (blob) => {
            await uploadAvatar(blob);   // бросит ошибку → покажется в кропере
            setPendingFile(null);       // успех → закрываем
          }}
        />
      )}
    </div>
  );
}

function ProfileNotes() {
  const { notes, addNote, toggleNote, removeNote } = useStore();
  const [showAll, setShowAll] = useState(false);
  const [adding, setAdding] = useState(false);
  const [draftText, setDraftText] = useState("");
  const [draftCategory, setDraftCategory] = useState<NoteCategory>("Общее");
  const [draftDate, setDraftDate] = useState("");

  const active = notes.filter(n => !n.done)
    .sort((a, b) => (a.reminderAt || "9999").localeCompare(b.reminderAt || "9999"));
  const visible = showAll ? active : active.slice(0, 3);

  const submit = () => {
    const text = draftText.trim();
    if (!text) return;
    addNote({ text, category: draftCategory, reminderAt: draftDate || undefined });
    setDraftText("");
    setDraftDate("");
    setDraftCategory("Общее");
    setAdding(false);
  };

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <StickyNote size={15} className="text-[#0056FF]" />
          <div className="font-medium text-[15px] text-black dark:text-white">Заметки</div>
          {notes.length > 0 && <span className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{active.length} активных</span>}
        </div>
        <div className="flex items-center gap-2">
          {active.length > 3 && (
            <button onClick={() => setShowAll(s => !s)} className="text-[12px] tracking-tight text-[#0056FF] hover:underline">
              {showAll ? "Свернуть" : "Все"}
            </button>
          )}
          <button onClick={() => setAdding(s => !s)} className="inline-flex h-8 items-center gap-1 rounded-full bg-[#0056FF] px-3 text-[12px] text-white">
            <Plus size={13} /> Заметка
          </button>
        </div>
      </div>

      {adding && (
        <div className="mb-3 rounded-2xl border border-black/[0.06] bg-black/[0.02] p-3 dark:border-white/[0.06] dark:bg-white/[0.04]">
          <textarea
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            placeholder="Что нужно не забыть?"
            rows={2}
            className="w-full resize-none bg-transparent text-[14px] tracking-tight text-black placeholder:text-black/40 outline-none dark:text-white dark:placeholder:text-white/40"
          />
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <select
              value={draftCategory}
              onChange={(e) => setDraftCategory(e.target.value as NoteCategory)}
              className="rounded-lg border border-black/10 bg-white px-2 py-1 text-[12px] tracking-tight dark:border-white/10 dark:bg-white/[0.04] dark:text-white"
            >
              {NOTE_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <input
              type="date"
              value={draftDate}
              onChange={(e) => setDraftDate(e.target.value)}
              className="rounded-lg border border-black/10 bg-white px-2 py-1 text-[12px] tracking-tight dark:border-white/10 dark:bg-white/[0.04] dark:text-white"
            />
            <div className="ml-auto flex gap-2">
              <button onClick={() => setAdding(false)} className="rounded-lg px-2 py-1 text-[12px] text-black/55 dark:text-white/55">Отмена</button>
              <button onClick={submit} disabled={!draftText.trim()} className="rounded-lg bg-[#0056FF] px-3 py-1 text-[12px] text-white disabled:opacity-50">Сохранить</button>
            </div>
          </div>
        </div>
      )}

      {visible.length === 0 ? (
        <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Пока пусто. Нажмите «Заметка», чтобы добавить напоминание.</div>
      ) : (
        <ul className="space-y-2">
          {visible.map((n) => (
            <li key={n.id} className="flex items-start gap-2 rounded-2xl border border-black/[0.05] bg-black/[0.015] p-2.5 dark:border-white/[0.06] dark:bg-white/[0.03]">
              <button
                onClick={() => toggleNote(n.id)}
                className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-md border border-black/15 dark:border-white/15"
                title="Отметить выполненной"
              >
                {n.done && <Check size={12} className="text-[#0056FF]" />}
              </button>
              <div className="min-w-0 flex-1">
                <div className={`text-[13px] tracking-tight ${n.done ? "text-black/40 line-through dark:text-white/40" : "text-black dark:text-white"}`}>{n.text}</div>
                <div className="mt-0.5 flex flex-wrap items-center gap-2 text-[11px] tracking-tight text-black/50 dark:text-white/50">
                  <Pill tone="ghost">{n.category}</Pill>
                  {n.reminderAt && <span>до {n.reminderAt}</span>}
                </div>
              </div>
              <button onClick={() => removeNote(n.id)} className="shrink-0 text-black/30 hover:text-red-500 dark:text-white/30" title="Удалить">
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function ProfileAddresses() {
  const { profile, currentUser, addAddress, updateAddress, removeAddress } = useStore();
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ label: "", region: "", district: "", city: "", street: "" });
  const seeded = useRef(false);
  const list = profile?.addresses ?? [];
  const canAdd = list.length < 5;

  // v1.3: авто-seed основного адреса из `currentUser.region/city/district`,
  // если addresses[] пуст и в currentUser есть данные. Делаем только один раз.
  useEffect(() => {
    if (seeded.current) return;
    if (list.length > 0) { seeded.current = true; return; }
    const region = currentUser.region;
    const city = currentUser.city;
    const district = currentUser.district;
    if (region || city) {
      seeded.current = true;
      addAddress({
        label: "Основной",
        region: region || "",
        district: district || "",
        city: city || "",
        street: "",
        isPrimary: true,
      });
    }
  }, [currentUser.region, currentUser.city, currentUser.district, list.length, addAddress]);

  const reset = () => { setForm({ label: "", region: "", district: "", city: "", street: "" }); };

  const submit = () => {
    if (!form.region && !form.city) return;
    addAddress({ ...form, isPrimary: list.length === 0 });
    reset();
    setAdding(false);
  };

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <MapPin size={15} className="text-[#0056FF]" />
          <div className="font-medium text-[15px] text-black dark:text-white">Адреса</div>
          <span className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{list.length}/5</span>
        </div>
        {canAdd && (
          <button onClick={() => { setAdding(s => !s); reset(); }} className="inline-flex h-8 items-center gap-1 rounded-full bg-[#0056FF] px-3 text-[12px] text-white">
            <Plus size={13} /> Добавить
          </button>
        )}
      </div>

      {adding && (
        <div className="mb-3 rounded-2xl border border-black/[0.06] bg-black/[0.02] p-3 dark:border-white/[0.06] dark:bg-white/[0.04]">
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <input value={form.label} onChange={(e) => setForm(f => ({ ...f, label: e.target.value }))} placeholder="Метка (Дом, Работа, Дача)" className="rounded-lg border border-black/10 bg-white px-3 py-2 text-[13px] tracking-tight dark:border-white/10 dark:bg-white/[0.04] dark:text-white" />
            <div>
              <RegionSearch
                value={form.region}
                onChange={(next) => setForm(f => ({ ...f, region: next, district: "", city: "" }))}
              />
            </div>
            <div>
              <DistrictSearch
                region={form.region}
                value={form.district}
                onChange={(next) => setForm(f => ({ ...f, district: next, city: cityForDistrict(f.region, next) }))}
              />
            </div>
            <div>
              <CitySearch
                region={form.region}
                district={form.district}
                value={form.city}
                onChange={(next) => setForm(f => ({ ...f, city: next }))}
              />
            </div>
            <input value={form.street} onChange={(e) => setForm(f => ({ ...f, street: e.target.value }))} placeholder="Улица, дом, квартира" className="rounded-lg border border-black/10 bg-white px-3 py-2 text-[13px] tracking-tight sm:col-span-2 dark:border-white/10 dark:bg-white/[0.04] dark:text-white" />
          </div>
          <div className="mt-2 flex gap-2">
            <button onClick={() => { setAdding(false); reset(); }} className="rounded-lg px-3 py-1 text-[12px] text-black/55 dark:text-white/55">Отмена</button>
            <button onClick={submit} className="ml-auto rounded-lg bg-[#0056FF] px-3 py-1 text-[12px] text-white">Сохранить</button>
          </div>
        </div>
      )}

      {list.length === 0 ? (
        <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Адресов пока нет. Добавьте основной, чтобы быстро заполнять документы.</div>
      ) : (
        <ul className="space-y-2">
          {list.map((a) => (
            <li key={a.id} className="flex items-start gap-2 rounded-2xl border border-black/[0.05] bg-black/[0.015] p-3 dark:border-white/[0.06] dark:bg-white/[0.03]">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <div className="text-[14px] tracking-tight text-black dark:text-white">{a.label || "Без метки"}</div>
                  {a.isPrimary && <Pill tone="ok">Основной</Pill>}
                </div>
                <div className="mt-0.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                  {[a.region, a.district, a.city, a.street].filter(Boolean).join(" · ") || "—"}
                </div>
              </div>
              {!a.isPrimary && (
                <button
                  onClick={() => updateAddress(a.id, { isPrimary: true })}
                  className="shrink-0 text-[12px] tracking-tight text-[#0056FF] hover:underline"
                  title="Сделать основным"
                >
                  Сделать основным
                </button>
              )}
              <button onClick={() => removeAddress(a.id)} className="shrink-0 text-black/30 hover:text-red-500 dark:text-white/30" title="Удалить">
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function ProfileSourcePreferences() {
  // Шарим состояние с NewsPage через P6-овский хук usePreferredSourceIds —
  // так звёздочки в ленте и птички в профиле всегда синхронизированы.
  const [preferredSourceIds, togglePreferredSource] = usePreferredSourceIds();
  const selected = new Set(preferredSourceIds);
  // По умолчанию свёрнуто — список из 17 источников занимает много места
  // в профиле. Раскрывается по тапу на заголовок.
  const [expanded, setExpanded] = useState(false);
  return (
    <Card className="p-5">
      <button
        type="button"
        onClick={() => setExpanded(v => !v)}
        className="flex w-full items-center gap-2 text-left"
        aria-expanded={expanded}
        aria-controls="profile-source-preferences-list"
      >
        <ListChecks size={15} className="text-[#0056FF] shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-[15px] text-black dark:text-white">Источники новостей</span>
            <span className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{selected.size} выбрано</span>
          </div>
          {!expanded && (
            <p className="text-[12px] tracking-tight text-black/55 dark:text-white/55 mt-1">Нажмите, чтобы выбрать предпочтительные источники для ленты «Новости».</p>
          )}
        </div>
        <ChevronRight
          size={16}
          className={`shrink-0 text-black/40 dark:text-white/40 transition-transform duration-200 ${expanded ? "rotate-90" : ""}`}
        />
      </button>
      {expanded && (
        <>
          <p className="text-[12px] tracking-tight text-black/55 dark:text-white/55 mt-3 mb-3">Выбранные источники будут показываться выше в ленте «Новости».</p>
          <div id="profile-source-preferences-list" className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {OFFICIAL_SOURCES.map((s) => {
              const on = selected.has(s.id);
              return (
                <label
                  key={s.id}
                  className={`flex items-start gap-2 rounded-2xl border p-2.5 cursor-pointer transition-colors ${on ? "border-[#0056FF] bg-[#E3E7FC] dark:bg-[#0E1A3A]" : "border-black/[0.05] hover:border-black/15 dark:border-white/[0.06] dark:hover:border-white/15"}`}
                >
                  <input
                    type="checkbox"
                    checked={on}
                    onChange={() => togglePreferredSource(s.id)}
                    className="mt-1 h-4 w-4 accent-[#0056FF]"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px] tracking-tight text-black dark:text-white truncate">{s.title}</div>
                    <div className="text-[11px] tracking-tight text-black/50 dark:text-white/50 truncate">{s.url.replace(/^https?:\/\//, "")}</div>
                  </div>
                </label>
              );
            })}
          </div>
        </>
      )}
    </Card>
  );
}

export function ProfilePage() {
  const { isMobile, openAdmin } = useContext(ShellContext);
  const { profile, currentUser } = useStore();
  const navigate = useNavigate();
  const [editOpen, setEditOpen] = useState(false);
  const canEdit = currentUser.role !== "guest";
  const isStaff = currentUser.role === "platform_admin" || currentUser.role === "content_editor" || currentUser.role === "admin" || currentUser.role === "editor";

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <ProfileEditModal open={editOpen} onClose={() => setEditOpen(false)} />
        <MobileTopBar title="Профиль" onBack={() => navigate(-1)} right={
          canEdit ? <button onClick={() => setEditOpen(true)} className="grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"><Edit3 size={15} className="text-black dark:text-white" /></button> : undefined
        } />
        <div className="px-5 space-y-4">
          <Card className="flex items-center gap-4 p-4">
            <ProfileAvatar size="md" />
            <div className="flex-1 min-w-0">
              <div className="tracking-tight text-black dark:text-white truncate" style={{ fontSize: 17 }}>{profile?.name}</div>
              <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55 truncate">{profile?.city} · {profile?.region}</div>
            </div>
          </Card>

          <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45 pl-1">Личные данные</div>
          <Card className="p-4 space-y-3 text-[13px]">
            <div className="flex justify-between"><span className="text-black/55 dark:text-white/55">Email</span><span className="text-black dark:text-white truncate ml-2">{profile?.email}</span></div>
            <div className="flex justify-between"><span className="text-black/55 dark:text-white/55">Роль</span><span className="text-black dark:text-white">{roleLabel(currentUser.role)}</span></div>
          </Card>

          {canEdit && (
            <>
              <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45 pl-1">Заметки</div>
              <ProfileNotes />

              <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45 pl-1">Адреса</div>
              <ProfileAddresses />

              <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45 pl-1">Источники</div>
              <ProfileSourcePreferences />
            </>
          )}

          <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45 pl-1">Настройки и прочее</div>
          <Card className="p-2">
            <button onClick={() => navigate('/settings')} className="flex w-full items-center justify-between p-3 text-left">
              <span className="text-[14px] text-black dark:text-white">Настройки приложения</span>
              <ChevronRight size={16} className="text-black/30 dark:text-white/30" />
            </button>
            <button onClick={() => navigate('/learning')} className="flex w-full items-center justify-between p-3 text-left border-t border-black/5 dark:border-white/5">
              <span className="text-[14px] text-black dark:text-white">Обучение</span>
              <ChevronRight size={16} className="text-black/30 dark:text-white/30" />
            </button>
            {isStaff && (
              <button onClick={openAdmin} className="flex w-full items-center justify-between p-3 text-left border-t border-black/5 dark:border-white/5">
                <span className="text-[14px] text-[#0056FF]">{currentUser.role === "content_editor" || currentUser.role === "editor" ? "Редактор контента" : "Админ-панель"}</span>
                <ChevronRight size={16} className="text-[#0056FF]/50" />
              </button>
            )}
          </Card>
          <MyContributions />
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-[920px]">
      <ProfileEditModal open={editOpen} onClose={() => setEditOpen(false)} />
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Аккаунт</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Профиль</div>
        </div>
        {canEdit && <GhostButton className="gap-2 px-4" onClick={() => setEditOpen(true)}><Edit3 size={15} /> Редактировать</GhostButton>}
      </div>

      <div className="mt-8 flex items-center gap-6">
        <ProfileAvatar size="lg" />
        <div>
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 24 }}>{currentUser.role === "guest" ? "Гость" : profile?.name}</div>
          <div className="mt-1 text-[14px] text-black/60 dark:text-white/60">{currentUser.role === "guest" ? "Войдите, чтобы сохранять личные данные" : profile?.email}</div>
          <div className="mt-2 text-[13px] text-[#0056FF]">{profile?.city}, {profile?.region}</div>
        </div>
      </div>

      <div className="mt-10 grid grid-cols-2 gap-6">
        <Card className="p-5">
          <div className="font-medium text-[15px] mb-4">Персонализация</div>
          <div className="space-y-3 text-[13px]">
            <div className="flex justify-between border-b border-black/5 dark:border-white/5 pb-2"><span className="text-black/55 dark:text-white/55">Статус занятости</span><span className="text-black dark:text-white">{employmentLabel(profile?.employment)}</span></div>
            <div className="flex justify-between border-b border-black/5 dark:border-white/5 pb-2"><span className="text-black/55 dark:text-white/55">Дети</span><span className="text-black dark:text-white">{profile?.flags?.hasChildren ? "Есть" : "Нет"}</span></div>
            <div className="flex justify-between border-b border-black/5 dark:border-white/5 pb-2"><span className="text-black/55 dark:text-white/55">Авто</span><span className="text-black dark:text-white">{profile?.flags?.hasCar ? "Есть" : "Нет"}</span></div>
            <div className="flex justify-between pb-1"><span className="text-black/55 dark:text-white/55">Жильё</span><span className="text-black dark:text-white">{profile?.flags?.homeowner ? "Собственник" : profile?.flags?.tenant ? "Арендатор" : "—"}</span></div>
          </div>
          {profile?.interests && profile.interests.length > 0 && (
            <div className="mt-4">
              <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45 mb-2">Интересы</div>
              <div className="flex flex-wrap gap-1.5">
                {profile.interests.map(t => <span key={t} className="rounded-full bg-[#E3E7FC] px-2.5 py-1 text-[12px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{t}</span>)}
              </div>
            </div>
          )}
        </Card>

        <div className="space-y-4">
          <Card interactive className="p-4 flex justify-between items-center cursor-pointer" onClick={() => navigate('/settings')}>
             <div>
               <div className="text-[15px] text-black dark:text-white">Настройки</div>
               <div className="text-[12px] text-black/55 dark:text-white/55">Тема, уведомления, язык</div>
             </div>
             <ChevronRight size={18} className="text-black/30 dark:text-white/30" />
          </Card>
          <Card interactive className="p-4 flex justify-between items-center cursor-pointer" onClick={() => navigate('/learning')}>
             <div>
               <div className="text-[15px] text-black dark:text-white">Обучение</div>
               <div className="text-[12px] text-black/55 dark:text-white/55">Ваши тесты и достижения</div>
             </div>
             <ChevronRight size={18} className="text-black/30 dark:text-white/30" />
          </Card>
        </div>
      </div>

      {canEdit && (
        <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ProfileNotes />
          <ProfileAddresses />
        </div>
      )}

      {canEdit && (
        <div className="mt-6">
          <ProfileSourcePreferences />
        </div>
      )}

      <div className="mt-8"><MyContributions /></div>
    </div>
  );
}

export function ProblemDetailPage() {
  const { isMobile } = useContext(ShellContext);
  const params = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { problemById, toggleFavorite, favorites, isAuthenticated } = useStore();
  const item = problemById(params?.id || "");
  const [checks, setChecks] = useState<Record<string, boolean>>({});

  if (!item) return <div className="p-10">Проблема не найдена</div>;

  const total = item.steps.length;
  const done = item.steps.filter(s => checks[s.id]).length;
  const progress = total ? Math.round((done / total) * 100) : 0;
  const isFav = favorites.includes(item.id);
  const onCreatePlan = () => {
    if (!isAuthenticated) {
      navigate(`/login?redirect=/problems/${item.id}&reason=create-plan`);
    } else {
      navigate("/catalog?from=" + item.id);
    }
  };
  const onToggleFav = () => toggleFavorite(item.id);

  return (
    <div className={`${isMobile ? "h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden" : "p-8 max-w-[800px]"} space-y-6`}>
      {isMobile ? (
         <MobileTopBar title="Решение проблемы" onBack={() => navigate(-1)} />
      ) : (
        <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55 hover:text-black dark:hover:text-white transition-colors">
          <ChevronLeft size={14} /> Назад
        </button>
      )}
      
      <div className={isMobile ? "px-5" : ""}>
        <div>
          <Pill tone="lavender">{catLabel(item.category)}</Pill>
          <h1 className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: isMobile ? 26 : 32, lineHeight: 1.1 }}>{item.title}</h1>
          <p className="mt-3 text-[14px] text-black/60 dark:text-white/60">{item.shortDescription}</p>
        </div>

        <Card className="mt-6 p-5 border border-amber-200/60 bg-amber-50 dark:border-amber-500/20 dark:bg-amber-500/10">
          <div className="flex gap-2 items-center text-amber-900 dark:text-amber-200 font-medium mb-1 tracking-tight text-[15px]">
            <AlertCircle size={16} /> Что делать прямо сейчас
          </div>
          <p className="text-[14px] text-amber-800 dark:text-amber-200/80 leading-relaxed mt-2">{item.whatToDoNow}</p>
        </Card>

        <Card className="mt-5 p-5">
          <div className="flex items-center justify-between text-[13px] tracking-tight text-black/55 dark:text-white/55 mb-3 font-medium">
            <span>Пошаговый план ({done} из {total})</span>
            <span>{progress}%</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06] mb-5">
            <motion.div initial={false} animate={{ width: `${progress}%` }} transition={{ duration: 0.3 }} className="h-full rounded-full bg-[#0056FF]" />
          </div>

          <div className="space-y-4">
            {item.steps.map((st, i) => (
              <label key={st.id} className="flex gap-3 items-start cursor-pointer group">
                <div className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors ${checks[st.id] ? "bg-[#0056FF] border-[#0056FF] text-white" : "border-black/20 bg-black/5 dark:border-white/20 dark:bg-white/5 group-hover:border-black/40 dark:group-hover:border-white/40"}`}>
                  {checks[st.id] && <Check size={12} strokeWidth={3} />}
                </div>
                <div className={`text-[14px] leading-snug transition-colors ${checks[st.id] ? "text-black/40 dark:text-white/40 line-through" : "text-black dark:text-white"}`}>
                  {i+1}. {st.title}
                </div>
                <input type="checkbox" className="hidden" checked={!!checks[st.id]} onChange={e => setChecks(c => ({...c, [st.id]: e.target.checked}))} />
              </label>
            ))}
          </div>
        </Card>

        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-5">
            <div className="text-[14px] tracking-tight font-medium mb-3 text-black dark:text-white flex items-center gap-2">
              <FileText size={16} className="text-[#0056FF]" /> Документы
            </div>
            <ul className="list-disc pl-4 space-y-1.5 text-[14px] text-black/70 dark:text-white/70">
              {item.documents.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </Card>
          <Card className="p-5">
            <div className="text-[14px] tracking-tight font-medium mb-3 text-black dark:text-white flex items-center gap-2">
              <Clock size={16} className="text-[#0056FF]" /> Сроки
            </div>
            <ul className="list-disc pl-4 space-y-1.5 text-[14px] text-black/70 dark:text-white/70">
              {item.deadlines.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
          </Card>
        </div>

        <Card className="mt-5 p-5">
            <div className="text-[14px] tracking-tight font-medium mb-3 text-black dark:text-white flex items-center gap-2">
              <Building2 size={16} className="text-[#0056FF]" /> Куда обращаться
            </div>
            <ul className="list-disc pl-4 space-y-1.5 text-[14px] text-black/70 dark:text-white/70">
              {item.institutions.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
        </Card>

        <Card className="mt-5 p-5 border border-red-100 bg-red-50 dark:border-red-900/30 dark:bg-red-900/10">
            <div className="text-[14px] tracking-tight font-medium mb-3 text-red-800 dark:text-red-200 flex items-center gap-2">
              <AlertCircle size={16} /> Частые ошибки
            </div>
            <ul className="list-disc pl-4 space-y-1.5 text-[14px] text-red-700/80 dark:text-red-200/80">
              {item.mistakes.map((d, i) => <li key={i}>{d}</li>)}
            </ul>
        </Card>

        <div className="mt-8 flex flex-col sm:flex-row gap-3">
          <PrimaryButton onClick={onCreatePlan} className="flex-1 text-[14px]">
            Создать персональный план
          </PrimaryButton>
          <GhostButton onClick={onToggleFav} className="flex-1 text-[14px]">
            {isFav ? "★ В избранном" : "Сохранить в избранное"}
          </GhostButton>
        </div>

        <div className="mt-4 flex items-center gap-2 text-[11px] text-black/45 dark:text-white/45">
          <Pill tone="warn">Черновик</Pill>
          <span>Источник: открытые данные РБ. Перед подачей документов сверяйтесь с актуальными редакциями НПА.</span>
        </div>
      </div>
    </div>
  );
}

// Поле пароля с кнопкой показать/скрыть (глазик). Используется на входе и
// регистрации, чтобы пользователь мог проверить введённый пароль.
function PasswordInput({
  value, onChange, placeholder, onKeyDown,
}: { value: string; onChange: (v: string) => void; placeholder: string; onKeyDown?: (e: React.KeyboardEvent) => void }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        type={show ? "text" : "password"}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 pr-12 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]"
      />
      <button
        type="button"
        tabIndex={-1}
        onClick={() => setShow((s) => !s)}
        aria-label={show ? "Скрыть пароль" : "Показать пароль"}
        className="absolute right-2 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-lg text-black/40 transition-colors hover:text-black/70 dark:text-white/40 dark:hover:text-white/70"
      >
        {show ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
  );
}

export function LoginPage() {
  const navigate = useNavigate();
  const { quickAccounts, signInAs, signInWithEmail } = useStore();
  const [email, setEmail] = useState("citizen@test.local");
  const [password, setPassword] = useState("Test12345!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = () => {
    if (loading) return;
    setLoading(true);
    setError("");
    window.setTimeout(() => {
      const ok = signInWithEmail(email, password);
      setLoading(false);
      if (ok) {
        navigate("/");
        return;
      }
      setError("Проверьте email и пароль. Для тестовых аккаунтов пароль: Test12345!");
    }, 120);
  };

  const handleGuest = () => {
    signInAs("guest");
    navigate("/");
  };

  const quickLogin = (id: string) => {
    signInAs(id);
    navigate("/");
  };

  return (
    <div className="relative mx-auto grid min-h-[100dvh] w-full max-w-[1120px] items-center overflow-hidden bg-[#F6F7FB] p-4 dark:bg-[#0B0D13] lg:min-h-[calc(100dvh-150px)] lg:rounded-[34px] lg:grid-cols-[minmax(0,1fr)_420px] lg:gap-6 lg:p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(0,86,255,0.14),transparent_30%),radial-gradient(circle_at_88%_80%,rgba(34,119,255,0.10),transparent_32%)]" />
      <AuthAside mode="login" />
      <div className="relative z-10 flex justify-center">
      <Card className="w-full max-w-[420px] border-0 p-6 shadow-[0_24px_80px_-48px_rgba(15,23,42,0.55)] sm:p-8">
        <div className="mb-6 flex justify-center">
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-[#0056FF] to-[#2277FF] text-white shadow-sm">
              <Shield size={16} />
            </div>
            <span className="text-xl font-medium tracking-tight text-black dark:text-white">Белпомощник</span>
          </div>
        </div>
        <h1 className="mb-2 text-center text-2xl font-medium tracking-tight text-black dark:text-white">Вход в аккаунт</h1>
        <p className="mb-6 text-center text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">
          Откройте свои ситуации, документы и уведомления.
        </p>
        
        <div className="space-y-4">
          <div>
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
          </div>
          <div>
            <PasswordInput placeholder="Пароль" value={password} onChange={setPassword} onKeyDown={(e) => { if (e.key === "Enter") handleLogin(); }} />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="remember" className="rounded text-[#0056FF] w-4 h-4 cursor-pointer" />
            <label htmlFor="remember" className="text-[13px] text-black/60 dark:text-white/60 cursor-pointer">Запомнить меня</label>
          </div>
          {error && <div className="rounded-xl bg-red-50 px-3.5 py-2.5 text-[12px] text-red-700 dark:bg-red-500/10 dark:text-red-200">{error}</div>}
          
          <PrimaryButton onClick={handleLogin} className="w-full py-3.5 text-[15px]">{loading ? "Проверяем..." : "Войти"}</PrimaryButton>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-2">
          {quickAccounts.filter(account => account.isTestAccount).map(account => (
            <button key={account.id} onClick={() => quickLogin(account.id)} className="flex items-center justify-between rounded-xl border border-black/[0.06] bg-black/[0.02] px-3.5 py-2.5 text-left text-[13px] tracking-tight transition-colors hover:bg-[#E3E7FC] dark:border-white/[0.06] dark:bg-white/[0.03] dark:hover:bg-[#0E1A3A]">
              <span className="text-black dark:text-white">{account.name}</span>
              <span className="text-black/45 dark:text-white/45">{roleLabel(account.role)}</span>
            </button>
          ))}
        </div>

        <div className="mt-6 flex flex-col items-center gap-4">
          <button onClick={() => navigate("/register")} className="text-[14px] text-[#0056FF] hover:underline">Зарегистрироваться</button>
          <button onClick={handleGuest} className="text-[14px] text-black/50 dark:text-white/50 hover:underline">Продолжить как гость</button>
        </div>
      </Card>
      </div>
    </div>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const { registerUser } = useStore();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [loc, setLoc] = useState({ region: "Минская область", district: "Минский район", city: "Минск" });
  const [error, setError] = useState("");

  const handleRegister = () => {
    setError("");
    if (!name.trim() || !email.trim() || password.length < 6) {
      setError("Заполните имя, email и пароль минимум из 6 символов.");
      return;
    }
    if (password !== repeat) {
      setError("Пароли не совпадают.");
      return;
    }
    registerUser({ name, email, password, region: loc.region, city: loc.city });
    navigate("/");
  };

  return (
    <div className="relative mx-auto grid min-h-[100dvh] w-full max-w-[1120px] items-center overflow-hidden bg-[#F6F7FB] p-4 dark:bg-[#0B0D13] lg:min-h-[calc(100dvh-150px)] lg:rounded-[34px] lg:grid-cols-[minmax(0,1fr)_440px] lg:gap-6 lg:p-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_18%_24%,rgba(0,86,255,0.14),transparent_32%),radial-gradient(circle_at_86%_76%,rgba(34,119,255,0.10),transparent_34%)]" />
      <AuthAside mode="register" />
      <div className="relative z-10 flex justify-center py-2 lg:max-h-[calc(100dvh-190px)] lg:overflow-y-auto [&::-webkit-scrollbar]:hidden">
        <Card className="h-fit w-full max-w-[440px] border-0 p-6 shadow-[0_24px_80px_-48px_rgba(15,23,42,0.55)] sm:p-8">
          <div className="mb-6 flex justify-center">
            <div className="flex items-center gap-2">
              <div className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-[#0056FF] to-[#2277FF] text-white shadow-sm">
                <Shield size={16} />
              </div>
              <span className="text-xl font-medium tracking-tight text-black dark:text-white">Белпомощник</span>
            </div>
          </div>
          <h1 className="mb-2 text-center text-2xl font-medium tracking-tight text-black dark:text-white">Создание аккаунта</h1>
          <p className="mb-6 text-center text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">
            Заполните базовые данные, чтобы сохранить личные планы и подсказки по региону.
          </p>
          
          <div className="space-y-4">
            <input type="text" placeholder="Имя и фамилия" value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
            <PasswordInput placeholder="Пароль" value={password} onChange={setPassword} />
            <PasswordInput placeholder="Повтор пароля" value={repeat} onChange={setRepeat} />
            <LocationPicker value={loc} onChange={setLoc} className="!grid-cols-1" />
            <p className="text-[11px] tracking-tight text-black/40 dark:text-white/40">Регион и город нужны, чтобы подсказывать ближайшие учреждения.</p>
            {error && <div className="rounded-xl bg-red-50 px-3.5 py-2.5 text-[12px] text-red-700 dark:bg-red-500/10 dark:text-red-200">{error}</div>}
            
            <PrimaryButton onClick={handleRegister} className="w-full py-3.5 text-[15px] mt-2">Создать аккаунт</PrimaryButton>
          </div>

          <div className="mt-6 flex justify-center">
            <button onClick={() => navigate("/login")} className="text-[14px] text-[#0056FF] hover:underline">Уже есть аккаунт? Войти</button>
          </div>
          <div className="mt-6 text-center text-[12px] text-black/40 dark:text-white/40 leading-relaxed">
            Информация носит справочный характер. Перед подачей документов рекомендуется уточнять актуальные требования на официальных ресурсах.
          </div>
        </Card>
      </div>
    </div>
  );
}

export function AboutPage() {
  const { isMobile } = useContext(ShellContext);
  const navigate = useNavigate();

  return (
    <div className={`${isMobile ? "h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden" : "p-8 max-w-[800px]"} space-y-6`}>
      {isMobile ? (
         <MobileTopBar title="О приложении" onBack={() => navigate(-1)} />
      ) : (
        <button onClick={() => navigate(-1)} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55 hover:text-black dark:hover:text-white transition-colors">
          <ChevronLeft size={14} /> Назад
        </button>
      )}
      
      <div className={isMobile ? "px-5" : ""}>
        <div className="flex justify-center mb-6">
          <div className="flex flex-col items-center gap-4">
            <div className="grid h-20 w-20 place-items-center rounded-3xl bg-gradient-to-br from-[#0056FF] to-[#2277FF] text-white shadow-xl shadow-[#0056FF]/20">
              <Shield size={36} />
            </div>
            <div className="text-center">
              <h1 className="text-2xl font-medium text-black dark:text-white tracking-tight">Белпомощник</h1>
              <div className="text-[13px] text-black/50 dark:text-white/50 mt-1">Версия: 0.1 beta</div>
            </div>
          </div>
        </div>

        <Card className="p-6">
          <p className="text-[15px] text-black/70 dark:text-white/70 leading-relaxed text-center tracking-tight">
            Приложение помогает гражданам Республики Беларусь проходить жизненные ситуации пошагово, не забывая о документах и сроках.
          </p>
        </Card>

        <div className="mt-8 text-[14px] tracking-tight font-medium pl-1 text-black/60 dark:text-white/60 mb-3">Для кого приложение</div>
        <Card className="p-5">
          <ul className="list-none space-y-3 text-[14px] text-black/80 dark:text-white/80">
            <li className="flex items-center gap-3"><div className="w-1.5 h-1.5 rounded-full bg-[#0056FF]" /> Граждане</li>
            <li className="flex items-center gap-3"><div className="w-1.5 h-1.5 rounded-full bg-[#0056FF]" /> Семьи</li>
            <li className="flex items-center gap-3"><div className="w-1.5 h-1.5 rounded-full bg-[#0056FF]" /> Индивидуальные предприниматели (ИП)</li>
            <li className="flex items-center gap-3"><div className="w-1.5 h-1.5 rounded-full bg-[#0056FF]" /> Люди, которым нужно разобраться с документами и обращениями</li>
          </ul>
        </Card>

        <div className="mt-8 text-[14px] tracking-tight font-medium pl-1 text-black/60 dark:text-white/60 mb-3">Что умеет</div>
        <Card className="p-5">
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6 text-[14px] text-black/80 dark:text-white/80">
            <li className="flex items-center gap-3"><div className="bg-[#0056FF]/10 text-[#0056FF] p-1 rounded-full"><Check size={12} strokeWidth={3} /></div> Жизненные сценарии</li>
            <li className="flex items-center gap-3"><div className="bg-[#0056FF]/10 text-[#0056FF] p-1 rounded-full"><Check size={12} strokeWidth={3} /></div> Личные ситуации</li>
            <li className="flex items-center gap-3"><div className="bg-[#0056FF]/10 text-[#0056FF] p-1 rounded-full"><Check size={12} strokeWidth={3} /></div> Задачи и сроки</li>
            <li className="flex items-center gap-3"><div className="bg-[#0056FF]/10 text-[#0056FF] p-1 rounded-full"><Check size={12} strokeWidth={3} /></div> Управление документами</li>
            <li className="flex items-center gap-3"><div className="bg-[#0056FF]/10 text-[#0056FF] p-1 rounded-full"><Check size={12} strokeWidth={3} /></div> Уведомления о важном</li>
            <li className="flex items-center gap-3"><div className="bg-[#0056FF]/10 text-[#0056FF] p-1 rounded-full"><Check size={12} strokeWidth={3} /></div> Правовые обновления</li>
            <li className="flex items-center gap-3"><div className="bg-[#0056FF]/10 text-[#0056FF] p-1 rounded-full"><Check size={12} strokeWidth={3} /></div> Обучение</li>
            <li className="flex items-center gap-3"><div className="bg-[#0056FF]/10 text-[#0056FF] p-1 rounded-full"><Check size={12} strokeWidth={3} /></div> Админ-панель</li>
          </ul>
        </Card>

        <div className="mt-8 rounded-2xl border border-amber-200/60 bg-amber-50 p-5 text-[13px] tracking-tight text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200 text-center leading-relaxed">
          Информация носит справочный характер. Перед подачей документов рекомендуется уточнять актуальные требования на официальных ресурсах.
        </div>
      </div>
    </div>
  );
}

export function ProblemsPage() {
  const { isMobile } = useContext(ShellContext);
  const { problems, categories } = useStore();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [activeCat, setActiveCat] = useState("all");

  const filtered = problems.filter(s => {
    if (activeCat !== "all" && s.category !== activeCat) return false;
    if (q && !s.title.toLowerCase().includes(q.toLowerCase())) return false;
    return true;
  });

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Каталог проблем" onBack={() => navigate(-1)} />
        <div className="px-5">
          <div className="flex items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3 dark:border-white/[0.06] dark:bg-[#0F1117]">
            <Search size={16} className="text-black/40 dark:text-white/40" />
            <input placeholder="Найти проблему" value={q} onChange={e => setQ(e.target.value)} className="flex-1 bg-transparent tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
          </div>
          <div className="mt-3"><ProposeButton kind="problem" className="w-full justify-center" /></div>
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden">
            <button onClick={() => setActiveCat("all")} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${activeCat==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
            {categories.map(c => (
              <button key={c.id} onClick={() => setActiveCat(c.id)} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${activeCat===c.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{c.name}</button>
            ))}
          </div>
          {filtered.length === 0 && <div className="mt-10 text-center text-[13px] text-black/55 dark:text-white/55">Ничего не найдено. Попробуйте изменить запрос.</div>}
          <div className="mt-5 grid grid-cols-1 gap-3">
            {filtered.map((s, i) => (
              <button key={s.id} onClick={() => navigate(`/problem-detail/${s.id}`)} className="block text-left w-full">
                <Card interactive className="p-4 flex gap-4 items-center">
                  <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl"
                    style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>
                    <CatIcon cat={s.category} />
                  </div>
                  <div className="flex-1">
                    <div className="text-[11px] text-[#0056FF] mb-1">{catLabel(s.category)}</div>
                    <div className="tracking-tight text-black dark:text-white leading-tight">{s.title}</div>
                    <div className="mt-1 text-[12px] tracking-tight text-black/50 dark:text-white/50">{s.shortDescription}</div>
                  </div>
                </Card>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Справочник</div>
      <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Каталог проблем</div>
      <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">
        Классический справочник проблем, если вы не хотите выбирать длительный сценарий.
      </p>
      
      <div className="mt-6 flex gap-3 items-center max-w-[640px]">
        <div className="flex flex-1 items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3 dark:border-white/[0.06] dark:bg-[#0F1117]">
          <Search size={16} className="text-black/40 dark:text-white/40" />
          <input placeholder="Найти проблему" value={q} onChange={e => setQ(e.target.value)} className="flex-1 bg-transparent tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
        </div>
        <ProposeButton kind="problem" className="shrink-0 self-stretch" />
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <button onClick={() => setActiveCat("all")} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${activeCat==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
        {categories.map(c => (
          <button key={c.id} onClick={() => setActiveCat(c.id)} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${activeCat===c.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{c.name}</button>
        ))}
      </div>
      
      <div className="mt-8"><EditorialFeed kind="problem" title="Проблемы от редакции и пользователей" /></div>
      {filtered.length === 0 && <div className="mt-10 text-[14px] text-black/55 dark:text-white/55">Ничего не найдено. Попробуйте изменить запрос.</div>}

      <div className="mt-6 grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((s, i) => (
          <button key={s.id} className="text-left" onClick={() => navigate(`/problem-detail/${s.id}`)}>
            <Card interactive className="p-5 flex flex-col h-full">
              <div className="flex items-start justify-between">
                <div className="grid h-12 w-12 place-items-center rounded-2xl" style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>
                  <CatIcon cat={s.category} />
                </div>
              </div>
              <div className="mt-6 tracking-tight text-black dark:text-white" style={{ fontSize: 16, lineHeight: 1.2 }}>{s.title}</div>
              <div className="mt-1 text-[12px] tracking-tight text-[#0056FF]">{catLabel(s.category)}</div>
              <div className="mt-3 text-[13px] tracking-tight text-black/60 dark:text-white/60 line-clamp-3">{s.shortDescription}</div>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}

function AuthAside({ mode }: { mode: "login" | "register" }) {
  const title = mode === "login" ? "Вернитесь к своим ситуациям" : "Начните с личного профиля";
  const text = mode === "login"
    ? "После входа откроются ваши задачи, документы, уведомления и быстрые роли для показа разных сценариев работы."
    : "Профиль нужен, чтобы подбирать учреждения по городу, сохранять документы и строить персональные планы.";
  const points = mode === "login"
    ? [
        { icon: <Check size={16} />, title: "Прогресс сохраняется", text: "Отмеченные задачи и ситуации остаются в аккаунте." },
        { icon: <Bell size={16} />, title: "Сроки под контролем", text: "Напоминания показывают ближайшие действия." },
        { icon: <Shield size={16} />, title: "Личные данные отдельно", text: "Гость видит интерфейс, но не меняет личные записи." },
      ]
    : [
        { icon: <MapPin size={16} />, title: "Адрес и регион", text: "Система сможет подсказывать подходящие учреждения." },
        { icon: <FileText size={16} />, title: "Документы", text: "Добавляйте паспорт, медкнижку и другие важные документы." },
        { icon: <Search size={16} />, title: "Каталог помощи", text: "Выбирайте проблемы или жизненные сценарии." },
      ];

  return (
    <div className="hidden min-h-[640px] overflow-hidden rounded-[34px] border border-[#0056FF]/15 bg-[#071022] p-8 text-white shadow-[0_36px_110px_-70px_rgba(0,86,255,0.9)] lg:flex lg:flex-col lg:justify-between">
      <div>
        <Logo size={34} />
        <div className="mt-10 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-[12px] tracking-tight text-white/75">
          <Sparkles size={12} /> гражданский помощник
        </div>
        <h1 className="mt-5 max-w-[12ch] tracking-tight" style={{ fontSize: 46, lineHeight: 1.02 }}>{title}</h1>
        <p className="mt-4 max-w-[46ch] text-[15px] leading-relaxed text-white/68">{text}</p>
      </div>

      <div className="mt-10 space-y-3">
        {points.map(point => (
          <div key={point.title} className="flex gap-3 rounded-3xl border border-white/10 bg-white/[0.07] p-4 backdrop-blur">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-white text-[#0056FF]">{point.icon}</span>
            <span>
              <span className="block text-[14px] font-medium tracking-tight text-white">{point.title}</span>
              <span className="mt-0.5 block text-[12px] leading-relaxed tracking-tight text-white/60">{point.text}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Финансы: ЖКХ и налоги (ТЗ §18) ---
const BYN = (v: number) => `${v.toFixed(2)} BYN`;
function payTone(status: string): "ok" | "warn" | "azure" {
  if (status === "Оплачено") return "ok";
  if (status === "Просрочено") return "warn";
  return "azure";
}
const todayISO = () => new Date().toISOString().slice(0, 10);
const MONTHS_RU = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
const monthLabel = (d: Date) => `${MONTHS_RU[d.getMonth()]} ${d.getFullYear()}`;
const monthEnd = (d: Date) => {
  const last = new Date(d.getFullYear(), d.getMonth() + 1, 0);
  return last.toISOString().slice(0, 10);
};

function EditableField({
  value,
  onCommit,
  placeholder,
  inputClass,
  type = "text",
}: {
  value: string;
  onCommit: (next: string) => void;
  placeholder?: string;
  inputClass?: string;
  type?: "text" | "number" | "date";
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value);
  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => { setDraft(value); setEditing(true); }}
        className={`block w-full truncate text-left ${inputClass ?? ""}`}
        title={value || placeholder || ""}
      >
        {value || <span className="text-black/35 dark:text-white/35">{placeholder}</span>}
      </button>
    );
  }
  return (
    <input
      autoFocus
      type={type}
      value={draft}
      placeholder={placeholder}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => { setEditing(false); if (draft !== value) onCommit(draft); }}
      onKeyDown={(e) => {
        if (e.key === "Enter") { (e.target as HTMLInputElement).blur(); }
        if (e.key === "Escape") { setDraft(value); setEditing(false); }
      }}
      className={`w-full rounded-lg border border-[#0056FF]/40 bg-white px-2 py-1 text-[14px] tracking-tight text-black outline-none focus:ring-2 focus:ring-[#0056FF]/30 dark:bg-white/[0.06] dark:text-white ${inputClass ?? ""}`}
    />
  );
}

function FinanceBody() {
  const {
    role, utilityAccounts, taxes,
    addUtilityAccount, updateUtilityAccount, deleteUtilityAccount,
    addUtilityPayment, updateUtilityPayment, deleteUtilityPayment,
    addTax, updateTax, deleteTax,
  } = useStore();
  const canEdit = role !== "guest";

  // v1.1 (P9): summary-карточки — ближайший платёж, просрочки, сумма месяца.
  const today = todayISO();
  const allUpcoming: { title: string; date: string; amount?: number; overdue: boolean }[] = [];
  for (const acc of utilityAccounts) {
    for (const p of acc.payments) {
      if (p.status === "Оплачено") continue;
      const overdue = !!p.paymentDeadline && p.paymentDeadline < today;
      allUpcoming.push({
        title: `${acc.provider || "ЖКХ"} · ${acc.address || "без адреса"}`,
        date: p.paymentDeadline || "",
        amount: typeof p.amount === "number" ? p.amount : undefined,
        overdue,
      });
    }
  }
  for (const t of taxes) {
    if (t.status === "Оплачено") continue;
    const overdue = !!t.dueDate && t.dueDate < today;
    allUpcoming.push({ title: t.title, date: t.dueDate || "", amount: typeof t.amount === "number" ? t.amount : undefined, overdue });
  }
  allUpcoming.sort((a, b) => (a.date || "9999").localeCompare(b.date || "9999"));
  const overdueCount = allUpcoming.filter(x => x.overdue).length;
  const next = allUpcoming.find(x => !x.overdue);
  const monthSum = allUpcoming
    .filter(x => x.date && x.date.startsWith(today.slice(0, 7)))
    .reduce((acc, x) => acc + (x.amount || 0), 0);

  return (
    <div className="space-y-8">
      {/* v1.1 (P9): summary — ближайший / просрочки / сумма месяца. */}
      <section>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Card className="p-4">
            <div className="flex items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
              <CalendarClock size={13} /> Ближайший платёж
            </div>
            <div className="mt-1.5 truncate text-[15px] tracking-tight text-black dark:text-white">
              {next ? next.title : "Нет сроков"}
            </div>
            <div className="mt-0.5 text-[12px] tracking-tight text-black/50 dark:text-white/50">
              {next ? (next.date ? (next.overdue ? "просрочен" : `до ${next.date}`) : "без срока") : "Всё оплачено или нет счетов"}
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 text-[12px] tracking-tight text-red-600 dark:text-red-400">
              <AlertCircle size={13} /> Просрочки
            </div>
            <div className="mt-1.5 tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>
              {overdueCount}
            </div>
            <div className="mt-0.5 text-[12px] tracking-tight text-black/50 dark:text-white/50">
              {overdueCount > 0 ? "нужно закрыть как можно скорее" : "просрочек нет"}
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-2 text-[12px] tracking-tight text-emerald-600 dark:text-emerald-400">
              <Wallet size={13} /> Сумма в этом месяце
            </div>
            <div className="mt-1.5 tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>
              {monthSum > 0 ? `${monthSum.toLocaleString("ru-RU")} BYN` : "—"}
            </div>
            <div className="mt-0.5 text-[12px] tracking-tight text-black/50 dark:text-white/50">
              {monthSum > 0 ? "по срокам этого месяца" : "нет счетов в этом месяце"}
            </div>
          </Card>
        </div>
      </section>
      {/* ЖКХ */}
      <section>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>
            <Home size={18} className="text-[#0056FF]" /> ЖКХ
          </div>
          {canEdit && (
            <GhostButton
              className="gap-1.5 px-3 text-[13px]"
              onClick={() =>
                addUtilityAccount({
                  address: "Новый адрес",
                  accountNumber: "",
                  provider: "",
                })
              }
            >
              <Plus size={14} /> Счёт
            </GhostButton>
          )}
        </div>

        <div className="mt-4 space-y-4">
          {utilityAccounts.map((acc) => {
            const upcoming = acc.payments
              .filter((p) => p.status !== "Оплачено")
              .sort((a, b) => (a.paymentDeadline || "").localeCompare(b.paymentDeadline || ""));
            const overdue = upcoming.find((p) => p.paymentDeadline && p.paymentDeadline < todayISO());
            return (
              <Card key={acc.id} className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1 space-y-1">
                    {canEdit ? (
                      <EditableField
                        value={acc.address}
                        placeholder="Адрес (например, ул. Ленина, 12)"
                        onCommit={(v) => updateUtilityAccount(acc.id, { address: v })}
                        inputClass="tracking-tight text-black dark:text-white"
                        // @ts-expect-error style via className
                      />
                    ) : (
                      <div className="tracking-tight text-black dark:text-white truncate" style={{ fontSize: 16 }}>
                        {acc.address}
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                      {canEdit ? (
                        <>
                          <EditableField
                            value={acc.provider}
                            placeholder="Поставщик"
                            onCommit={(v) => updateUtilityAccount(acc.id, { provider: v })}
                            inputClass="bg-transparent text-[12px]"
                          />
                          <span>·</span>
                          <EditableField
                            value={acc.accountNumber}
                            placeholder="Лицевой счёт"
                            onCommit={(v) => updateUtilityAccount(acc.id, { accountNumber: v })}
                            inputClass="bg-transparent text-[12px]"
                          />
                        </>
                      ) : (
                        <span>
                          {acc.provider}
                          {acc.accountNumber ? ` · ${acc.accountNumber}` : ""}
                        </span>
                      )}
                    </div>
                    {overdue && (
                      <div className="mt-1 inline-flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400">
                        <AlertCircle size={11} /> Просрочен платёж за {overdue.period}
                      </div>
                    )}
                  </div>
                  {canEdit && (
                    <button
                      onClick={() => deleteUtilityAccount(acc.id)}
                      className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-black/35 hover:bg-black/[0.04] hover:text-red-500 dark:text-white/35 dark:hover:bg-white/[0.06]"
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
                </div>

                <div className="mt-4 space-y-2.5">
                  {acc.payments.map((p) => (
                    <div
                      key={p.id}
                      className="flex flex-wrap items-center gap-3 rounded-2xl bg-[#F6F7FB] px-4 py-3 dark:bg-white/[0.04]"
                    >
                      <div className="flex-1 min-w-[120px]">
                        {canEdit ? (
                          <div className="flex items-center gap-2">
                            <EditableField
                              value={p.period}
                              placeholder="Период (напр. Июль 2026)"
                              onCommit={(v) => updateUtilityPayment(acc.id, p.id, { period: v })}
                            />
                            <Pill tone={payTone(p.status)}>{p.status}</Pill>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <span className="tracking-tight text-black dark:text-white">{p.period}</span>
                            <Pill tone={payTone(p.status)}>{p.status}</Pill>
                          </div>
                        )}
                        <div className="mt-0.5 flex items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                          {canEdit ? (
                            <>
                              <EditableField
                                value={p.amount ? String(p.amount) : ""}
                                placeholder="Сумма"
                                type="number"
                                onCommit={(v) =>
                                  updateUtilityPayment(acc.id, p.id, { amount: Number(v) || 0 })
                                }
                              />
                              <span>· оплатить до</span>
                              <EditableField
                                value={p.paymentDeadline || ""}
                                placeholder="—"
                                type="date"
                                onCommit={(v) => updateUtilityPayment(acc.id, p.id, { paymentDeadline: v })}
                              />
                            </>
                          ) : (
                            <span>
                              {BYN(p.amount)}
                              {p.paymentDeadline ? ` · оплатить до ${p.paymentDeadline}` : ""}
                            </span>
                          )}
                        </div>
                      </div>
                      {canEdit && p.status !== "Оплачено" && (
                        <button
                          onClick={() =>
                            updateUtilityPayment(acc.id, p.id, {
                              status: "Оплачено",
                              paymentDate: todayISO(),
                            })
                          }
                          className="flex items-center gap-1 rounded-xl bg-[#0056FF] px-3 py-1.5 text-[12px] tracking-tight text-white"
                        >
                          <Check size={13} /> Оплачено
                        </button>
                      )}
                      {canEdit && (
                        <button
                          onClick={() => deleteUtilityPayment(acc.id, p.id)}
                          className="grid h-8 w-8 place-items-center rounded-lg text-black/30 hover:text-red-500 dark:text-white/30"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  ))}
                  {canEdit && (
                    <button
                      onClick={() =>
                        addUtilityPayment(acc.id, {
                          period: monthLabel(new Date()),
                          amount: 0,
                          status: "Предстоит",
                          paymentDeadline: monthEnd(new Date()),
                        })
                      }
                      className="flex w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-black/15 bg-transparent py-3 text-[13px] tracking-tight text-black/55 hover:bg-black/[0.02] dark:border-white/15 dark:text-white/55 dark:hover:bg-white/[0.03]"
                    >
                      <Plus size={14} /> Добавить платёж
                    </button>
                  )}
                  {acc.payments.length === 0 && !canEdit && (
                    <div className="text-[12px] text-black/45 dark:text-white/45">Платежей пока нет</div>
                  )}
                </div>
              </Card>
            );
          })}
          {utilityAccounts.length === 0 && (
            <Card className="p-6 text-center text-[13px] tracking-tight text-black/55 dark:text-white/55">
              {canEdit
                ? "Лицевые счета не добавлены. Нажмите «Счёт», чтобы добавить первый."
                : "Войдите, чтобы добавлять лицевые счета и следить за сроками оплаты."}
            </Card>
          )}
        </div>
      </section>

      {/* Налоги */}
      <section>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>
            <Wallet size={18} className="text-[#0056FF]" /> Налоги
          </div>
          {canEdit && (
            <GhostButton
              className="gap-1.5 px-3 text-[13px]"
              onClick={() =>
                addTax({
                  title: "Новый налог",
                  userType: "individual",
                  amount: 0,
                  status: "Предстоит",
                  deadline: "",
                  period: String(new Date().getFullYear()),
                })
              }
            >
              <Plus size={14} /> Налог
            </GhostButton>
          )}
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {taxes.map((t) => {
            const overdue = t.status !== "Оплачено" && t.deadline && t.deadline < todayISO();
            return (
              <Card key={t.id} className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1 space-y-1">
                    {canEdit ? (
                      <EditableField
                        value={t.title}
                        placeholder="Название (напр. Земельный налог)"
                        onCommit={(v) => updateTax(t.id, { title: v })}
                        inputClass="tracking-tight text-black dark:text-white"
                      />
                    ) : (
                      <div className="tracking-tight text-black dark:text-white truncate" style={{ fontSize: 16 }}>
                        {t.title}
                      </div>
                    )}
                    <div className="flex flex-wrap items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                      {canEdit ? (
                        <>
                          <EditableField
                            value={t.amount ? String(t.amount) : ""}
                            placeholder="Сумма"
                            type="number"
                            onCommit={(v) => updateTax(t.id, { amount: Number(v) || 0 })}
                          />
                          <span>·</span>
                          <EditableField
                            value={t.period || ""}
                            placeholder="Период (2026)"
                            onCommit={(v) => updateTax(t.id, { period: v })}
                          />
                          <span>· до</span>
                          <EditableField
                            value={t.deadline || ""}
                            placeholder="—"
                            type="date"
                            onCommit={(v) => updateTax(t.id, { deadline: v })}
                          />
                        </>
                      ) : (
                        <span>
                          {BYN(t.amount)}
                          {t.deadline ? ` · до ${t.deadline}` : ""}
                        </span>
                      )}
                    </div>
                    {overdue && (
                      <div className="mt-1 inline-flex items-center gap-1 text-[11px] text-amber-600 dark:text-amber-400">
                        <AlertCircle size={11} /> Просрочен
                      </div>
                    )}
                  </div>
                  <Pill
                    tone={
                      t.status === "Оплачено" ? "ok" : overdue ? "warn" : "lavender"
                    }
                  >
                    {t.status}
                  </Pill>
                </div>
                {canEdit && (
                  <div className="mt-4 flex items-center gap-2">
                    {t.status !== "Оплачено" && (
                      <button
                        onClick={() => updateTax(t.id, { status: "Оплачено" })}
                        className="flex items-center gap-1 rounded-xl bg-[#0056FF] px-3 py-1.5 text-[12px] tracking-tight text-white"
                      >
                        <Check size={13} /> Отметить оплаченным
                      </button>
                    )}
                    <button
                      onClick={() => deleteTax(t.id)}
                      className="grid h-8 w-8 place-items-center rounded-lg text-black/35 hover:text-red-500 dark:text-white/35"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                )}
              </Card>
            );
          })}
          {taxes.length === 0 && (
            <Card className="p-6 text-center text-[13px] tracking-tight text-black/55 dark:text-white/55 md:col-span-2">
              {canEdit
                ? "Налоговые обязательства не добавлены. Нажмите «Налог», чтобы добавить первое."
                : "Войдите, чтобы добавлять налоговые обязательства."}
            </Card>
          )}
        </div>
      </section>
    </div>
  );
}

export function FinancePage() {
  const { isMobile } = useContext(ShellContext);
  const navigate = useNavigate();

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="ЖКХ и налоги" onBack={() => navigate(-1)} />
        <div className="px-5 pt-2"><FinanceBody /></div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div>
        <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Платежи</div>
        <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>ЖКХ и налоги</div>
        <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">Следите за сроками оплаты, передачи показаний и налоговыми обязательствами</p>
      </div>
      <div className="mt-6 max-w-[920px]"><FinanceBody /></div>
    </div>
  );
}

/* ============================================================
   P7: ExtremistPage — каркас раздела «Экстремистский контент».
   Только скелет: пустое состояние, фильтры, форма добавления.
   Никаких реальных данных, имён или ссылок. Контент добавится
   отдельным этапом после проверки официальных источников.
   ============================================================ */

const EXTREMIST_ALL_CONTENT_TYPES: ExtremistContentType[] = [
  "social", "channels", "media", "persons", "organizations", "music", "other",
];

type ExtremistForm = {
  title: string;
  category: ExtremistCategory;
  sourceUrl: string;
  sourceName: string;
  includedAt: string;
  lastCheckedAt: string;
  shortDescription: string;
  coverUrl: string;
  mediaUrls: string[];
  attachmentUrls: string[];
  mediaUrlInput: string;
  attachmentUrlInput: string;
  contentTypes: ExtremistContentType[];
  status: ExtremistStatus;
};

const emptyExtremistForm = (): ExtremistForm => ({
  title: "",
  category: "registry",
  sourceUrl: "",
  sourceName: "",
  includedAt: "",
  lastCheckedAt: "",
  shortDescription: "",
  coverUrl: "",
  mediaUrls: [],
  attachmentUrls: [],
  mediaUrlInput: "",
  attachmentUrlInput: "",
  contentTypes: [],
  status: "draft",
});

function isValidHttpUrl(value: string): boolean {
  if (!value) return false;
  try {
    const u = new URL(value);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

type RawExtremistEntry = {
  id?: string | number;
  title?: string;
  category?: string;
  source_url?: string;
  source_name?: string;
  included_at?: string | null;
  last_checked_at?: string | null;
  short_description?: string;
  cover_url?: string;
  media_urls?: string[];
  attachment_urls?: string[];
  filters_json?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
};

function parseExtremistContentTypes(raw: string | undefined): ExtremistContentType[] {
  try {
    const parsed = JSON.parse(raw || "{}");
    const values = Array.isArray(parsed?.content_types) ? parsed.content_types : [];
    return values.filter((x: string): x is ExtremistContentType => EXTREMIST_ALL_CONTENT_TYPES.includes(x as ExtremistContentType));
  } catch {
    return [];
  }
}

function adaptExtremistEntry(raw: RawExtremistEntry): ExtremistEntry {
  return {
    id: String(raw.id ?? `entry-${Date.now()}`),
    title: raw.title ?? "",
    category: EXTREMIST_CATEGORY_LABEL[raw.category as ExtremistCategory] ? raw.category as ExtremistCategory : "registry",
    sourceUrl: raw.source_url ?? "",
    sourceName: raw.source_name ?? "",
    includedAt: raw.included_at ?? undefined,
    lastCheckedAt: raw.last_checked_at ?? undefined,
    shortDescription: raw.short_description ?? "",
    coverUrl: raw.cover_url ?? "",
    mediaUrls: Array.isArray(raw.media_urls) ? raw.media_urls : [],
    attachmentUrls: Array.isArray(raw.attachment_urls) ? raw.attachment_urls : [],
    contentTypes: parseExtremistContentTypes(raw.filters_json),
    status: raw.status === "draft" ? "draft" : "published",
    createdAt: raw.created_at ?? new Date().toISOString(),
    updatedAt: raw.updated_at ?? new Date().toISOString(),
  };
}

function formatExtremistDate(value?: string): string {
  if (!value) return "не указана";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 10);
  return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "long", year: "numeric" });
}

function sourceHost(value: string): string {
  try {
    return new URL(value).host.replace(/^www\./, "");
  } catch {
    return value || "официальный источник";
  }
}

function isImageUrl(value: string): boolean {
  return /\.(png|jpe?g|webp|gif|avif)(\?.*)?$/i.test(value);
}

function ExtremistEntryCard({
  entry,
  onOpen,
}: {
  entry: ExtremistEntry;
  onOpen: () => void;
}) {
  const mediaCount = (entry.mediaUrls?.length ?? 0) + (entry.attachmentUrls?.length ?? 0);
  const checkedLabel = entry.lastCheckedAt ? formatExtremistDate(entry.lastCheckedAt) : "требуется проверка";
  return (
    <Card className="group overflow-hidden p-0 transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-[0_20px_60px_-46px_rgba(15,23,42,0.55)]">
      {entry.coverUrl ? (
        <button type="button" onClick={onOpen} className="block h-44 w-full overflow-hidden text-left">
          <img src={entry.coverUrl} alt="" className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.02]" />
        </button>
      ) : (
        <button
          type="button"
          onClick={onOpen}
          className="flex h-32 w-full items-center justify-between overflow-hidden bg-gradient-to-br from-red-50 via-white to-blue-50 px-5 text-left dark:from-red-500/15 dark:via-white/[0.04] dark:to-blue-500/10"
        >
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-200">
            <AlertTriangle size={24} />
          </div>
          <div className="text-right text-[12px] uppercase tracking-[0.16em] text-black/35 dark:text-white/35">
            официальный<br />источник
          </div>
        </button>
      )}
      <div className="p-4">
        <div className="flex flex-wrap items-center gap-1.5">
          <Pill tone={entry.status === "published" ? "ok" : "ghost"}>{EXTREMIST_STATUS_LABEL[entry.status]}</Pill>
          <Pill tone="warn">{EXTREMIST_CATEGORY_LABEL[entry.category]}</Pill>
          {mediaCount > 0 && <Pill tone="lavender">{mediaCount} медиа</Pill>}
        </div>
        <button type="button" onClick={onOpen} className="mt-3 block w-full text-left">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18, lineHeight: 1.18 }}>
            {entry.title}
          </div>
          {entry.shortDescription && (
            <div className="mt-2 line-clamp-3 text-[13px] leading-relaxed tracking-tight text-black/55 dark:text-white/55">
              {entry.shortDescription}
            </div>
          )}
        </button>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {entry.contentTypes.length > 0 ? entry.contentTypes.map((t) => (
            <span key={t} className="rounded-full bg-black/[0.04] px-2.5 py-1 text-[11px] tracking-tight text-black/55 dark:bg-white/[0.06] dark:text-white/55">
              {EXTREMIST_CONTENT_TYPE_LABEL[t]}
            </span>
          )) : (
            <span className="rounded-full bg-black/[0.04] px-2.5 py-1 text-[11px] tracking-tight text-black/45 dark:bg-white/[0.06] dark:text-white/45">
              тип не указан
            </span>
          )}
        </div>
        <div className="mt-4 rounded-2xl bg-black/[0.025] p-3 dark:bg-white/[0.045]">
          <div className="flex items-start gap-2">
            <Shield size={14} className="mt-0.5 shrink-0 text-[#0056FF]" />
            <div className="min-w-0">
              <div className="truncate text-[12px] tracking-tight text-black/60 dark:text-white/60">
                {entry.sourceName || sourceHost(entry.sourceUrl)}
              </div>
              <div className="mt-0.5 text-[11px] tracking-tight text-black/38 dark:text-white/38">
                Проверено: {checkedLabel}
              </div>
            </div>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-black/[0.06] pt-3 dark:border-white/[0.08]">
          <button
            type="button"
            onClick={onOpen}
            className="inline-flex items-center gap-1.5 text-[13px] font-medium tracking-tight text-[#0056FF]"
          >
            Подробнее <ArrowRight size={14} />
          </button>
          <a
            href={entry.sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 text-[12px] tracking-tight text-black/45 hover:text-[#0056FF] dark:text-white/45"
          >
            Источник <ArrowUpRight size={13} />
          </a>
        </div>
      </div>
    </Card>
  );
}

export function ExtremistPage() {
  const { isMobile } = useContext(ShellContext);
  const { role, uploadMedia, authSession } = useStore();
  const navigate = useNavigate();
  const canEdit = role === "editor" || role === "admin" || role === "content_editor" || role === "platform_admin";
  const coverInputRef = useRef<HTMLInputElement>(null);
  const mediaInputRef = useRef<HTMLInputElement>(null);
  const attachmentInputRef = useRef<HTMLInputElement>(null);

  const [entries, setEntries] = useState<ExtremistEntry[]>([]);
  const [statusFilter, setStatusFilter] = useState<"all" | ExtremistStatus>("all");
  const [typeFilter, setTypeFilter] = useState<"all" | ExtremistContentType>("all");
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<ExtremistForm>(emptyExtremistForm);
  const [formError, setFormError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [saving, setSaving] = useState(false);

  const reloadEntries = useCallback(async () => {
    setLoadError("");
    try {
      const token = authSession?.access_token ?? apiClient.loadTokens()?.access_token;
      const raw = canEdit && token
        ? await apiClient.getAdminExtremistEntries<RawExtremistEntry[]>(token)
        : await apiClient.getExtremistEntries<RawExtremistEntry[]>();
      setEntries(raw.map(adaptExtremistEntry));
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Не удалось загрузить записи.");
      setEntries([]);
    }
  }, [authSession?.access_token, canEdit]);

  useEffect(() => {
    reloadEntries();
  }, [reloadEntries]);

  const filtered = entries.filter((e) => {
    if (statusFilter !== "all" && e.status !== statusFilter) return false;
    if (typeFilter !== "all" && !e.contentTypes.includes(typeFilter)) return false;
    return true;
  });

  const closeForm = () => {
    setFormOpen(false);
    setForm(emptyExtremistForm());
    setFormError("");
    setSaving(false);
  };

  const appendUrl = (field: "mediaUrls" | "attachmentUrls", inputField: "mediaUrlInput" | "attachmentUrlInput") => {
    const value = form[inputField].trim();
    if (!isValidHttpUrl(value)) {
      setFormError("Вставьте корректную ссылку в формате http(s)://…");
      return;
    }
    setForm({ ...form, [field]: [...form[field], value], [inputField]: "" });
    setFormError("");
  };

  const removeUrl = (field: "mediaUrls" | "attachmentUrls", value: string) => {
    setForm({ ...form, [field]: form[field].filter((x) => x !== value) });
  };

  const uploadSelectedFiles = async (files: FileList | null, target: "cover" | "media" | "attachment") => {
    if (!files || files.length === 0) return;
    setFormError("");
    const uploaded: string[] = [];
    for (const file of Array.from(files)) {
      const remote = await uploadMedia(file);
      uploaded.push(remote ?? URL.createObjectURL(file));
    }
    if (target === "cover") {
      setForm((prev) => ({ ...prev, coverUrl: uploaded[0] ?? prev.coverUrl }));
    } else if (target === "media") {
      setForm((prev) => ({ ...prev, mediaUrls: [...prev.mediaUrls, ...uploaded] }));
    } else {
      setForm((prev) => ({ ...prev, attachmentUrls: [...prev.attachmentUrls, ...uploaded] }));
    }
  };

  const submitForm = async () => {
    setFormError("");
    if (form.title.trim().length < 2) {
      setFormError("Введите название (минимум 2 символа).");
      return;
    }
    if (!isValidHttpUrl(form.sourceUrl)) {
      setFormError("Укажите корректный URL официального источника (http(s)://…). Это обязательное поле.");
      return;
    }
    const token = apiClient.loadTokens()?.access_token;
    if (!token) {
      setFormError("Для сохранения нужна роль редактора или администратора с активной backend-сессией.");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        title: form.title.trim(),
        category: form.category,
        source_url: form.sourceUrl.trim(),
        source_name: form.sourceName.trim(),
        included_at: form.includedAt ? new Date(form.includedAt).toISOString() : null,
        last_checked_at: form.lastCheckedAt ? new Date(form.lastCheckedAt).toISOString() : null,
        short_description: form.shortDescription.trim(),
        cover_url: form.coverUrl.trim(),
        media_urls: form.mediaUrls.filter(isValidHttpUrl),
        attachment_urls: form.attachmentUrls.filter(isValidHttpUrl),
        filters_json: JSON.stringify({ content_types: form.contentTypes }),
        status: form.status,
      };
      const created = await apiClient.createExtremistEntry<RawExtremistEntry>(token, payload);
      setEntries((prev) => [adaptExtremistEntry(created), ...prev]);
      closeForm();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Не удалось сохранить запись.");
      setSaving(false);
    }
  };

  const headerBlock = (
    <div className="rounded-2xl border border-red-200/70 bg-red-50 p-4 dark:border-red-500/25 dark:bg-red-500/10">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-300">
          <AlertTriangle size={17} />
        </span>
        <div>
          <div className="tracking-tight text-red-900 dark:text-red-200" style={{ fontSize: 15 }}>
            Информация справочная. Актуальность проверяется на официальном ресурсе.
          </div>
          <p className="mt-1 text-[13px] leading-relaxed text-red-800/85 dark:text-red-200/75">
            Раздел «Экстремистский контент» содержит только записи с проверенным официальным
            источником и датой проверки. Без подтверждения данные в раздел не добавляются.
          </p>
        </div>
      </div>
    </div>
  );

  const filtersBlock = (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setStatusFilter("all")}
          className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${statusFilter === "all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}
        >Все статусы</button>
        {(Object.keys(EXTREMIST_STATUS_LABEL) as ExtremistStatus[]).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${statusFilter === s ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}
          >{EXTREMIST_STATUS_LABEL[s]}</button>
        ))}
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden">
        <button
          onClick={() => setTypeFilter("all")}
          className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${typeFilter === "all" ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}
        >Все типы</button>
        {EXTREMIST_ALL_CONTENT_TYPES.map((t) => (
          <button
            key={t}
            onClick={() => setTypeFilter(t)}
            className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${typeFilter === t ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}
          >{EXTREMIST_CONTENT_TYPE_LABEL[t]}</button>
        ))}
      </div>
    </div>
  );

  const emptyBlock = (
    <div className="grid place-items-center rounded-3xl border border-dashed border-black/10 p-12 text-center dark:border-white/12">
      <div>
        <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-red-50 text-red-500 dark:bg-red-500/15 dark:text-red-300">
          <AlertTriangle size={20} />
        </div>
        <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>
          Список пуст
        </div>
        <div className="mt-1 max-w-[42ch] text-[13px] tracking-tight text-black/55 dark:text-white/55">
          Контент добавляется после проверки официальных источников.
        </div>
        {canEdit && (
          <button
            onClick={() => setFormOpen(true)}
            className="mt-5 inline-flex h-10 items-center gap-1.5 rounded-xl bg-[#0056FF] px-4 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)]"
          >
            <Plus size={14} /> Добавить запись
          </button>
        )}
      </div>
    </div>
  );

  const entriesGrid = filtered.length > 0 && (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      {filtered.map((entry) => (
        <ExtremistEntryCard
          key={entry.id}
          entry={entry}
          onOpen={() => navigate(`/extremist/${entry.id}`)}
        />
      ))}
    </div>
  );

  const formModal = formOpen && (
    <div className="fixed inset-0 z-[120] flex items-end justify-center bg-black/40 p-0 backdrop-blur-sm sm:items-center sm:p-4" onClick={closeForm}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[92dvh] w-full max-w-[560px] overflow-y-auto rounded-t-[28px] bg-white p-5 shadow-2xl dark:bg-[#0F1117] sm:rounded-[28px] sm:p-6 [&::-webkit-scrollbar]:hidden"
      >
        <input ref={coverInputRef} type="file" accept="image/*" hidden onChange={(e) => { void uploadSelectedFiles(e.target.files, "cover"); e.currentTarget.value = ""; }} />
        <input ref={mediaInputRef} type="file" accept="image/*,video/*" multiple hidden onChange={(e) => { void uploadSelectedFiles(e.target.files, "media"); e.currentTarget.value = ""; }} />
        <input ref={attachmentInputRef} type="file" accept=".pdf,image/*,video/*" multiple hidden onChange={(e) => { void uploadSelectedFiles(e.target.files, "attachment"); e.currentTarget.value = ""; }} />
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[12px] uppercase tracking-[0.14em] text-[#0056FF]">P7 · каркас</div>
            <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 19 }}>Новая запись</div>
          </div>
          <button onClick={closeForm} className="grid h-9 w-9 place-items-center rounded-full bg-black/[0.04] dark:bg-white/[0.06]">
            <X size={15} className="text-black dark:text-white" />
          </button>
        </div>

        <div className="mt-5 space-y-4">
          <label className="block">
            <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Название *</span>
            <input
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Например: запись реестра"
              className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Тип материала</span>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value as ExtremistCategory })}
                className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
              >
                {(Object.keys(EXTREMIST_CATEGORY_LABEL) as ExtremistCategory[]).map((c) => (
                  <option key={c} value={c}>{EXTREMIST_CATEGORY_LABEL[c]}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Статус</span>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value as ExtremistStatus })}
                className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
              >
                {(Object.keys(EXTREMIST_STATUS_LABEL) as ExtremistStatus[]).map((s) => (
                  <option key={s} value={s}>{EXTREMIST_STATUS_LABEL[s]}</option>
                ))}
              </select>
            </label>
          </div>

          <label className="block">
            <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">
              URL официального источника *
            </span>
            <input
              value={form.sourceUrl}
              onChange={(e) => setForm({ ...form, sourceUrl: e.target.value })}
              placeholder="https://…"
              inputMode="url"
              className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
            />
          </label>

          <label className="block">
            <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Название источника</span>
            <input
              value={form.sourceName}
              onChange={(e) => setForm({ ...form, sourceName: e.target.value })}
              placeholder="Например: pravo.by"
              className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
            />
          </label>

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Дата включения</span>
              <input
                type="date"
                value={form.includedAt}
                onChange={(e) => setForm({ ...form, includedAt: e.target.value })}
                className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
              />
            </label>
            <label className="block">
              <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Дата проверки</span>
              <input
                type="date"
                value={form.lastCheckedAt}
                onChange={(e) => setForm({ ...form, lastCheckedAt: e.target.value })}
                className="mt-1.5 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
              />
            </label>
          </div>

          <label className="block">
            <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Краткое пояснение</span>
            <textarea
              value={form.shortDescription}
              onChange={(e) => setForm({ ...form, shortDescription: e.target.value })}
              placeholder="Короткое описание для контекста."
              rows={3}
              className="mt-1.5 w-full resize-none rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
            />
          </label>

          <div className="rounded-2xl border border-black/[0.06] p-3 dark:border-white/[0.08]">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[13px] tracking-tight text-black dark:text-white">Обложка</div>
                <div className="text-[11px] tracking-tight text-black/40 dark:text-white/40">Файл или ссылка на официальное изображение</div>
              </div>
              <button
                type="button"
                onClick={() => coverInputRef.current?.click()}
                className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-black/10 px-3 text-[12px] tracking-tight text-black/65 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/65"
              >
                <Camera size={14} /> Файл
              </button>
            </div>
            {form.coverUrl && (
              <div className="mt-3 overflow-hidden rounded-xl">
                <img src={form.coverUrl} alt="" className="h-32 w-full object-cover" />
              </div>
            )}
            <input
              value={form.coverUrl}
              onChange={(e) => setForm({ ...form, coverUrl: e.target.value })}
              placeholder="Или вставьте URL: https://…"
              inputMode="url"
              className="mt-3 w-full rounded-xl border border-black/10 bg-white px-3 py-2.5 text-[14px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-black/[0.06] p-3 dark:border-white/[0.08]">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-[13px] tracking-tight text-black dark:text-white">Фото и видео</div>
                  <div className="text-[11px] tracking-tight text-black/40 dark:text-white/40">Несколько ссылок или файлов</div>
                </div>
                <button
                  type="button"
                  onClick={() => mediaInputRef.current?.click()}
                  className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-black/10 px-3 text-[12px] tracking-tight text-black/65 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/65"
                >
                  <Camera size={14} /> Файл
                </button>
              </div>
              <div className="mt-3 flex gap-2">
                <input
                  value={form.mediaUrlInput}
                  onChange={(e) => setForm({ ...form, mediaUrlInput: e.target.value })}
                  placeholder="https://…"
                  inputMode="url"
                  className="min-w-0 flex-1 rounded-xl border border-black/10 bg-white px-3 py-2 text-[13px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
                />
                <button type="button" onClick={() => appendUrl("mediaUrls", "mediaUrlInput")} className="rounded-xl bg-[#0056FF] px-3 text-[12px] tracking-tight text-white">
                  Добавить
                </button>
              </div>
              <div className="mt-2 space-y-1.5">
                {form.mediaUrls.map((url) => (
                  <div key={url} className="flex items-center gap-2 rounded-xl bg-black/[0.03] px-2.5 py-2 dark:bg-white/[0.05]">
                    <Camera size={13} className="shrink-0 text-[#0056FF]" />
                    <span className="min-w-0 flex-1 truncate text-[12px] tracking-tight text-black/55 dark:text-white/55">{url}</span>
                    <button type="button" onClick={() => removeUrl("mediaUrls", url)} className="text-black/35 hover:text-red-500 dark:text-white/35"><X size={13} /></button>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-black/[0.06] p-3 dark:border-white/[0.08]">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-[13px] tracking-tight text-black dark:text-white">Файлы и вложения</div>
                  <div className="text-[11px] tracking-tight text-black/40 dark:text-white/40">PDF, изображения, видео</div>
                </div>
                <button
                  type="button"
                  onClick={() => attachmentInputRef.current?.click()}
                  className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-black/10 px-3 text-[12px] tracking-tight text-black/65 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/65"
                >
                  <FileText size={14} /> Файл
                </button>
              </div>
              <div className="mt-3 flex gap-2">
                <input
                  value={form.attachmentUrlInput}
                  onChange={(e) => setForm({ ...form, attachmentUrlInput: e.target.value })}
                  placeholder="https://…"
                  inputMode="url"
                  className="min-w-0 flex-1 rounded-xl border border-black/10 bg-white px-3 py-2 text-[13px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
                />
                <button type="button" onClick={() => appendUrl("attachmentUrls", "attachmentUrlInput")} className="rounded-xl bg-[#0056FF] px-3 text-[12px] tracking-tight text-white">
                  Добавить
                </button>
              </div>
              <div className="mt-2 space-y-1.5">
                {form.attachmentUrls.map((url) => (
                  <div key={url} className="flex items-center gap-2 rounded-xl bg-black/[0.03] px-2.5 py-2 dark:bg-white/[0.05]">
                    <FileText size={13} className="shrink-0 text-[#0056FF]" />
                    <span className="min-w-0 flex-1 truncate text-[12px] tracking-tight text-black/55 dark:text-white/55">{url}</span>
                    <button type="button" onClick={() => removeUrl("attachmentUrls", url)} className="text-black/35 hover:text-red-500 dark:text-white/35"><X size={13} /></button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div>
            <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Тип контента (мульти-выбор)</span>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {EXTREMIST_ALL_CONTENT_TYPES.map((t) => {
                const on = form.contentTypes.includes(t);
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => {
                      const next = on
                        ? form.contentTypes.filter((x) => x !== t)
                        : [...form.contentTypes, t];
                      setForm({ ...form, contentTypes: next });
                    }}
                    className={`rounded-full px-3 py-1.5 text-[12px] tracking-tight ${on ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}
                  >
                    {EXTREMIST_CONTENT_TYPE_LABEL[t]}
                  </button>
                );
              })}
            </div>
          </div>

          {formError && (
            <div className="rounded-xl bg-red-50 px-3.5 py-2.5 text-[12px] text-red-700 dark:bg-red-500/10 dark:text-red-200">
              {formError}
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              onClick={closeForm}
              className="rounded-xl px-4 py-2.5 text-[14px] tracking-tight text-black/70 dark:text-white/70"
            >
              Отмена
            </button>
            <button
              onClick={submitForm}
              disabled={saving}
              className="rounded-xl bg-[#0056FF] px-5 py-2.5 text-[14px] font-medium tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] disabled:opacity-55"
            >
              {saving ? "Сохраняем…" : "Сохранить"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Экстремистский контент" onBack={() => navigate(-1)} right={
          canEdit ? <button onClick={() => setFormOpen(true)} className="grid h-10 w-10 place-items-center rounded-full bg-[#0056FF] text-white shadow-sm"><Plus size={16} /></button> : undefined
        } />
        <div className="space-y-4 px-5">
          {headerBlock}
          <div>
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>
              Экстремистский контент — реестр (справочно)
            </div>
            <p className="mt-1 text-[13px] leading-relaxed text-black/55 dark:text-white/55">
              Все записи проходят проверку по официальным источникам. Без неё раздел остаётся пустым.
            </p>
          </div>
          {filtersBlock}
          {loadError && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-[13px] tracking-tight text-amber-800 dark:border-amber-500/25 dark:bg-amber-500/10 dark:text-amber-200">
              {loadError}
            </div>
          )}
          {entriesGrid}
          {filtered.length === 0 ? emptyBlock : null}
        </div>
        {formModal}
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Справочно · юридически чувствительный раздел</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>
            Экстремистский контент — реестр
          </div>
          <p className="mt-2 max-w-[620px] tracking-tight text-black/60 dark:text-white/60">
            Все записи проходят проверку по официальным источникам. Без неё раздел остаётся пустым.
          </p>
        </div>
        {canEdit && (
          <button
            onClick={() => setFormOpen(true)}
            className="inline-flex h-10 items-center gap-1.5 rounded-xl bg-[#0056FF] px-4 text-[13px] tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)]"
          >
            <Plus size={14} /> Добавить запись
          </button>
        )}
      </div>

      <div className="mt-6 max-w-[920px] space-y-5">
        {headerBlock}
        {filtersBlock}
        {loadError && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-[13px] tracking-tight text-amber-800 dark:border-amber-500/25 dark:bg-amber-500/10 dark:text-amber-200">
            {loadError}
          </div>
        )}
        {entriesGrid}
        {filtered.length === 0 ? emptyBlock : null}
      </div>
      {formModal}
    </div>
  );
}

export function ExtremistDetailPage() {
  const { isMobile } = useContext(ShellContext);
  const { role, authSession } = useStore();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const canEdit = role === "editor" || role === "admin" || role === "content_editor" || role === "platform_admin";
  const [entry, setEntry] = useState<ExtremistEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadEntry = useCallback(async () => {
    if (!id) {
      setError("Запись не найдена.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const token = authSession?.access_token ?? apiClient.loadTokens()?.access_token;
      const raw = canEdit && token
        ? await apiClient.getAdminExtremistEntry<RawExtremistEntry>(token, id)
        : await apiClient.getExtremistEntry<RawExtremistEntry>(id);
      setEntry(adaptExtremistEntry(raw));
    } catch (err) {
      setEntry(null);
      setError(err instanceof Error ? err.message : "Не удалось открыть запись.");
    } finally {
      setLoading(false);
    }
  }, [authSession?.access_token, canEdit, id]);

  useEffect(() => {
    loadEntry();
  }, [loadEntry]);

  const allMedia = entry ? [...(entry.mediaUrls ?? []), ...(entry.attachmentUrls ?? [])] : [];

  const loadingBlock = (
    <div className="grid min-h-[320px] place-items-center rounded-[28px] border border-black/[0.06] bg-white p-8 text-center dark:border-white/[0.08] dark:bg-white/[0.04]">
      <div>
        <RefreshCw size={22} className="mx-auto animate-spin text-[#0056FF]" />
        <div className="mt-3 text-[14px] tracking-tight text-black/55 dark:text-white/55">Загружаем карточку…</div>
      </div>
    </div>
  );

  const errorBlock = (
    <div className="grid min-h-[320px] place-items-center rounded-[28px] border border-red-200/70 bg-red-50 p-8 text-center dark:border-red-500/25 dark:bg-red-500/10">
      <div>
        <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-200">
          <AlertTriangle size={22} />
        </div>
        <div className="mt-4 tracking-tight text-red-900 dark:text-red-100" style={{ fontSize: 20 }}>
          Карточка недоступна
        </div>
        <p className="mt-2 max-w-[46ch] text-[13px] leading-relaxed text-red-800/75 dark:text-red-200/75">
          {error || "Запись не опубликована или была удалена."}
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          <button
            type="button"
            onClick={() => navigate("/news")}
            className="rounded-2xl border border-red-200 bg-white px-4 py-2.5 text-[13px] tracking-tight text-red-700 dark:border-red-500/20 dark:bg-white/[0.05] dark:text-red-100"
          >
            Вернуться к новостям
          </button>
          <button
            type="button"
            onClick={loadEntry}
            className="rounded-2xl bg-[#0056FF] px-4 py-2.5 text-[13px] tracking-tight text-white"
          >
            Повторить
          </button>
        </div>
      </div>
    </div>
  );

  const content = entry && (
    <div className="space-y-5">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="hidden items-center gap-2 text-[13px] tracking-tight text-black/45 hover:text-[#0056FF] dark:text-white/45 md:inline-flex"
      >
        <ChevronLeft size={15} /> Назад
      </button>

      <section className="overflow-hidden rounded-[32px] border border-black/[0.06] bg-white shadow-[0_24px_80px_-56px_rgba(15,23,42,0.55)] dark:border-white/[0.08] dark:bg-white/[0.04]">
        {entry.coverUrl ? (
          <div className="h-[260px] w-full overflow-hidden bg-black/[0.04] dark:bg-white/[0.04]">
            <img src={entry.coverUrl} alt="" className="h-full w-full object-cover" />
          </div>
        ) : (
          <div className="flex min-h-[220px] items-end justify-between overflow-hidden bg-gradient-to-br from-red-50 via-white to-blue-50 p-6 dark:from-red-500/15 dark:via-white/[0.04] dark:to-blue-500/10">
            <div className="grid h-16 w-16 place-items-center rounded-3xl bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-200">
              <AlertTriangle size={28} />
            </div>
            <div className="max-w-[220px] text-right text-[12px] uppercase tracking-[0.18em] text-black/35 dark:text-white/35">
              проверка только по официальному ресурсу
            </div>
          </div>
        )}
        <div className="p-5 md:p-7">
          <div className="flex flex-wrap items-center gap-1.5">
            <Pill tone={entry.status === "published" ? "ok" : "ghost"}>{EXTREMIST_STATUS_LABEL[entry.status]}</Pill>
            <Pill tone="warn">{EXTREMIST_CATEGORY_LABEL[entry.category]}</Pill>
            {entry.status === "draft" && canEdit && <Pill tone="lavender">видно редакции</Pill>}
          </div>
          <h1 className="mt-4 max-w-[880px] tracking-tight text-black dark:text-white" style={{ fontSize: isMobile ? 30 : 44, lineHeight: 1.03 }}>
            {entry.title}
          </h1>
          {entry.shortDescription && (
            <p className="mt-4 max-w-[760px] text-[16px] leading-relaxed tracking-tight text-black/60 dark:text-white/60">
              {entry.shortDescription}
            </p>
          )}
          <div className="mt-6 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl bg-black/[0.025] p-4 dark:bg-white/[0.045]">
              <div className="flex items-center gap-2 text-[12px] tracking-tight text-black/40 dark:text-white/40">
                <CalendarClock size={14} /> Дата включения
              </div>
              <div className="mt-2 text-[14px] tracking-tight text-black dark:text-white">
                {formatExtremistDate(entry.includedAt)}
              </div>
            </div>
            <div className="rounded-2xl bg-black/[0.025] p-4 dark:bg-white/[0.045]">
              <div className="flex items-center gap-2 text-[12px] tracking-tight text-black/40 dark:text-white/40">
                <Check size={14} /> Дата проверки
              </div>
              <div className="mt-2 text-[14px] tracking-tight text-black dark:text-white">
                {formatExtremistDate(entry.lastCheckedAt)}
              </div>
            </div>
            <div className="rounded-2xl bg-black/[0.025] p-4 dark:bg-white/[0.045]">
              <div className="flex items-center gap-2 text-[12px] tracking-tight text-black/40 dark:text-white/40">
                <Shield size={14} /> Источник
              </div>
              <div className="mt-2 truncate text-[14px] tracking-tight text-black dark:text-white">
                {entry.sourceName || sourceHost(entry.sourceUrl)}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-5">
          <Card>
            <div className="flex items-start gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-red-50 text-red-500 dark:bg-red-500/15 dark:text-red-200">
                <AlertTriangle size={18} />
              </span>
              <div>
                <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 20 }}>
                  Как использовать эту информацию
                </div>
                <p className="mt-2 text-[14px] leading-relaxed tracking-tight text-black/58 dark:text-white/58">
                  Карточка носит справочный характер и помогает перейти к официальной записи.
                  Перед любыми действиями проверяйте актуальность, формулировки и дату публикации
                  на официальном ресурсе. Приложение не воспроизводит запрещённые материалы, а
                  показывает только служебное описание и ссылку на источник.
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 20 }}>
                  Типы и признаки записи
                </div>
                <p className="mt-1 text-[13px] tracking-tight text-black/50 dark:text-white/50">
                  Эти метки используются для фильтрации раздела.
                </p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {entry.contentTypes.length > 0 ? entry.contentTypes.map((type) => (
                <span
                  key={type}
                  className="rounded-full bg-[#E3E7FC] px-3 py-1.5 text-[12px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"
                >
                  {EXTREMIST_CONTENT_TYPE_LABEL[type]}
                </span>
              )) : (
                <span className="rounded-full bg-black/[0.04] px-3 py-1.5 text-[12px] tracking-tight text-black/45 dark:bg-white/[0.06] dark:text-white/45">
                  Метки не указаны
                </span>
              )}
            </div>
          </Card>

          {allMedia.length > 0 && (
            <Card>
              <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 20 }}>
                Медиа и вложения
              </div>
              <p className="mt-1 text-[13px] tracking-tight text-black/50 dark:text-white/50">
                Файлы и ссылки добавляются только как справочные материалы к официальной записи.
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {allMedia.map((url, index) => (
                  <a
                    key={`${url}-${index}`}
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="group overflow-hidden rounded-2xl border border-black/[0.06] bg-black/[0.02] transition hover:border-[#0056FF]/35 dark:border-white/[0.08] dark:bg-white/[0.04]"
                  >
                    {isImageUrl(url) ? (
                      <img src={url} alt="" className="h-36 w-full object-cover" />
                    ) : (
                      <div className="grid h-36 place-items-center bg-white dark:bg-white/[0.04]">
                        <FileText size={28} className="text-black/30 dark:text-white/30" />
                      </div>
                    )}
                    <div className="flex items-center gap-2 p-3">
                      <Camera size={14} className="shrink-0 text-[#0056FF]" />
                      <span className="min-w-0 flex-1 truncate text-[12px] tracking-tight text-black/55 dark:text-white/55">
                        {sourceHost(url)}
                      </span>
                      <ExternalLink size={13} className="text-black/35 group-hover:text-[#0056FF] dark:text-white/35" />
                    </div>
                  </a>
                ))}
              </div>
            </Card>
          )}
        </div>

        <aside className="space-y-5">
          <Card>
            <div className="flex items-center gap-2 text-[12px] uppercase tracking-[0.14em] text-[#0056FF]">
              <Shield size={14} /> Официальный источник
            </div>
            <div className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>
              {entry.sourceName || sourceHost(entry.sourceUrl)}
            </div>
            <div className="mt-2 break-all text-[12px] leading-relaxed tracking-tight text-black/45 dark:text-white/45">
              {entry.sourceUrl}
            </div>
            <a
              href={entry.sourceUrl}
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#0056FF] px-4 py-3 text-[13px] font-medium tracking-tight text-white shadow-[0_16px_34px_-22px_rgba(0,86,255,0.75)]"
            >
              Открыть источник <ArrowUpRight size={14} />
            </a>
          </Card>

          <Card>
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>
              Проверочный статус
            </div>
            <div className="mt-3 space-y-2 text-[13px] tracking-tight text-black/55 dark:text-white/55">
              <div className="flex items-center justify-between gap-3">
                <span>Статус</span>
                <span className="text-black dark:text-white">{EXTREMIST_STATUS_LABEL[entry.status]}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>Проверка</span>
                <span className="text-right text-black dark:text-white">{formatExtremistDate(entry.lastCheckedAt)}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>Обновлено</span>
                <span className="text-right text-black dark:text-white">{formatExtremistDate(entry.updatedAt)}</span>
              </div>
            </div>
          </Card>
        </aside>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Материал" onBack={() => navigate(-1)} />
        <div className="px-5">
          {loading ? loadingBlock : entry ? content : errorBlock}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1180px] p-8">
      {loading ? loadingBlock : entry ? content : errorBlock}
    </div>
  );
}
