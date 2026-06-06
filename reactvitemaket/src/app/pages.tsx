import React, { useContext, useState } from "react";
import { useNavigate, useOutletContext, useParams } from "react-router";
import { ShellContext, MobileTopBar } from "./App";
import { useStore, DOC_TYPE_LABEL, maskDocumentNumber } from "./data/store";
import {
  Search, FileText, Home, Building2, Briefcase, Hammer, Heart, Shield, Wallet,
  Plus, Check, Lock, MapPin, CalendarClock, ChevronRight, AlertCircle, Clock,
  ArrowUpRight, ArrowRight, X, ScanLine, EyeOff, Baby, Award, BookOpen, Star, Trash2,
  Bell, ChevronLeft, Edit3, Newspaper
} from "lucide-react";
import { Card, Pill, PrimaryButton, GhostButton, Logo, LocationPicker } from "./components/belp-ui";
import { motion } from "motion/react";
import { UserDocument } from "./data/types";
import { OFFICIAL_SOURCES } from "./data/mock";
import { matchesQuery } from "./services/search";
import { ProfileEditModal, ProposeButton, MyContributions, EditorialFeed, DocumentCardModal } from "./components/extra-screens";

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

export function CatalogPage() {
  const { isMobile } = useContext(ShellContext);
  const { scenarios, categories } = useStore();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [activeCat, setActiveCat] = useState("all");

  const filtered = scenarios.filter(s => {
    if (activeCat !== "all" && s.category !== activeCat) return false;
    if (q && !s.title.toLowerCase().includes(q.toLowerCase())) return false;
    return true;
  });

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Каталог ситуаций" onBack={() => navigate(-1)} />
        <div className="px-5">
          <div className="flex items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3 dark:border-white/[0.06] dark:bg-[#0F1117]">
            <Search size={16} className="text-black/40 dark:text-white/40" />
            <input placeholder="Найти ситуацию" value={q} onChange={e => setQ(e.target.value)} className="flex-1 bg-transparent tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
          </div>
          <div className="mt-3"><ProposeButton kind="scenario" className="w-full justify-center" /></div>
          <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden">
            <button onClick={() => setActiveCat("all")} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${activeCat==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
            {categories.map(c => (
              <button key={c.id} onClick={() => setActiveCat(c.id)} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${activeCat===c.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{c.name}</button>
            ))}
          </div>
          {filtered.length === 0 && <div className="mt-10 text-center text-[13px] text-black/55 dark:text-white/55">Сценарии не найдены</div>}
          <div className="mt-5 grid grid-cols-1 gap-3">
            {filtered.map((s, i) => (
              <button key={s.id} onClick={() => navigate(`/scenarios/${s.id}`)} className="block text-left w-full">
                <Card interactive className="p-4 flex gap-4 items-center">
                  <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl"
                    style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>
                    <CatIcon cat={s.category} />
                  </div>
                  <div>
                    <div className="text-[11px] text-[#0056FF] mb-1">{catLabel(s.category)}</div>
                    <div className="tracking-tight text-black dark:text-white leading-tight">{s.title}</div>
                    <div className="mt-1 text-[12px] tracking-tight text-black/50 dark:text-white/50">{s.estimatedTime} · {s.difficulty === "easy" ? "Простой" : "Сложный"}</div>
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
      <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Жизненные сценарии</div>
      <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">
        Выберите ситуацию, и приложение покажет пошаговый план действий.
      </p>
      
      <div className="mt-6 flex gap-3 items-center max-w-[640px]">
        <div className="flex flex-1 items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3 dark:border-white/[0.06] dark:bg-[#0F1117]">
          <Search size={16} className="text-black/40 dark:text-white/40" />
          <input placeholder="Найти сценарий" value={q} onChange={e => setQ(e.target.value)} className="flex-1 bg-transparent tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
        </div>
        <ProposeButton kind="scenario" className="shrink-0 self-stretch" />
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <button onClick={() => setActiveCat("all")} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${activeCat==="all" ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>Все</button>
        {categories.map(c => (
          <button key={c.id} onClick={() => setActiveCat(c.id)} className={`shrink-0 rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${activeCat===c.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{c.name}</button>
        ))}
      </div>
      
      <div className="mt-8"><EditorialFeed kind="scenario" title="Ситуации от редакции и пользователей" /></div>
      {filtered.length === 0 && <div className="mt-10 text-[14px] text-black/55 dark:text-white/55">Сценарии не найдены. Попробуйте изменить запрос или категорию.</div>}
      
      <div className="mt-6 grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((s, i) => (
          <button key={s.id} className="text-left" onClick={() => navigate(`/scenarios/${s.id}`)}>
            <Card interactive className="p-5 flex flex-col h-full">
              <div className="grid h-12 w-12 place-items-center rounded-2xl" style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>
                <CatIcon cat={s.category} />
              </div>
              <div className="mt-8 tracking-tight text-black dark:text-white" style={{ fontSize: 16, lineHeight: 1.2 }}>{s.title}</div>
              <div className="mt-1 text-[12px] tracking-tight text-black/50 dark:text-white/50">{catLabel(s.category)}</div>
              <div className="mt-4 flex flex-col gap-1 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                <span>Срок: {s.estimatedTime}</span>
                <span>Задач: {s.taskCount ?? s.stages.reduce((n, st) => n + st.tasks.length, 0)}</span>
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
  const [activeCategory, setActiveCategory] = useState<string>("documents");
  const [activeStep, setActiveStep] = useState<number>(0);

  // Демо-карточки сценариев для блока «Попробуйте»
  const DEMO_CATEGORIES = [
    { id: "documents", label: "Документы", icon: <Shield size={18} />, color: "from-[#001A66] to-[#0056FF]" },
    { id: "housing", label: "ЖКХ", icon: <Home size={18} />, color: "from-[#0056FF] to-[#2277FF]" },
    { id: "taxes", label: "Налоги", icon: <Wallet size={18} />, color: "from-[#2277FF] to-[#9BB8FF]" },
    { id: "family", label: "Семья", icon: <Heart size={18} />, color: "from-[#001A66] to-[#9BB8FF]" },
  ];

  const DEMO_STEPS = [
    { title: "Выберите сценарий", desc: "Паспорт, ЖКХ, налоги, прописка — уже готовые пошаговые планы.", icon: <Search size={20} /> },
    { title: "Создайте свою ситуацию", desc: "Один тап — и в «Моих ситуациях» появятся задачи, документы, сроки.", icon: <Plus size={20} /> },
    { title: "Получайте напоминания", desc: "Белпомощник напомнит о дедлайнах и приближающихся сроках документов.", icon: <Bell size={20} /> },
  ];

  return (
    <div className="relative min-h-[100dvh] overflow-hidden bg-[#F6F7FB] dark:bg-[#07080C]">
      {/* Декоративные blur-орбы */}
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-[#0056FF]/15 blur-3xl" />
      <div className="pointer-events-none absolute -right-24 top-1/3 h-80 w-80 rounded-full bg-[#2277FF]/10 blur-3xl" />

      <div className="relative mx-auto max-w-[1100px] px-5 pb-32 pt-6 sm:px-8 sm:pt-10">
        {/* v1.0: brand-bar */}
        <div className="flex items-center justify-between">
          <button onClick={() => navigate("/welcome")} className="flex items-center gap-2">
            <Logo size={30} />
          </button>
          <button
            onClick={() => navigate("/login")}
            className="text-[13px] tracking-tight text-black/65 hover:text-black dark:text-white/65 dark:hover:text-white"
          >
            Войти
          </button>
        </div>

        {/* Hero */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="mt-12">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#E3E7FC] px-3 py-1.5 text-[12px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
            <Sparkles size={12} /> mobile-first · Беларусь
          </span>
          <h1 className="mt-5 max-w-[18ch] text-[36px] font-medium leading-[1.05] tracking-tight text-black dark:text-white sm:text-[56px]">
            Помощник, который <span className="bg-gradient-to-r from-[#0056FF] to-[#2277FF] bg-clip-text text-transparent">превращает проблему</span> в понятный план
          </h1>
          <p className="mt-5 max-w-[58ch] text-[15px] leading-relaxed tracking-tight text-black/65 dark:text-white/65 sm:text-[18px]">
            Найдите жизненную ситуацию, получите чек-лист, документы, сроки и напоминания. Без канцелярита. Паспорт, ЖКХ, налоги, прописка — по шагам.
          </p>

          <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
            <PrimaryButton onClick={() => navigate("/register")} className="px-7 sm:w-auto">Зарегистрироваться</PrimaryButton>
            <GhostButton onClick={() => navigate("/login")} className="px-7">У меня уже есть аккаунт</GhostButton>
          </div>
        </motion.div>

        {/* Категории — интерактивные табы с превью */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }} className="mt-14">
          <div className="flex items-end justify-between">
            <div>
              <div className="text-[12px] uppercase tracking-[0.14em] text-[#0056FF]">Попробуйте</div>
              <h2 className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 24 }}>Жизненные ситуации</h2>
            </div>
          </div>
          <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {DEMO_CATEGORIES.map((c) => (
              <button
                key={c.id}
                onClick={() => setActiveCategory(c.id)}
                className={`flex items-center gap-2 rounded-2xl border px-4 py-3 text-left transition-all ${activeCategory === c.id ? "border-[#0056FF] bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "border-black/[0.06] bg-white text-black/70 dark:border-white/[0.06] dark:bg-white/[0.04] dark:text-white/70"}`}
              >
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br text-white" style={{ backgroundImage: `linear-gradient(135deg, var(--tw-gradient-stops))` }}>
                  {c.icon}
                </span>
                <span className="text-[14px] font-medium tracking-tight">{c.label}</span>
              </button>
            ))}
          </div>
        </motion.div>

        {/* Шаги работы */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} className="mt-14">
          <div className="text-[12px] uppercase tracking-[0.14em] text-[#0056FF]">Как это работает</div>
          <h2 className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 24 }}>Три шага до результата</h2>
          <div className="mt-5 space-y-3">
            {DEMO_STEPS.map((step, i) => (
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
        </motion.div>

        {/* CTA блок */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }} className="mt-14 overflow-hidden rounded-3xl p-1">
          <div
            className="rounded-[22px] p-8 text-white sm:p-10"
            style={{ background: "radial-gradient(120% 100% at 0% 0%, #2277FF 0%, #0056FF 45%, #001A66 100%)" }}
          >
            <div className="text-[12px] uppercase tracking-[0.14em] text-white/70">Готовы попробовать?</div>
            <h3 className="mt-2 max-w-[20ch] tracking-tight" style={{ fontSize: 28, lineHeight: 1.1 }}>
              Зарегистрируйтесь — это бесплатно и занимает минуту.
            </h3>
            <p className="mt-3 max-w-[48ch] text-[14px] leading-relaxed text-white/80">
              После регистрации вы получите доступ к каталогу ситуаций, документам, уведомлениям и админ-панели (если у вас есть роль редактора или администратора).
            </p>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={() => navigate("/register")}
                className="rounded-2xl bg-white px-6 py-3 text-[14px] font-semibold tracking-tight text-[#0056FF] shadow-[0_8px_24px_-8px_rgba(0,0,0,0.25)]"
              >
                Создать аккаунт
              </button>
              <button
                onClick={() => navigate("/login")}
                className="rounded-2xl border border-white/30 bg-white/10 px-6 py-3 text-[14px] font-semibold tracking-tight text-white backdrop-blur"
              >
                У меня уже есть аккаунт
              </button>
            </div>
          </div>
        </motion.div>

        {/* Footer */}
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
      <div className="relative mx-auto flex min-h-[100dvh] max-w-[1100px] flex-col justify-center px-5 py-12 sm:px-8">
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

  // v0.7: объединяем «Новости» (статьи с kind='news') и «Закон-апдейты»
  // (массив legal) в одну ленту с фильтр-чипами. Подписка на закон-апдейты
  // уже есть в settings.notifications.legal.
  type FilterKey = "all" | "news" | "law";
  const [filter, setFilter] = useState<FilterKey>("all");

  const newsList = articles
    .filter((a) => a.status === "published" && a.kind === "news")
    .map((a) => ({
      kind: "news" as const,
      title: a.title,
      summary: a.summary ?? "",
      date: a.publishedAt ?? a.updatedAt ?? "",
      // никаких дополнительных полей
    }));

  const lawList = legal.map((l) => ({
    kind: "law" as const,
    title: l.title,
    summary: l.summary ?? "",
    date: l.effectiveDate ?? "",
    sourceUrl: l.sourceUrl,
    priority: l.priority,
  }));

  const combined =
    filter === "news" ? newsList
    : filter === "law" ? lawList
    : [...newsList, ...lawList].sort((a, b) => (b.date ?? "").localeCompare(a.date ?? ""));

  const filterCounts = {
    all: newsList.length + lawList.length,
    news: newsList.length,
    law: lawList.length,
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
        <div className="px-5 space-y-4">
          <ProposeButton kind="news" className="w-full justify-center" />
          <div className="flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden">{filterChips}</div>
          <div className="space-y-3">
            {combined.map((item, i) => (
              <NewsCard key={`${item.kind}-${i}-${item.title}`} item={item} navigate={navigate} />
            ))}
          </div>
          {empty}
        </div>
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
        <div className="flex flex-wrap gap-2">{filterChips}</div>
      </div>
      <div className="mt-8 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {combined.map((item, i) => (
          <NewsCard key={`${item.kind}-${i}-${item.title}`} item={item} navigate={navigate} />
        ))}
      </div>
      {empty}
    </div>
  );
}

function NewsCard({
  item, navigate,
}: {
  item:
    | { kind: "news"; title: string; summary: string; date: string }
    | { kind: "law"; title: string; summary: string; date: string; sourceUrl?: string; priority?: "low" | "medium" | "high" };
  navigate: (path: string) => void;
}) {
  const isLaw = item.kind === "law";
  return (
    <button
      onClick={() => isLaw ? navigate("/legal") : navigate("/news")}
      className="block text-left"
    >
      <Card className="flex h-full flex-col p-5">
        <div className="flex items-center gap-2">
          <Pill tone={isLaw ? "warn" : "lavender"}>
            {isLaw ? "Закон-апдейт" : "Новость"}
          </Pill>
          {isLaw && item.priority === "high" && <Pill tone="warn"><AlertCircle size={11} /> Важное</Pill>}
        </div>
        <div className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 16, lineHeight: 1.25 }}>{item.title}</div>
        {item.summary && <div className="mt-1 line-clamp-3 text-[13px] tracking-tight text-black/55 dark:text-white/55">{item.summary}</div>}
        {item.date && <div className="mt-auto pt-3 text-[11px] tracking-tight text-black/40 dark:text-white/40">{item.date}</div>}
      </Card>
    </button>
  );
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
  const { legal } = useStore();
  const item = legal.find(l => l.id === params?.id);
  
  if (!item) return <div className="p-10">Новость не найдена</div>;

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
          <Pill tone="lavender">{catLabel(item.category)}</Pill>
          <h1 className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: isMobile ? 26 : 32, lineHeight: 1.1 }}>{item.title}</h1>
          <div className="mt-3 flex gap-4 text-[13px] text-black/55 dark:text-white/55">
            <span className="flex items-center gap-1.5"><Clock size={14} /> с {item.effectiveDate}</span>
          </div>
        </div>

        <Card className="mt-6 p-5">
          <div className="font-medium text-[15px] mb-1">Что изменилось?</div>
          <p className="text-[14px] text-black/70 dark:text-white/70 leading-relaxed whitespace-pre-wrap">{item.whatChanged || item.summary}</p>
          
          <div className="mt-6 font-medium text-[15px] mb-1">Кого это касается?</div>
          <p className="text-[14px] text-black/70 dark:text-white/70 leading-relaxed whitespace-pre-wrap">{item.whoAffected || "Всех граждан РБ"}</p>

          <div className="mt-6 font-medium text-[15px] mb-1">Что сделать?</div>
          <p className="text-[14px] text-black/70 dark:text-white/70 leading-relaxed whitespace-pre-wrap">{item.whatToDo}</p>
        </Card>
        
        <div className="mt-6 rounded-2xl border border-amber-200/60 bg-amber-50 p-4 text-[13px] tracking-tight text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
          Информация носит справочный характер. Перед действиями рекомендуется сверить требования на официальном ресурсе.
        </div>
      </div>
    </div>
  );
}

