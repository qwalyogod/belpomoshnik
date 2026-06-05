import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import {
  Search, FileText, Building2, Lock, Check, ChevronRight, ChevronLeft, AlertCircle,
  ArrowUpRight, X, Star, Plus, Trash2, Edit3, Shield, Globe, BellRing, EyeOff,
  Award, BookOpen, Sparkles, Clock, MapPin,
} from "lucide-react";
import { Card, Pill, PrimaryButton, GhostButton } from "./belp-ui";
import { ContentEditor, type ContentKind, type ContentDraft } from "./content-editor";
import { useNavigate } from "react-router";
import { useStore, maskDocumentNumber, DOC_TYPE_LABEL } from "../data/store";
import { apiClient } from "../services/api";
import { buildSuggestions, getRecentSearches, addRecentSearch, POPULAR_QUERIES, SuggestionItem } from "../services/search";
import { matchInstitutions, hasProfileLocation } from "../services/institutions";
import { LEARNING_QUIZ, LEARNING_CATEGORIES } from "../data/mock";
import { Scenario, UserDocumentType, Lang, Article, ArticleKind } from "../data/types";

/* ---------------- DISCLAIMER ---------------- */
export function SourcesDisclaimer() {
  return (
    <div className="rounded-2xl border border-amber-200/60 bg-amber-50 p-3.5 text-[12px] tracking-tight text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
      Информация носит справочный характер. Перед подачей документов уточняйте актуальные требования
      на официальных ресурсах.
    </div>
  );
}