export function NotificationsPage() {
  const { isMobile } = useContext(ShellContext);
  const { notifications, markAllRead } = useStore();
  const navigate = useNavigate();

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <MobileTopBar title="Уведомления" onBack={() => navigate(-1)} right={
          <button onClick={markAllRead} className="grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"><Check size={15} className="text-black dark:text-white" /></button>
        } />
        <div className="px-5 space-y-3">
          {notifications.map((it) => (
            <Card key={it.id} className={`flex items-start gap-3 p-4 ${it.read ? 'opacity-60' : ''}`}>
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
          <Card key={it.id} className={`flex items-start gap-4 p-5 ${it.read ? 'opacity-60' : ''}`}>
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
        ))}
      </div>
    </div>
  );
}

export function ProfilePage() {
  const { isMobile, openAdmin } = useContext(ShellContext);
  const { profile, currentUser } = useStore();
  const navigate = useNavigate();
  const [editOpen, setEditOpen] = useState(false);
  const canEdit = currentUser.role !== "guest";
  const isStaff = currentUser.role === "admin" || currentUser.role === "editor";

  if (isMobile) {
    return (
      <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
        <ProfileEditModal open={editOpen} onClose={() => setEditOpen(false)} />
        <MobileTopBar title="Профиль" onBack={() => navigate(-1)} right={
          canEdit ? <button onClick={() => setEditOpen(true)} className="grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"><Edit3 size={15} className="text-black dark:text-white" /></button> : undefined
        } />
        <div className="px-5 space-y-4">
          <Card className="flex items-center gap-4 p-4">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#0056FF] to-[#2277FF] flex items-center justify-center text-white text-lg font-medium">{profile?.name ? profile.name[0] : 'П'}</div>
            <div className="flex-1">
              <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 17 }}>{profile?.name}</div>
              <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{profile?.city} · {profile?.region}</div>
            </div>
          </Card>
          
          <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45 pl-1">Личные данные</div>
          <Card className="p-4 space-y-3 text-[13px]">
            <div className="flex justify-between"><span className="text-black/55 dark:text-white/55">Email</span><span className="text-black dark:text-white">{profile?.email}</span></div>
            <div className="flex justify-between"><span className="text-black/55 dark:text-white/55">Роль</span><span className="text-black dark:text-white">{roleLabel(currentUser.role)}</span></div>
          </Card>
          
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
                <span className="text-[14px] text-[#0056FF]">{currentUser.role === "editor" ? "Редактор контента" : "Админ-панель"}</span>
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
    <div className="p-8 max-w-[800px]">
      <ProfileEditModal open={editOpen} onClose={() => setEditOpen(false)} />
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Аккаунт</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Профиль</div>
        </div>
        {canEdit && <GhostButton className="gap-2 px-4" onClick={() => setEditOpen(true)}><Edit3 size={15} /> Редактировать</GhostButton>}
      </div>

      <div className="mt-8 flex items-center gap-6">
        <div className="h-24 w-24 rounded-3xl bg-gradient-to-br from-[#0056FF] to-[#2277FF] flex items-center justify-center text-white text-3xl font-medium">{profile?.name ? profile.name[0] : 'П'}</div>
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
      <MyContributions />
    </div>
  );
}

export function ProblemDetailPage() {
  const { isMobile } = useContext(ShellContext);
  const params = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { problemById } = useStore();
  const item = problemById(params?.id || "");
  const [checks, setChecks] = useState<Record<string, boolean>>({});

  if (!item) return <div className="p-10">Проблема не найдена</div>;

  const total = item.steps.length;
  const done = item.steps.filter(s => checks[s.id]).length;
  const progress = total ? Math.round((done / total) * 100) : 0;

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
          <PrimaryButton className="flex-1 text-[14px]">Создать персональный план</PrimaryButton>
          <GhostButton className="flex-1 text-[14px]">Сохранить в избранное</GhostButton>
        </div>
      </div>
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
    <div className="flex h-full flex-col items-center justify-center p-5 relative overflow-hidden bg-[#F6F7FB] dark:bg-[#0B0D13]">
      <div className="pointer-events-none absolute -top-24 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-[#0056FF]/10 blur-3xl" />
      <Card className="w-full max-w-[400px] p-6 sm:p-8 z-10 shadow-xl border-0">
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-[#0056FF] to-[#2277FF] text-white shadow-sm">
              <Shield size={16} />
            </div>
            <span className="text-xl font-medium tracking-tight text-black dark:text-white">Белпомощник</span>
          </div>
        </div>
        <h1 className="text-2xl font-medium text-center text-black dark:text-white mb-6 tracking-tight">Вход</h1>
        
        <div className="space-y-4">
          <div>
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
          </div>
          <div>
            <input type="password" placeholder="Пароль" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") handleLogin(); }} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
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
    <div className="flex h-full flex-col items-center justify-center p-5 relative overflow-hidden bg-[#F6F7FB] dark:bg-[#0B0D13]">
      <div className="pointer-events-none absolute -bottom-24 right-1/4 h-80 w-80 rounded-full bg-[#0056FF]/10 blur-3xl" />
      <div className="h-full w-full overflow-y-auto pt-10 pb-20 flex justify-center [&::-webkit-scrollbar]:hidden">
        <Card className="w-full max-w-[400px] p-6 sm:p-8 z-10 shadow-xl border-0 h-fit">
          <div className="flex justify-center mb-6">
            <div className="flex items-center gap-2">
              <div className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-[#0056FF] to-[#2277FF] text-white shadow-sm">
                <Shield size={16} />
              </div>
              <span className="text-xl font-medium tracking-tight text-black dark:text-white">Белпомощник</span>
            </div>
          </div>
          <h1 className="text-2xl font-medium text-center text-black dark:text-white mb-6 tracking-tight">Создание аккаунта</h1>
          
          <div className="space-y-4">
            <input type="text" placeholder="Имя и фамилия" value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
            <input type="password" placeholder="Пароль" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
            <input type="password" placeholder="Повтор пароля" value={repeat} onChange={(e) => setRepeat(e.target.value)} className="w-full rounded-xl border border-black/10 bg-black/[0.02] px-4 py-3.5 text-[14px] outline-none transition-all focus:border-[#0056FF] focus:bg-white dark:border-white/10 dark:bg-white/[0.02] dark:text-white dark:focus:border-[#0056FF] dark:focus:bg-[#0F1117]" />
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

  return (
    <div className="space-y-8">
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