/* ---------------- SCENARIO DETAIL ---------------- */
export function ScenarioDetail({
  scenario, onBack, onOpenMySituation, onOpenScenario, onProtected,
}: {
  scenario: Scenario;
  onBack: () => void;
  onOpenMySituation: (id: string) => void;
  onOpenScenario: (id: string) => void;
  onProtected: () => boolean; // returns true if allowed
}) {
  const { role, createSituation, favorites, toggleFavorite, situationByScenario, scenarioById, profile } = useStore();
  const isFav = favorites.includes(scenario.id);
  const matchedInstitutions = matchInstitutions(scenario.institutions, profile);
  const hasLocation = hasProfileLocation(profile);
  const existing = situationByScenario(scenario.id);

  const handleCreate = () => {
    if (!onProtected()) return;
    const id = createSituation(scenario.id);
    if (!id) return;
    onOpenMySituation(id);
  };

  const diffLabel = scenario.difficulty === "easy" ? "Простой" : scenario.difficulty === "medium" ? "Средний" : "Сложный";

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55">
        <ChevronLeft size={14} /> Жизненные сценарии
      </button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-[640px]">
          <div className="flex items-center gap-2 flex-wrap">
            <Pill tone="lavender">{categoryLabel(scenario.category)}</Pill>
            <Pill tone="ghost">{diffLabel}</Pill>
            <Pill tone="ghost">Срок: {scenario.estimatedTime}</Pill>
            {existing && <Pill tone={existing.status === "done" ? "ok" : "royal"}>{existing.status === "done" ? "Завершено" : "В процессе"}</Pill>}
          </div>
          <h1 className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 32, lineHeight: 1.08 }}>{scenario.title}</h1>
          <p className="mt-2 tracking-tight text-black/60 dark:text-white/60">{scenario.longDescription}</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => toggleFavorite(scenario.id)}
            aria-label="В избранное"
            className={`grid h-11 w-11 place-items-center rounded-xl border ${isFav ? "border-[#0056FF] bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "border-black/[0.08] bg-white text-black/55 dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-white/55"}`}
          >
            <Star size={16} fill={isFav ? "currentColor" : "none"} />
          </button>
          <PrimaryButton onClick={handleCreate} className="h-11 px-5">
            {existing ? "Открыть мою ситуацию" : "Создать мою ситуацию"}
          </PrimaryButton>
        </div>
      </div>

      <Card className="p-5">
        <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Для кого</div>
        <div className="mt-1 tracking-tight text-black dark:text-white">{scenario.forWhom}</div>
      </Card>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>Этапы и задачи</div>
          {scenario.stages.map((stage, idx) => (
            <Card key={stage.id} className="p-5">
              <div className="flex items-center gap-3">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-[#E3E7FC] text-[12px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{idx + 1}</span>
                <div className="tracking-tight text-black dark:text-white">{stage.title}</div>
              </div>
              <div className="mt-3 space-y-2.5">
                {stage.tasks.map((t) => {
                  const blocked = t.blockedBy && t.blockedBy.length > 0;
                  return (
                    <div key={t.id} className="flex items-start gap-3 rounded-2xl bg-[#F6F7FB] px-3.5 py-3 dark:bg-white/[0.03]">
                      <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md border border-black/15 bg-white text-black/30 dark:border-white/15 dark:bg-white/[0.05]">
                        {blocked ? <Lock size={12} /> : null}
                      </span>
                      <div className="flex-1">
                        <div className="tracking-tight text-black dark:text-white">{t.title}</div>
                        <div className="mt-0.5 flex items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                          <span>{taskKindLabel(t.kind)}</span>
                          {t.durationHint && <span>· {t.durationHint}</span>}
                          {blocked && <span className="text-amber-600 dark:text-amber-400">· зависит от предыдущих</span>}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          ))}

          {scenario.relatedIds.length > 0 && (
            <Card className="p-5">
              <div className="tracking-tight text-black dark:text-white">Связанные сценарии</div>
              <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
                {scenario.relatedIds.map(rid => {
                  const r = scenarioById(rid);
                  if (!r) return null;
                  return (
                    <button key={rid} onClick={() => onOpenScenario(rid)} className="flex items-center justify-between rounded-2xl bg-[#F6F7FB] px-4 py-3 text-left dark:bg-white/[0.03]">
                      <div>
                        <div className="text-[11px] tracking-tight text-[#0056FF]">{categoryLabel(r.category)}</div>
                        <div className="tracking-tight text-black dark:text-white">{r.title}</div>
                      </div>
                      <ChevronRight size={16} className="text-black/30 dark:text-white/30" />
                    </button>
                  );
                })}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-5">
          <Card className="p-5">
            <div className="tracking-tight text-black dark:text-white">Документы</div>
            <div className="mt-3 space-y-2">
              {scenario.documents.map(d => (
                <div key={d.id} className="flex items-start gap-2 text-[13px] tracking-tight text-black/75 dark:text-white/75">
                  <Check size={14} className="mt-0.5 text-[#0056FF]" />
                  <div>
                    <div>{d.name}</div>
                    {d.note && <div className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{d.note}</div>}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <div className="flex items-center gap-2">
              <div className="tracking-tight text-black dark:text-white">Куда обращаться</div>
              {hasLocation && <Pill tone="lavender">{profile.city || profile.region}</Pill>}
            </div>
            {hasLocation && (
              <div className="mt-1 text-[12px] tracking-tight text-black/50 dark:text-white/50">
                Подобрано по вашему адресу из профиля.
              </div>
            )}
            <div className="mt-3 space-y-3">
              {matchedInstitutions.map(ins => (
                <div key={ins.id} className={`flex items-start gap-3 rounded-2xl ${ins.matched ? "bg-[#E3E7FC]/40 px-3 py-2.5 dark:bg-[#0E1A3A]/40" : ""}`}>
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                    <Building2 size={15} />
                  </span>
                  <div className="min-w-0 flex-1 text-[13px] tracking-tight">
                    <div className="flex items-center gap-2">
                      <span className="text-black dark:text-white">{ins.name}</span>
                      {ins.matched && <span className="inline-flex items-center gap-1 rounded-full bg-[#0056FF] px-2 py-0.5 text-[10px] text-white"><MapPin size={9} /> рядом</span>}
                    </div>
                    <div className="text-black/55 dark:text-white/55">{ins.matchReason || ins.address}</div>
                    {ins.hours && <div className="mt-0.5 text-black/55 dark:text-white/55">{ins.hours}</div>}
                  </div>
                </div>
              ))}
              {matchedInstitutions.length === 0 && <div className="text-[13px] text-black/55 dark:text-white/55">Учреждения уточняются по месту обращения.</div>}
            </div>
          </Card>

          <Card className="p-5">
            <div className="tracking-tight text-black dark:text-white">Официальные источники</div>
            <div className="mt-3 space-y-3">
              {scenario.sources.length === 0 && (
                <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Источники не указаны.</div>
              )}
              {scenario.sources.map(s => (
                <div key={s.id} className="rounded-2xl bg-[#F6F7FB] px-3.5 py-3 dark:bg-white/[0.03]">
                  <div className="flex items-center justify-between">
                    <div className="tracking-tight text-black dark:text-white">{s.title}</div>
                    {s.checkedAt
                      ? <span className="text-[10px] tracking-tight text-emerald-600 dark:text-emerald-400">проверено {s.checkedAt}</span>
                      : <span className="text-[10px] tracking-tight text-amber-600 dark:text-amber-400">требует проверки</span>}
                  </div>
                  <div className="mt-0.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">{s.description}</div>
                  <div className="mt-1 inline-flex items-center gap-1 text-[12px] tracking-tight text-[#0056FF]">{s.url} <ArrowUpRight size={11} /></div>
                </div>
              ))}
            </div>
            <div className="mt-4"><SourcesDisclaimer /></div>
          </Card>

          {role === "guest" && (
            <Card className="p-4">
              <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">
                Создание ситуации, отметка задач и хранение документов доступны после входа.
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function categoryLabel(id: string) {
  return ({
    documents: "Документы", family: "Семья", work: "Работа", business: "ИП и бизнес",
    housing: "Жильё и ЖКХ", taxes: "Налоги", health: "Здоровье", auto: "Авто",
  } as Record<string,string>)[id] ?? id;
}

function taskKindLabel(k: string) {
  return ({
    form: "Заполнить", visit: "Визит в учреждение", payment: "Оплата",
    wait: "Ожидание", document: "Документ",
  } as Record<string,string>)[k] ?? k;
}

/* ---------------- MY SITUATION DETAIL (interactive) ---------------- */
export function MySituationDetail({ situationId, onBack }: { situationId: string; onBack: () => void }) {
  const { situations, scenarioById, toggleTask, taskIsBlocked, situationProgress, deleteSituation, setNote } = useStore();
  const situation = situations.find(s => s.id === situationId);
  const scenario = situation ? scenarioById(situation.scenarioId) : undefined;
  const [openNote, setOpenNote] = useState<string | null>(null);

  if (!situation || !scenario) {
    return (
      <div className="space-y-4">
        <button onClick={onBack} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55">
          <ChevronLeft size={14} /> Назад
        </button>
        <Card className="p-5">Ситуация не найдена.</Card>
      </div>
    );
  }

  const progress = situationProgress(situation);
  const totalTasks = scenario.stages.reduce((n, st) => n + st.tasks.length, 0);

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55">
        <ChevronLeft size={14} /> Мои ситуации
      </button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Pill tone="lavender">{categoryLabel(scenario.category)}</Pill>
          <h1 className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 30, lineHeight: 1.08 }}>{scenario.title}</h1>
          <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">Начато {situation.startedAt}</div>
        </div>
        <div className="flex items-center gap-2">
          <Pill tone={situation.status === "done" ? "ok" : situation.status === "in_progress" ? "royal" : "ghost"}>
            {situation.status === "done" ? "Завершено" : situation.status === "in_progress" ? "В процессе" : "Не начата"}
          </Pill>
          <button
            onClick={() => { if (confirm("Удалить ситуацию?")) { deleteSituation(situation.id); onBack(); } }}
            className="inline-flex h-10 items-center gap-1.5 rounded-xl border border-black/10 bg-white px-3 text-[13px] tracking-tight text-black/65 dark:border-white/10 dark:bg-white/[0.04] dark:text-white/65"
          >
            <Trash2 size={14} /> Удалить
          </button>
        </div>
      </div>

      <Card className="p-5">
        <div className="flex items-center justify-between text-[12px] tracking-tight text-black/55 dark:text-white/55">
          <span>Прогресс: {situation.completedTaskIds.length} из {totalTasks} задач</span>
          <span>{progress}%</span>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
          <motion.div initial={false} animate={{ width: `${progress}%` }} transition={{ duration: 0.6 }} className="h-full rounded-full" style={{ background: "linear-gradient(90deg,#0056FF,#2277FF)" }} />
        </div>
      </Card>

      <div className="space-y-5">
        {scenario.stages.map((stage, idx) => (
          <Card key={stage.id} className="p-5">
            <div className="flex items-center gap-3">
              <span className="grid h-7 w-7 place-items-center rounded-full bg-[#E3E7FC] text-[12px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{idx + 1}</span>
              <div className="tracking-tight text-black dark:text-white">{stage.title}</div>
            </div>
            <div className="mt-3 space-y-2.5">
              {stage.tasks.map(t => {
                const isDone = situation.completedTaskIds.includes(t.id);
                const blocked = taskIsBlocked(situation, t.id) && !isDone;
                const note = situation.notes[t.id] ?? "";
                return (
                  <div key={t.id} className={`rounded-2xl bg-[#F6F7FB] px-3.5 py-3 dark:bg-white/[0.03] ${blocked ? "opacity-70" : ""}`}>
                    <div className="flex items-start gap-3">
                      <button
                        disabled={blocked}
                        onClick={() => toggleTask(situation.id, t.id)}
                        className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md border transition-colors ${
                          isDone ? "border-[#0056FF] bg-[#0056FF] text-white"
                          : blocked ? "border-black/15 bg-white text-black/30 dark:border-white/15 dark:bg-white/[0.05]"
                          : "border-black/30 bg-white hover:border-[#0056FF] dark:border-white/30 dark:bg-white/[0.05]"
                        }`}
                      >
                        {isDone ? <Check size={14} strokeWidth={3} /> : blocked ? <Lock size={12} /> : null}
                      </button>
                      <div className="flex-1">
                        <div className={`tracking-tight ${isDone ? "text-black/50 line-through dark:text-white/50" : "text-black dark:text-white"}`}>{t.title}</div>
                        <div className="mt-0.5 flex items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                          <span>{taskKindLabel(t.kind)}</span>
                          {t.durationHint && <span>· {t.durationHint}</span>}
                          {blocked && <span className="text-amber-600 dark:text-amber-400">· разблокируется после предыдущих</span>}
                        </div>
                        <button
                          onClick={() => setOpenNote(openNote === t.id ? null : t.id)}
                          className="mt-2 inline-flex items-center gap-1 text-[12px] tracking-tight text-[#0056FF]"
                        >
                          <Edit3 size={12} /> {note ? "Заметка" : "Добавить заметку"}
                        </button>
                        {openNote === t.id && (
                          <textarea
                            value={note}
                            onChange={(e) => setNote(situation.id, t.id, e.target.value)}
                            placeholder="Личная заметка к задаче"
                            className="mt-2 h-20 w-full resize-none rounded-xl border border-black/10 bg-white p-2.5 text-[13px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/10 dark:bg-white/[0.04] dark:text-white"
                          />
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

/* ---------------- SETTINGS ---------------- */
export function SettingsPage({ themeMode, setThemeMode }: { themeMode: "light" | "dark" | "system"; setThemeMode: (m: "light" | "dark" | "system") => void }) {
  const { settings, updateSettings, setLang } = useStore();

  const Toggle = ({ on, onChange }: { on: boolean; onChange: () => void }) => (
    <button onClick={onChange} className={`relative h-7 w-12 rounded-full transition-colors ${on ? "bg-[#0056FF]" : "bg-black/10 dark:bg-white/15"}`}>
      <motion.span layout className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow ${on ? "left-[22px]" : "left-0.5"}`} />
    </button>
  );

  const Row = ({ label, sub, right }: { label: string; sub?: string; right: React.ReactNode }) => (
    <div className="flex items-center justify-between gap-4 py-3.5">
      <div>
        <div className="tracking-tight text-black dark:text-white">{label}</div>
        {sub && <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{sub}</div>}
      </div>
      {right}
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[13px] tracking-tight text-black/55 dark:text-white/55">Настройки</div>
        <h1 className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Параметры аккаунта</h1>
      </div>

      <Card className="p-5">
        <div className="flex items-center gap-2"><Sparkles size={15} className="text-[#0056FF]" /><div className="tracking-tight text-black dark:text-white">Интерфейс</div></div>
        <div className="py-3.5">
          <div className="tracking-tight text-black dark:text-white">Тема оформления</div>
          <div className="mt-2.5 flex flex-wrap gap-2">
            {[
              { id: "light" as const, n: "Светлая" },
              { id: "dark" as const, n: "Тёмная" },
              { id: "system" as const, n: "Системная" },
            ].map(t => (
              <button key={t.id} onClick={() => setThemeMode(t.id)}
                className={`rounded-full px-4 py-2 text-[13px] tracking-tight ${themeMode === t.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>
                {t.n}
              </button>
            ))}
          </div>
          <div className="mt-1.5 text-[12px] tracking-tight text-black/50 dark:text-white/55">Системная — подстраивается под тему вашего устройства.</div>
        </div>
        <div className="mt-2 divide-y divide-black/[0.05] dark:divide-white/[0.05]">
          <Row label="Большой шрифт" right={<Toggle on={settings.accessibility.largeFont} onChange={() => updateSettings({ accessibility: { ...settings.accessibility, largeFont: !settings.accessibility.largeFont } })} />} />
          <Row label="Высокий контраст" right={<Toggle on={settings.accessibility.highContrast} onChange={() => updateSettings({ accessibility: { ...settings.accessibility, highContrast: !settings.accessibility.highContrast } })} />} />
        </div>
      </Card>

      <Card className="p-5">
        <div className="flex items-center gap-2"><Globe size={15} className="text-[#0056FF]" /><div className="tracking-tight text-black dark:text-white">Язык интерфейса</div></div>
        <div className="mt-3 flex gap-2">
          {[
            { id: "ru" as Lang, n: "Русский" },
            { id: "be" as Lang, n: "Беларуская" },
            { id: "en" as Lang, n: "English" },
          ].map(l => (
            <button key={l.id} onClick={() => setLang(l.id)}
              className={`rounded-full px-4 py-2 text-[13px] tracking-tight ${settings.lang === l.id ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>
              {l.n}
            </button>
          ))}
        </div>
      </Card>

      <Card className="p-5">
        <div className="flex items-center gap-2"><BellRing size={15} className="text-[#0056FF]" /><div className="tracking-tight text-black dark:text-white">Уведомления</div></div>
        <div className="mt-2 divide-y divide-black/[0.05] dark:divide-white/[0.05]">
          <Row label="Сроки задач" right={<Toggle on={settings.notifications.deadlines} onChange={() => updateSettings({ notifications: { ...settings.notifications, deadlines: !settings.notifications.deadlines } })} />} />
          <Row label="Срок действия документов" right={<Toggle on={settings.notifications.documents} onChange={() => updateSettings({ notifications: { ...settings.notifications, documents: !settings.notifications.documents } })} />} />
          <Row label="Правовые обновления" right={<Toggle on={settings.notifications.legal} onChange={() => updateSettings({ notifications: { ...settings.notifications, legal: !settings.notifications.legal } })} />} />
          <Row label="Push-уведомления" right={<Toggle on={settings.notifications.push} onChange={() => updateSettings({ notifications: { ...settings.notifications, push: !settings.notifications.push } })} />} />
        </div>
      </Card>

      <Card className="p-5">
        <div className="flex items-center gap-2"><Shield size={15} className="text-[#0056FF]" /><div className="tracking-tight text-black dark:text-white">Приватность</div></div>
        <div className="mt-2 divide-y divide-black/[0.05] dark:divide-white/[0.05]">
          <Row label="Скрывать данные документов" sub="Номера маскируются по умолчанию"
            right={<Toggle on={settings.privacy.maskDocuments} onChange={() => updateSettings({ privacy: { ...settings.privacy, maskDocuments: !settings.privacy.maskDocuments } })} />} />
          <Row label="Быстрый вход (Face/Touch ID)" right={<Toggle on={settings.privacy.quickLogin} onChange={() => updateSettings({ privacy: { ...settings.privacy, quickLogin: !settings.privacy.quickLogin } })} />} />
        </div>
      </Card>
    </div>
  );
}

/* ---------------- LEARNING ---------------- */
function LearningQuiz() {
  const { applyQuizResult, role } = useStore();
  const quiz = LEARNING_QUIZ;
  const [step, setStep] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);

  const q = quiz.questions[step];

  const choose = (idx: number) => {
    if (picked !== null) return;
    setPicked(idx);
    const isRight = idx === q.answer;
    const nextCorrect = correct + (isRight ? 1 : 0);
    setCorrect(nextCorrect);
    setTimeout(() => {
      if (step + 1 < quiz.questions.length) {
        setStep(step + 1);
        setPicked(null);
      } else {
        setDone(true);
        applyQuizResult(nextCorrect, quiz.questions.length);
      }
    }, 650);
  };

  const restart = () => { setStep(0); setPicked(null); setCorrect(0); setDone(false); };

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"><Sparkles size={16} /></span>
        <div>
          <div className="tracking-tight text-black dark:text-white">Проверьте себя</div>
          <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Тема: {quiz.topic}</div>
        </div>
      </div>

      {done ? (
        <div className="mt-5">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>
            Результат: {correct} из {quiz.questions.length}
          </div>
          <div className="mt-1 text-[13px] tracking-tight text-black/60 dark:text-white/60">
            {correct === quiz.questions.length ? "Отлично! Тема усвоена." : correct >= 2 ? "Хорошо, но есть что повторить." : "Стоит перечитать материал."}
          </div>
          <GhostButton className="mt-4" onClick={restart}>Пройти ещё раз</GhostButton>
        </div>
      ) : (
        <div className="mt-5">
          <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">Вопрос {step + 1} из {quiz.questions.length}</div>
          <div className="mt-1.5 tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{q.q}</div>
          <div className="mt-4 space-y-2.5">
            {q.options.map((opt, idx) => {
              const isPicked = picked === idx;
              const isAnswer = idx === q.answer;
              const tone = picked === null ? "" : isAnswer ? "border-emerald-400 bg-emerald-50 dark:bg-emerald-500/10" : isPicked ? "border-red-400 bg-red-50 dark:bg-red-500/10" : "";
              return (
                <button key={idx} disabled={picked !== null || role === "guest"} onClick={() => choose(idx)}
                  className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left text-[14px] tracking-tight transition-colors ${tone || "border-black/[0.08] hover:bg-black/[0.02] dark:border-white/[0.08] dark:hover:bg-white/[0.04]"} text-black dark:text-white`}>
                  <span>{opt}</span>
                  {picked !== null && isAnswer && <Check size={16} className="text-emerald-500" />}
                  {picked !== null && isPicked && !isAnswer && <X size={16} className="text-red-500" />}
                </button>
              );
            })}
          </div>
          {role === "guest" && <div className="mt-3 text-[12px] tracking-tight text-black/45 dark:text-white/45">Войдите, чтобы сохранять прогресс обучения.</div>}
        </div>
      )}
    </Card>
  );
}

export function LearningPage() {
  const { profile } = useStore();
  return (
    <div className="space-y-6">
      <div>
        <div className="text-[13px] tracking-tight text-black/55 dark:text-white/55">Дополнительный режим</div>
        <h1 className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Обучение</h1>
        <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">
          Короткие подсказки, как пользоваться сервисом, и важные правовые основы. Прогресс сохраняется автоматически.
        </p>
      </div>

      <Card className="p-5">
        <div className="flex items-center justify-between text-[12px] tracking-tight text-black/55 dark:text-white/55">
          <span>Прогресс обучения</span><span>{profile?.learningProgress || 0}%</span>
        </div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
          <motion.div initial={false} animate={{ width: `${profile?.learningProgress || 0}%` }} transition={{ duration: 0.6 }} className="h-full rounded-full" style={{ background: "linear-gradient(90deg,#0056FF,#2277FF)" }} />
        </div>
      </Card>

      <Card className="p-5">
        <div className="tracking-tight text-black dark:text-white">Прогресс по темам</div>
        <div className="mt-4 space-y-3">
          {LEARNING_CATEGORIES.map((c) => (
            <div key={c.id}>
              <div className="flex items-center justify-between text-[12px] tracking-tight text-black/60 dark:text-white/60">
                <span>{c.name}</span><span>{c.progress}%</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
                <div className="h-full rounded-full bg-[#0056FF]" style={{ width: `${c.progress}%` }} />
              </div>
            </div>
          ))}
        </div>
      </Card>

      <LearningQuiz />

      {profile?.achievements?.length > 0 && (
        <Card className="p-5">
          <div className="tracking-tight text-black dark:text-white">Достижения</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {profile?.achievements?.map(a => (
              <span key={a.id} className="inline-flex items-center gap-2 rounded-full bg-[#E3E7FC] px-3.5 py-1.5 text-[12px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <Award size={12} /> {a.title}
              </span>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

/* ---------------- AI ASSISTANT ---------------- */
type AssistantMsg = {
  role: "user" | "assistant";
  text: string;
  section?: { id: string; title: string; description: string; route: string };
  warning?: boolean;
};

export function AssistantPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { role } = useStore();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<AssistantMsg[]>([
    { role: "assistant", text: "Здравствуйте! Напишите, что хотите найти или сделать — подскажу подходящий раздел." },
  ]);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);

  if (!open) return null;

  const send = async () => {
    const text = value.trim();
    if (!text || busy) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setValue("");
    setBusy(true);
    try {
      const res = await apiClient.askAssistant<{
        response_text: string;
        section: { id: string; title: string; description: string; route: string };
        requires_auth_warning: boolean;
      }>({ message: text, role, is_guest: role === "guest" });
      setMessages((m) => [...m, { role: "assistant", text: res.response_text, section: res.section, warning: res.requires_auth_warning }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Не удалось связаться с помощником. Попробуйте позже или воспользуйтесь поиском и каталогом." }]);
    } finally {
      setBusy(false);
    }
  };

  const goTo = (route: string) => { onClose(); navigate(route); };

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-end p-0 sm:items-end sm:justify-end sm:p-6" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30 backdrop-blur-[2px]" />
      <div onClick={(e) => e.stopPropagation()}
        className="relative flex h-[80vh] w-full flex-col overflow-hidden rounded-t-3xl border border-black/[0.08] bg-white shadow-[0_40px_120px_-30px_rgba(15,23,42,0.5)] dark:border-white/[0.08] dark:bg-[#0B0D13] sm:h-[560px] sm:w-[400px] sm:rounded-3xl">
        <div className="flex items-center justify-between border-b border-black/[0.06] px-5 py-4 dark:border-white/[0.06]">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#0056FF] text-white"><Sparkles size={16} /></span>
            <div>
              <div className="tracking-tight text-black dark:text-white">Помощник</div>
              <div className="text-[11px] tracking-tight text-black/45 dark:text-white/45">Ориентир по разделам</div>
            </div>
          </div>
          <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg text-black/40 hover:bg-black/[0.04] dark:text-white/40 dark:hover:bg-white/[0.06]"><X size={16} /></button>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4 [&::-webkit-scrollbar]:hidden">
          {messages.map((m, i) => (
            <div key={i}>
              <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[14px] tracking-tight ${m.role === "user"
                ? "ml-auto bg-[#0056FF] text-white"
                : "bg-[#F6F7FB] text-black dark:bg-white/[0.05] dark:text-white"}`}>
                {m.text}
              </div>
              {m.section && (
                <button onClick={() => goTo(m.section!.route)}
                  className="mt-2 flex w-full items-center gap-3 rounded-2xl border border-black/[0.08] bg-white px-3.5 py-3 text-left transition-colors hover:bg-black/[0.02] dark:border-white/[0.08] dark:bg-white/[0.03] dark:hover:bg-white/[0.06]">
                  <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"><ArrowUpRight size={16} /></span>
                  <span className="min-w-0 flex-1">
                    <span className="block tracking-tight text-black dark:text-white">{m.section.title}</span>
                    <span className="block truncate text-[12px] tracking-tight text-black/55 dark:text-white/55">{m.warning ? "Нужен вход или регистрация" : m.section.description}</span>
                  </span>
                  <span className="text-[12px] font-medium tracking-tight text-[#0056FF]">Перейти →</span>
                </button>
              )}
            </div>
          ))}
          {busy && <div className="text-[12px] tracking-tight text-black/40 dark:text-white/40">Помощник печатает…</div>}
        </div>

        <div className="flex items-end gap-2 border-t border-black/[0.06] p-3 dark:border-white/[0.06]">
          <textarea value={value} onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            rows={1} placeholder="Например: хочу добавить паспорт"
            className="max-h-24 flex-1 resize-none rounded-2xl bg-[#F6F7FB] px-4 py-2.5 text-[14px] tracking-tight text-black outline-none dark:bg-white/[0.05] dark:text-white" />
          <button onClick={send} disabled={busy || !value.trim()}
            className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-[#0056FF] text-white disabled:opacity-40"><ArrowUpRight size={18} /></button>
        </div>
      </div>
    </div>
  );
}

/* ---------------- PROFILE EDIT ---------------- */
const EMPLOYMENT_OPTIONS = [
  { id: "employee", n: "Наёмный работник" },
  { id: "ip", n: "ИП" },
  { id: "student", n: "Студент" },
  { id: "pensioner", n: "Пенсионер" },
  { id: "unemployed", n: "Безработный" },
];
const INTEREST_OPTIONS = ["Документы", "Семья", "ЖКХ", "Налоги", "Здоровье", "Работа", "Авто", "Бизнес/ИП"];

function ProfileField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block">
      <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)}
        className="mt-1 h-11 w-full rounded-2xl border border-black/[0.08] bg-[#F6F7FB] px-3.5 text-[14px] tracking-tight text-black outline-none focus:border-[#0056FF] dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-white" />
    </label>
  );
}

function ProfileFlag({ label, on, onClick }: { label: string; on: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} className={`flex items-center justify-between rounded-2xl border px-3.5 py-2.5 text-left text-[13px] tracking-tight transition-colors ${on ? "border-[#0056FF] bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "border-black/[0.08] text-black/70 dark:border-white/[0.08] dark:text-white/70"}`}>
      {label}{on && <Check size={15} />}
    </button>
  );
}

export function ProfileEditModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { profile, updateProfile } = useStore();
  const [form, setForm] = useState(profile);
  useEffect(() => { if (open) setForm(profile); }, [open, profile]);

  if (!open) return null;

  const set = (patch: Partial<typeof form>) => setForm(f => ({ ...f, ...patch }));
  const setFlag = (key: keyof typeof form.flags) => setForm(f => ({ ...f, flags: { ...f.flags, [key]: !f.flags[key] } }));
  const toggleInterest = (t: string) => setForm(f => ({ ...f, interests: f.interests.includes(t) ? f.interests.filter(x => x !== t) : [...f.interests, t] }));
  const save = () => {
    updateProfile({
      name: form.name, region: form.region, city: form.city, district: form.district,
      address: form.address, employment: form.employment, flags: form.flags, interests: form.interests,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} className="flex max-h-[88vh] w-full max-w-[520px] flex-col overflow-hidden rounded-3xl bg-white shadow-2xl dark:bg-[#0F1117]">
        <div className="flex items-center justify-between border-b border-black/[0.06] px-5 py-4 dark:border-white/[0.06]">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 17 }}>Редактировать профиль</div>
          <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg text-black/40 hover:bg-black/[0.04] dark:text-white/40 dark:hover:bg-white/[0.06]"><X size={16} /></button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-5 [&::-webkit-scrollbar]:hidden">
          <ProfileField label="Имя и фамилия" value={form.name} onChange={(v) => set({ name: v })} />
          <div className="grid grid-cols-2 gap-3">
            <ProfileField label="Область / регион" value={form.region} onChange={(v) => set({ region: v })} />
            <ProfileField label="Город" value={form.city} onChange={(v) => set({ city: v })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <ProfileField label="Район" value={form.district} onChange={(v) => set({ district: v })} />
            <ProfileField label="Адрес" value={form.address ?? ""} onChange={(v) => set({ address: v })} />
          </div>

          <div>
            <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Статус занятости</span>
            <div className="mt-1.5 flex flex-wrap gap-2">
              {EMPLOYMENT_OPTIONS.map(o => (
                <button key={o.id} onClick={() => set({ employment: o.id })} className={`rounded-full px-3.5 py-1.5 text-[13px] tracking-tight ${form.employment === o.id ? "bg-[#0056FF] text-white" : "bg-[#F6F7FB] text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{o.n}</button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <ProfileFlag label="Есть дети" on={form.flags.hasChildren} onClick={() => setFlag("hasChildren")} />
            <ProfileFlag label="Есть авто" on={form.flags.hasCar} onClick={() => setFlag("hasCar")} />
            <ProfileFlag label="Собственник жилья" on={form.flags.homeowner} onClick={() => setFlag("homeowner")} />
            <ProfileFlag label="Арендатор" on={form.flags.tenant} onClick={() => setFlag("tenant")} />
          </div>

          <div>
            <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Интересы</span>
            <div className="mt-1.5 flex flex-wrap gap-2">
              {INTEREST_OPTIONS.map(t => {
                const on = form.interests.includes(t);
                return <button key={t} onClick={() => toggleInterest(t)} className={`rounded-full px-3 py-1.5 text-[13px] tracking-tight ${on ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "bg-[#F6F7FB] text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{t}</button>;
              })}
            </div>
          </div>
        </div>

        <div className="flex gap-2 border-t border-black/[0.06] p-4 dark:border-white/[0.06]">
          <GhostButton className="flex-1" onClick={onClose}>Отмена</GhostButton>
          <PrimaryButton className="flex-1" onClick={save}>Сохранить</PrimaryButton>
        </div>
      </div>
    </div>
  );
}

/* ---------------- GUEST GUARD ---------------- */
export function GuestGuardModal({
  open, onClose, onSignIn, onRegister,
}: {
  open: boolean;
  onClose: () => void;
  onSignIn: () => void;
  onRegister: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/40 p-4 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, y: 16, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.2 }}
        className="relative w-full max-w-[420px] rounded-3xl bg-white p-6 shadow-2xl dark:bg-[#0F1117]"
      >
        <button onClick={onClose} className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-black/[0.05] text-black/55 dark:bg-white/[0.06] dark:text-white/55">
          <X size={15} />
        </button>
        <div className="grid h-12 w-12 place-items-center rounded-2xl" style={{ background: "linear-gradient(135deg,#0056FF,#2277FF)" }}>
          <Shield size={22} className="text-white" />
        </div>
        <h2 className="mt-4 tracking-tight text-black dark:text-white" style={{ fontSize: 20 }}>Войдите или зарегистрируйтесь</h2>
        <p className="mt-2 tracking-tight text-black/60 dark:text-white/60">
          Это действие доступно после входа: создание ситуаций, отметка задач, хранение документов.
        </p>
        <div className="mt-5 flex gap-2">
          <PrimaryButton onClick={onSignIn} className="h-11 flex-1">Войти</PrimaryButton>
          <GhostButton onClick={onRegister} className="h-11 flex-1">Зарегистрироваться</GhostButton>
        </div>
        <button onClick={onClose} className="mt-3 w-full text-[12px] tracking-tight text-black/45 dark:text-white/45">Продолжить просмотр</button>
      </motion.div>
    </div>
  );
}

/* ---------------- SEARCH OVERLAY ---------------- */
type SearchResult =
  | { kind: "scenario"; id: string; title: string; sub: string }
  | { kind: "document"; id: string; title: string; sub: string }
  | { kind: "legal"; id: string; title: string; sub: string }
  | { kind: "institution"; id: string; title: string; sub: string };

export function SearchOverlay({
  open, onClose, onOpenScenario, onOpenLegal, onOpenDocuments,
}: {
  open: boolean;
  onClose: () => void;
  onOpenScenario: (id: string) => void;
  onOpenLegal: () => void;
  onOpenDocuments: () => void;
}) {
  const { scenarios, problems, documents, publicDocuments, authorities, legal } = useStore();
  const [q, setQ] = useState("");
  const [recent, setRecent] = useState<string[]>([]);
  useEffect(() => { if (open) setRecent(getRecentSearches()); }, [open]);

  const pool = useMemo<SuggestionItem[]>(() => {
    const p: SuggestionItem[] = [];
    problems.forEach(x => p.push({ label: x.title, kind: "проблема" }));
    scenarios.forEach(x => p.push({ label: x.title, kind: "сценарий" }));
    publicDocuments.forEach(x => p.push({ label: x.name, kind: "документ" }));
    documents.forEach(x => p.push({ label: x.title, kind: "документ" }));
    authorities.forEach(x => p.push({ label: x.name, kind: "учреждение" }));
    legal.forEach(x => p.push({ label: x.title, kind: "закон-апдейт" }));
    return p;
  }, [problems, scenarios, publicDocuments, documents, authorities, legal]);

  const typed = useMemo(() => buildSuggestions(q, pool, 6), [q, pool]);
  const commit = (value: string) => { setQ(value); addRecentSearch(value); setRecent(getRecentSearches()); };

  const results = useMemo<SearchResult[]>(() => {
    const query = q.trim().toLowerCase();
    if (!query) return [];
    const r: SearchResult[] = [];
    scenarios.forEach(s => {
      if ((s.title + s.shortDescription).toLowerCase().includes(query)) {
        r.push({ kind: "scenario", id: s.id, title: s.title, sub: s.shortDescription });
      }
      s.institutions.forEach(ins => {
        if (ins.name.toLowerCase().includes(query)) {
          r.push({ kind: "institution", id: ins.id, title: ins.name, sub: ins.address });
        }
      });
    });
    documents.forEach(d => {
      if (d.title.toLowerCase().includes(query)) {
        r.push({ kind: "document", id: d.id, title: d.title, sub: DOC_TYPE_LABEL[d.type] });
      }
    });
    publicDocuments.forEach(d => {
      if ((d.name + (d.note ?? "")).toLowerCase().includes(query)) {
        r.push({ kind: "document", id: d.id, title: d.name, sub: d.required ? "Обязательный документ" : "Документ по ситуации" });
      }
    });
    authorities.forEach(ins => {
      if ((ins.name + ins.address + (ins.phone ?? "")).toLowerCase().includes(query)) {
        r.push({ kind: "institution", id: ins.id, title: ins.name, sub: ins.address || "Учреждение из справочника" });
      }
    });
    legal.forEach(l => {
      if ((l.title + l.summary).toLowerCase().includes(query)) {
        r.push({ kind: "legal", id: l.id, title: l.title, sub: l.summary });
      }
    });
    return r.slice(0, 12);
  }, [q, scenarios, documents, publicDocuments, authorities, legal]);

  if (!open) return null;

  const pick = (r: SearchResult) => {
    if (q.trim()) addRecentSearch(q.trim());
    if (r.kind === "scenario") onOpenScenario(r.id);
    else if (r.kind === "legal") onOpenLegal();
    else if (r.kind === "document") onOpenDocuments();
    else if (r.kind === "institution") {
      const sc = scenarios.find(s => s.institutions.some(i => i.id === r.id));
      if (sc) onOpenScenario(sc.id);
    }
    onClose();
  };

  const kindLabel: Record<SearchResult["kind"], string> = {
    scenario: "Сценарий", document: "Документ", legal: "Правовое обновление", institution: "Учреждение",
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/40 p-4 backdrop-blur-sm" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }}
        onClick={(e) => e.stopPropagation()}
        className="mx-auto mt-[10vh] w-full max-w-[640px] overflow-hidden rounded-3xl bg-white shadow-2xl dark:bg-[#0F1117]"
      >
        <div className="flex items-center gap-3 border-b border-black/[0.06] px-5 py-4 dark:border-white/[0.06]">
          <Search size={18} className="text-black/40 dark:text-white/40" />
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Поиск по сценариям, документам, учреждениям"
            className="flex-1 bg-transparent tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40"
          />
          <button onClick={onClose} className="rounded-md bg-black/[0.05] px-1.5 py-0.5 text-[10px] tracking-tight text-black/55 dark:bg-white/[0.08] dark:text-white/60">ESC</button>
        </div>

        <div className="max-h-[60vh] overflow-y-auto p-3">
          {!q.trim() && (
            <div className="px-2 py-1">
              {recent.length > 0 && (
                <div className="mb-3">
                  <div className="px-2 pb-2 text-[11px] uppercase tracking-[0.14em] text-black/40 dark:text-white/40">Недавние запросы</div>
                  <div className="space-y-0.5">
                    {recent.map(s => (
                      <button key={s} onClick={() => setQ(s)} className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-[14px] tracking-tight text-black/80 hover:bg-[#F6F7FB] dark:text-white/80 dark:hover:bg-white/[0.04]">
                        <Clock size={14} className="text-black/35 dark:text-white/35" /> {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div className="px-2 pb-2 text-[11px] uppercase tracking-[0.14em] text-black/40 dark:text-white/40">Популярное</div>
              <div className="flex flex-wrap gap-2 px-1">
                {POPULAR_QUERIES.map(s => (
                  <button key={s} onClick={() => setQ(s)} className="rounded-full bg-[#F6F7FB] px-3.5 py-1.5 text-[13px] tracking-tight text-black/70 dark:bg-white/[0.06] dark:text-white/70">{s}</button>
                ))}
              </div>
            </div>
          )}

          {q.trim() && typed.length > 0 && (
            <div className="mb-1 border-b border-black/[0.05] pb-2 dark:border-white/[0.05]">
              {typed.map(s => (
                <button key={s.label} onClick={() => commit(s.label)} className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left hover:bg-[#F6F7FB] dark:hover:bg-white/[0.04]">
                  <Search size={14} className="shrink-0 text-black/35 dark:text-white/35" />
                  <span className="flex-1 truncate text-[14px] tracking-tight text-black dark:text-white">{s.label}</span>
                  <span className="text-[11px] tracking-tight text-black/35 dark:text-white/35">{s.kind}</span>
                </button>
              ))}
            </div>
          )}
          {q.trim() && results.length === 0 && (
            <div className="px-4 py-8 text-center text-[13px] tracking-tight text-black/55 dark:text-white/55">Ничего не нашли</div>
          )}
          {results.map(r => (
            <button key={r.kind + r.id} onClick={() => pick(r)} className="flex w-full items-start gap-3 rounded-2xl px-3 py-3 text-left hover:bg-[#F6F7FB] dark:hover:bg-white/[0.04]">
              <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                {r.kind === "scenario" && <FileText size={14} />}
                {r.kind === "document" && <Shield size={14} />}
                {r.kind === "legal" && <AlertCircle size={14} />}
                {r.kind === "institution" && <Building2 size={14} />}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-[10px] uppercase tracking-[0.14em] text-black/40 dark:text-white/40">{kindLabel[r.kind]}</div>
                <div className="truncate tracking-tight text-black dark:text-white">{r.title}</div>
                <div className="truncate text-[12px] tracking-tight text-black/55 dark:text-white/55">{r.sub}</div>
              </div>
            </button>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

/* ---------------- DOCUMENT EDIT MODAL ---------------- */
export function DocumentEditModal({
  open, onClose, editingId,
}: {
  open: boolean; onClose: () => void; editingId: string | null;
}) {
  const { documents, addDocument, updateDocument, deleteDocument } = useStore();
  const existing = editingId ? documents.find(d => d.id === editingId) : undefined;
  const [type, setType] = useState<UserDocumentType>(existing?.type ?? "passport");
  const [title, setTitle] = useState(existing?.title ?? "");
  const [number, setNumber] = useState(existing?.number ?? "");
  const [expiresAt, setExpiresAt] = useState(existing?.expiresAt ?? "");

  useEffect(() => {
    if (!open) return;
    setType(existing?.type ?? "passport");
    setTitle(existing?.title ?? "");
    setNumber(existing?.number ?? "");
    setExpiresAt(existing?.expiresAt ?? "");
  }, [existing?.expiresAt, existing?.number, existing?.title, existing?.type, open]);

  if (!open) return null;

  const save = () => {
    if (!title.trim()) return;
    if (existing) {
      updateDocument(existing.id, { type, title, number, expiresAt });
    } else {
      addDocument({ type, title, number, expiresAt, status: "active" });
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/40 p-4 backdrop-blur-sm" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-[480px] rounded-3xl bg-white p-6 shadow-2xl dark:bg-[#0F1117]"
      >
        <div className="flex items-center justify-between">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>{existing ? "Изменить документ" : "Новый документ"}</div>
          <button onClick={onClose} className="grid h-9 w-9 place-items-center rounded-full bg-black/[0.05] text-black/55 dark:bg-white/[0.06] dark:text-white/55"><X size={15} /></button>
        </div>

        <div className="mt-5 space-y-3">
          <Field label="Тип документа">
            <select
              value={type} onChange={(e) => setType(e.target.value as UserDocumentType)}
              className="h-11 w-full rounded-xl border border-black/10 bg-white px-3 tracking-tight outline-none focus:border-[#0056FF] dark:border-white/10 dark:bg-white/[0.04] dark:text-white"
            >
              {(Object.keys(DOC_TYPE_LABEL) as UserDocumentType[]).map(t => (
                <option key={t} value={t}>{DOC_TYPE_LABEL[t]}</option>
              ))}
            </select>
          </Field>
          <Field label="Название">
            <Input value={title} onChange={setTitle} placeholder="Например: Паспорт гражданина РБ" />
          </Field>
          <Field label="Номер документа">
            <Input value={number} onChange={setNumber} placeholder="Например: MP1234567" />
          </Field>
          <Field label="Действует до" sub="Опционально">
            <Input value={expiresAt} onChange={setExpiresAt} placeholder="ГГГГ-ММ-ДД" />
          </Field>

          <div className="rounded-xl bg-[#F6F7FB] p-3 text-[12px] tracking-tight text-black/55 dark:bg-white/[0.04] dark:text-white/55">
            <div className="flex items-center gap-2"><EyeOff size={12} /> Хранится локально, доступ только у вас.</div>
          </div>

          <button className="flex w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-black/15 py-3 text-[13px] tracking-tight text-black/55 dark:border-white/15 dark:text-white/55">
            <Plus size={14} /> Загрузить скан документа
          </button>
        </div>

        <div className="mt-5 flex items-center justify-between gap-2">
          {existing ? (
            <button
              onClick={() => { deleteDocument(existing.id); onClose(); }}
              className="inline-flex h-11 items-center gap-1.5 rounded-xl px-3 text-[13px] tracking-tight text-red-600 dark:text-red-400"
            >
              <Trash2 size={14} /> Удалить
            </button>
          ) : <span />}
          <div className="flex gap-2">
            <GhostButton onClick={onClose} className="h-11">Отмена</GhostButton>
            <PrimaryButton onClick={save} className="h-11 px-5">Сохранить</PrimaryButton>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function Field({ label, sub, children }: { label: string; sub?: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{label}</span>
        {sub && <span className="text-[11px] tracking-tight text-black/40 dark:text-white/40">{sub}</span>}
      </div>
      {children}
    </div>
  );
}
function Input({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      className="h-11 w-full rounded-xl border border-black/10 bg-white px-3 tracking-tight outline-none focus:border-[#0056FF] dark:border-white/10 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/40" />
  );
}

/* ---------------- helpers for usage in App ---------------- */
export function formatDocumentNumber(num: string, masked: boolean) {
  return maskDocumentNumber(num, !masked);
}

/* ---------------- Reader-facing editorial content ---------------- */
function articleAuthorLabel(a: Article) {
  const m = a.author;
  if (m.proposedBy) {
    const who = m.anonymous ? "Аноним" : m.proposedBy;
    return m.name && m.name !== m.proposedBy ? `Предложено: ${who} · при поддержке ${m.name}` : `Предложено: ${who}`;
  }
  return `Автор: ${m.name || "Редакция"}`;
}
function articleToDraft(a: Article): Partial<ContentDraft> {
  return {
    kind: a.kind, title: a.title, summary: a.summary, bodyHtml: a.bodyHtml, cover: a.cover,
    video: a.video, gallery: a.gallery, tags: a.tags, category: a.category,
    specialization: a.specialization, audience: a.audience, source: a.source,
    sourceUrl: a.sourceUrl, date: a.date, author: a.author.name,
  };
}
const ARTICLE_KIND_LABEL: Record<string, string> = { news: "Новость", scenario: "Ситуация", problem: "Проблема" };

function ArticleReaderModal({ article, onClose, onEdit }: { article: Article; onClose: () => void; onEdit?: (a: Article) => void }) {
  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/40 p-0 backdrop-blur-sm sm:p-4" onClick={onClose}>
      <div className="h-[100dvh] w-full overflow-y-auto bg-white dark:bg-[#0B0D13] sm:h-auto sm:max-h-[90vh] sm:max-w-[760px] sm:rounded-2xl [&::-webkit-scrollbar]:hidden" onClick={(e) => e.stopPropagation()}>
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-black/[0.06] bg-white/80 px-4 py-2.5 backdrop-blur dark:border-white/[0.06] dark:bg-[#0B0D13]/80">
          <span className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{ARTICLE_KIND_LABEL[article.kind]}</span>
          <div className="flex items-center gap-1.5">
            {onEdit && <button onClick={() => onEdit(article)} className="inline-flex items-center gap-1.5 rounded-lg border border-black/10 px-2.5 py-1.5 text-[12px] tracking-tight text-[#0056FF] hover:bg-[#0056FF]/[0.06] dark:border-white/12 dark:text-[#7FA8FF]"><Edit3 size={13} /> Изменить</button>}
            <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg text-black/55 hover:bg-black/[0.05] dark:text-white/55 dark:hover:bg-white/[0.07]"><X size={16} /></button>
          </div>
        </div>
        <article className="px-5 py-6 sm:px-8">
          {article.cover && <img src={article.cover} alt="" className="mb-5 aspect-[16/9] w-full rounded-2xl object-cover" />}
          <div className="text-[12px] uppercase tracking-[0.12em] text-[#0056FF]">{article.category}</div>
          <h1 className="mt-2 text-[26px] font-medium leading-tight tracking-tight text-black dark:text-white sm:text-[30px]">{article.title}</h1>
          <div className="mt-2 text-[13px] tracking-tight text-black/45 dark:text-white/45">{articleAuthorLabel(article)} · {article.date}</div>
          {article.summary && <p className="mt-4 text-[15px] leading-relaxed tracking-tight text-black/70 dark:text-white/70">{article.summary}</p>}
          <div className="mt-4 text-[15px] leading-relaxed tracking-tight text-black/85 [&_a]:text-[#0056FF] [&_a]:underline dark:text-white/85" dangerouslySetInnerHTML={{ __html: article.bodyHtml || "" }} />
          {article.tags.length > 0 && (
            <div className="mt-5 flex flex-wrap gap-1.5">
              {article.tags.map((t) => <span key={t} className="rounded-full bg-black/[0.05] px-2.5 py-1 text-[12px] tracking-tight text-black/55 dark:bg-white/[0.06] dark:text-white/55">#{t}</span>)}
            </div>
          )}
          {article.sourceUrl && <a href={article.sourceUrl} target="_blank" rel="noreferrer" className="mt-5 inline-flex items-center gap-1.5 text-[13px] tracking-tight text-[#0056FF]"><Globe size={13} /> {article.source || "Источник"}</a>}
        </article>
      </div>
    </div>
  );
}

function ArticleEditModal({ article, onClose }: { article: Article; onClose: () => void }) {
  const { updateArticle, profile } = useStore();
  const submit = (draft: ContentDraft, action: "publish" | "draft" | "submit") => {
    updateArticle(article.id, {
      kind: draft.kind, title: draft.title.trim(), summary: draft.summary, bodyHtml: draft.bodyHtml,
      cover: draft.cover, video: draft.video, gallery: draft.gallery, tags: draft.tags,
      category: draft.category, specialization: draft.specialization, audience: draft.audience,
      source: draft.source, sourceUrl: draft.sourceUrl, date: draft.date,
      status: action === "draft" ? "draft" : "published",
    });
    onClose();
  };
  return (
    <div className="fixed inset-0 z-[110] grid place-items-center bg-black/40 p-0 backdrop-blur-sm sm:p-4">
      <div className="h-[100dvh] w-full overflow-hidden bg-white shadow-2xl dark:bg-[#0B0D13] sm:h-[88vh] sm:max-w-[1000px] sm:rounded-2xl">
        <ContentEditor kind={article.kind} mode="edit" initial={articleToDraft(article)} authorName={profile.name} onClose={onClose} onSubmit={submit} />
      </div>
    </div>
  );
}

export function EditorialFeed({ kind, title = "Материалы редакции" }: { kind?: ArticleKind; title?: string }) {
  const { articles, role } = useStore();
  const [reader, setReader] = useState<Article | null>(null);
  const [editArt, setEditArt] = useState<Article | null>(null);
  const list = articles.filter((a) => a.status === "published" && (!kind || a.kind === kind));
  if (list.length === 0) return null;
  const isStaff = role === "editor" || role === "admin";

  return (
    <div className="mb-8">
      <div className="mb-3 flex items-center gap-2">
        <Sparkles size={16} className="text-[#0056FF]" />
        <span className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{title}</span>
        <span className="rounded-full bg-[#E3E7FC] px-2 py-0.5 text-[11px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{list.length}</span>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {list.map((a) => (
          <button key={a.id} onClick={() => setReader(a)} className="text-left">
            <Card interactive className="flex h-full flex-col overflow-hidden p-0">
              {a.cover
                ? <img src={a.cover} alt="" className="aspect-[16/9] w-full object-cover" />
                : <div className="aspect-[16/9] w-full bg-gradient-to-br from-[#0056FF] to-[#2277FF]" />}
              <div className="flex flex-1 flex-col p-4">
                <div className="text-[11px] uppercase tracking-[0.1em] text-[#0056FF]">{a.category}</div>
                <div className="mt-1.5 line-clamp-2 tracking-tight text-black dark:text-white" style={{ fontSize: 15, lineHeight: 1.25 }}>{a.title}</div>
                {a.summary && <div className="mt-1 line-clamp-2 text-[13px] tracking-tight text-black/55 dark:text-white/55">{a.summary}</div>}
                <div className="mt-auto pt-3 text-[12px] tracking-tight text-black/45 dark:text-white/45">{articleAuthorLabel(a)} · {a.date}</div>
              </div>
            </Card>
          </button>
        ))}
      </div>
      {reader && <ArticleReaderModal article={reader} onClose={() => setReader(null)} onEdit={isStaff ? (a) => { setReader(null); setEditArt(a); } : undefined} />}
      {editArt && <ArticleEditModal article={editArt} onClose={() => setEditArt(null)} />}
    </div>
  );
}

/* ---------------- UGC: предложить контент ---------------- */
export function ProposeButton({ kind, label, className = "" }: { kind: ContentKind; label?: string; className?: string }) {
  const { role } = useStore();
  const [open, setOpen] = useState(false);
  if (role === "guest") return null; // только вошедшие пользователи предлагают контент
  const text = label ?? (kind === "news" ? "Предложить новость" : kind === "problem" ? "Предложить проблему" : "Предложить ситуацию");
  return (
    <>
      <button onClick={() => setOpen(true)} className={`inline-flex items-center gap-1.5 rounded-xl border border-[#0056FF]/25 bg-[#0056FF]/[0.06] px-3 py-2 text-[13px] tracking-tight text-[#0056FF] transition-colors hover:bg-[#0056FF]/[0.12] active:translate-y-[1px] dark:text-[#7FA8FF] ${className}`}>
        <Plus size={15} /> {text}
      </button>
      <ProposeContentModal open={open} kind={kind} onClose={() => setOpen(false)} />
    </>
  );
}

export function ProposeContentModal({ open, kind = "scenario", initial, editId, onClose }: { open: boolean; kind?: ContentKind; initial?: Partial<ContentDraft>; editId?: string; onClose: () => void }) {
  const { addArticle, updateArticle, currentUser, profile, isSubmitterBlocked } = useStore();
  if (!open) return null;
  const blocked = isSubmitterBlocked(currentUser.id);

  const submit = (draft: ContentDraft, action: "publish" | "draft" | "submit") => {
    const fields = {
      kind: draft.kind, title: draft.title.trim(), summary: draft.summary, bodyHtml: draft.bodyHtml,
      cover: draft.cover, video: draft.video, gallery: draft.gallery, tags: draft.tags,
      category: draft.category, specialization: draft.specialization, audience: draft.audience,
      source: draft.source, sourceUrl: draft.sourceUrl, date: draft.date,
      status: (action === "draft" ? "draft" : "review") as Article["status"],
    };
    if (editId) {
      updateArticle(editId, { ...fields, author: { name: "", role: "citizen", proposedBy: profile.name || "Пользователь", proposerId: currentUser.id, anonymous: draft.anonymous } });
    } else {
      addArticle({ ...fields, author: { name: "", role: "citizen", proposedBy: profile.name || "Пользователь", proposerId: currentUser.id, anonymous: draft.anonymous } });
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/40 p-0 backdrop-blur-sm sm:p-4">
      {blocked ? (
        <Card className="max-w-[420px] p-6 text-center">
          <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-red-50 text-red-500 dark:bg-red-500/15"><Lock size={20} /></div>
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>Отправка ограничена</div>
          <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">Администрация ограничила вам предложение материалов. Обратитесь в поддержку, если это ошибка.</div>
          <button onClick={onClose} className="mx-auto mt-4 inline-flex h-9 items-center rounded-xl border border-black/10 px-4 text-[13px] tracking-tight text-black/70 dark:border-white/12 dark:text-white/70">Закрыть</button>
        </Card>
      ) : (
        <div className="h-[100dvh] w-full overflow-hidden bg-white shadow-2xl dark:bg-[#0B0D13] sm:h-[88vh] sm:max-w-[1000px] sm:rounded-2xl">
          <ContentEditor kind={kind} propose initial={initial} authorName={profile.name} onClose={onClose} onSubmit={submit} />
        </div>
      )}
    </div>
  );
}

// «Мои предложения» — citizen sees own submissions + can resume drafts.
export function MyContributions() {
  const { articles, currentUser } = useStore();
  const [resume, setResume] = useState<Article | null>(null);
  const mine = articles.filter((a) => a.author.proposerId === currentUser.id);
  if (currentUser.role === "guest" || mine.length === 0) return null;

  const kindLabel = (k: string) => (k === "news" ? "Новость" : k === "problem" ? "Проблема" : "Ситуация");
  const statusMeta = (s: string): { l: string; tone: "ok" | "lavender" | "warn" | "ghost" } =>
    s === "published" ? { l: "Опубликовано", tone: "ok" } :
    s === "review" ? { l: "На проверке", tone: "lavender" } :
    s === "rejected" ? { l: "Отклонено", tone: "warn" } : { l: "Черновик", tone: "ghost" };

  return (
    <div className="mt-6">
      <div className="mb-3 flex items-center gap-2">
        <Sparkles size={16} className="text-[#0056FF]" />
        <span className="tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>Мои предложения</span>
      </div>
      <div className="space-y-2.5">
        {mine.map((a) => {
          const st = statusMeta(a.status);
          return (
            <Card key={a.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
              <div className="min-w-0">
                <div className="mb-1 flex items-center gap-1.5">
                  <Pill tone="lavender">{kindLabel(a.kind)}</Pill>
                  <Pill tone={st.tone}>{st.l}</Pill>
                  {a.author.anonymous && <Pill tone="ghost"><EyeOff size={11} /> Анонимно</Pill>}
                </div>
                <div className="truncate tracking-tight text-black dark:text-white">{a.title || "Без названия"}</div>
                <div className="mt-0.5 text-[12px] tracking-tight text-black/45 dark:text-white/45">{a.date}{a.status === "rejected" && " · отклонено редактором"}</div>
              </div>
              {a.status === "draft" && (
                <button onClick={() => setResume(a)} className="inline-flex items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 py-2 text-[13px] tracking-tight text-white transition-all hover:bg-[#0049DB] active:translate-y-[1px]"><Edit3 size={14} /> Продолжить</button>
              )}
            </Card>
          );
        })}
      </div>
      <ProposeContentModal
        open={!!resume}
        kind={(resume?.kind ?? "scenario") as ContentKind}
        editId={resume?.id}
        initial={resume ? { kind: resume.kind, title: resume.title, summary: resume.summary, bodyHtml: resume.bodyHtml, cover: resume.cover, tags: resume.tags, category: resume.category, date: resume.date, anonymous: resume.author.anonymous } : undefined}
        onClose={() => setResume(null)}
      />
    </div>
  );
}
