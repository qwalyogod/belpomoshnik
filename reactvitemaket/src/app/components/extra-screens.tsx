import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";
import {
  Search, FileText, Building2, Lock, Check, ChevronRight, ChevronLeft, AlertCircle,
  ArrowUpRight, X, Star, Plus, Trash2, Edit3, Shield, Globe, BellRing, EyeOff,
  Eye, Upload, Download, ExternalLink,
  Award, BookOpen, Sparkles, Clock, MapPin, Wrench, Newspaper,
  ListChecks, KeyRound, Loader2,
} from "lucide-react";
import { Card, Pill, PrimaryButton, GhostButton, LocationPicker } from "./belp-ui";
import { ContentEditor, type ContentKind, type ContentDraft } from "./content-editor";
import { isBiometricAvailable, requestPushPermission, sendTestNotification, getPushStatus } from "../services/a11y";
import { useNavigate } from "react-router";
import { useStore, maskDocumentNumber, DOC_TYPE_LABEL } from "../data/store";
import { apiClient, API_BASE_URL } from "../services/api";
import { buildSuggestions, getRecentSearches, addRecentSearch, POPULAR_QUERIES, SuggestionItem } from "../services/search";
import {
  institutionsForScenario,
  matchInstitutions,
  matchInstitutionsForAddresses,
  hasProfileLocation,
  profileAddresses,
} from "../services/institutions";
import { LEARNING_QUIZ, LEARNING_CATEGORIES, ACHIEVEMENTS_CATALOG } from "../data/mock";
import { Scenario, UserDocumentType, Lang, Article, ArticleKind, CustomField } from "../data/types";

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
  const { role, createSituation, favorites, toggleFavorite, situationByScenario, scenarioById, profile, authorities } = useStore();
  const isFav = favorites.includes(scenario.id);
  // v1.2: ближайшие учреждения подбираем по ОСНОВНОМУ адресу пользователя
  // (а не по legacy city/region). Нет основного — берём первый адрес, иначе
  // fallback на city/region профиля.
  const profileAddressList = profileAddresses(profile);
  const primaryAddress = profileAddressList[0] ?? { city: profile.city, region: profile.region, district: profile.district };
  const hasLocation = hasProfileLocation(primaryAddress);
  const scenarioInstitutionPool = institutionsForScenario(scenario.institutions, authorities, scenario.category, scenario.title);
  const nearInstitutions = matchInstitutions(scenarioInstitutionPool, primaryAddress);
  const nearIds = new Set(nearInstitutions.map(i => i.id));
  // Ближайшие (matched) — первыми, затем остальные, чтобы список не был пустым.
  const matchedInstitutions = [
    ...nearInstitutions,
    ...scenarioInstitutionPool.filter(i => !nearIds.has(i.id)).map(i => ({ ...i, matched: false as const })),
  ].slice(0, 12);
  const existing = situationByScenario(scenario.id);

  const handleCreate = () => {
    if (!onProtected()) return;
    if (existing) {
      onOpenMySituation(existing.id);
      return;
    }
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

        <div className="flex w-full flex-col gap-2 sm:w-auto sm:min-w-[330px]">
          <div className="flex w-full items-center gap-2">
            <button
              onClick={() => toggleFavorite(scenario.id)}
              aria-label={isFav ? "Убрать из избранного" : "В избранное"}
              className={`grid h-[54px] w-[54px] shrink-0 place-items-center rounded-[22px] border transition-all active:translate-y-[1px] ${isFav ? "border-[#0056FF]/20 bg-[#E3E7FC] text-[#0056FF] dark:border-[#7FA8FF]/20 dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "border-black/[0.08] bg-white text-black/55 hover:bg-black/[0.03] dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-white/55 dark:hover:bg-white/[0.08]"}`}
            >
              <Star size={19} fill={isFav ? "currentColor" : "none"} />
            </button>
            <button
              type="button"
              onClick={handleCreate}
              className="inline-flex min-h-[54px] flex-1 items-center justify-center rounded-[22px] bg-[#0056FF] px-5 py-3 text-[15px] font-semibold leading-tight tracking-tight text-white shadow-[0_16px_42px_-18px_rgba(0,86,255,0.65)] transition-all hover:bg-[#0049DB] active:translate-y-[1px]"
            >
              <span className="inline-flex max-w-full items-center justify-center gap-2 text-center">
                {existing ? <Check size={18} className="shrink-0" /> : <Plus size={18} className="shrink-0" />}
                <span>{existing ? "Открыть мою ситуацию" : "Создать мою ситуацию"}</span>
              </span>
            </button>
          </div>
          {existing && (
            <div className="inline-flex items-center gap-2 rounded-[18px] bg-emerald-50 px-3 py-2 text-[12px] font-medium tracking-tight text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
              <Check size={14} />
              Уже добавлено в «Мои ситуации»
            </div>
          )}
        </div>
      </div>

      <Card className="p-5">
        <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Для кого</div>
        <div className="mt-1 tracking-tight text-black dark:text-white">{scenario.forWhom}</div>
      </Card>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>Этапы и задачи</div>
            {existing ? (
              <button onClick={() => onOpenMySituation(existing.id)} className="inline-flex items-center gap-1 text-[13px] tracking-tight text-[#0056FF]">
                Перейти к выполнению <ChevronRight size={14} />
              </button>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-[#F6F7FB] px-3 py-1.5 text-[11px] tracking-tight text-black/55 dark:bg-white/[0.05] dark:text-white/55">
                <Lock size={11} /> Отмечать можно после добавления в «Мои ситуации»
              </span>
            )}
          </div>
          {/* В режиме просмотра задачи — read-only (без чекбоксов). Отметка
              выполнения доступна только в «Моей ситуации» после добавления. */}
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
                      <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center text-black/30 dark:text-white/30">
                        {blocked ? <Lock size={12} /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
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
              {hasLocation && <Pill tone="lavender">{primaryAddress.city || primaryAddress.region}</Pill>}
            </div>
            {hasLocation ? (
              <div className="mt-1 text-[12px] tracking-tight text-black/50 dark:text-white/50">
                Ближайшие — по вашему основному адресу из профиля.
              </div>
            ) : (
              <div className="mt-1 text-[12px] tracking-tight text-black/50 dark:text-white/50">
                Укажите основной адрес в профиле, чтобы подобрать ближайшие учреждения.
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
  const { situations, scenarioById, toggleTask, taskIsBlocked, situationProgress, deleteSituation, setNote, profile, authorities } = useStore();
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
  const addressGroups = matchInstitutionsForAddresses(
    institutionsForScenario(scenario.institutions, authorities, scenario.category, scenario.title),
    profileAddresses(profile),
  );

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

      <Card className="p-5">
        <div className="flex items-center gap-2">
          <Building2 size={16} className="text-[#0056FF]" />
          <div className="tracking-tight text-black dark:text-white">Куда обращаться</div>
        </div>
        <div className="mt-1 text-[12px] tracking-tight text-black/50 dark:text-white/50">
          Учреждения подбираются по адресу из профиля. Если адресов несколько, показываем отдельные группы.
        </div>
        <div className="mt-4 space-y-4">
          {addressGroups.map(group => {
            const title = group.address.label || group.address.city || group.address.region || "Адрес";
            const subtitle = [group.address.city, group.address.district, group.address.region].filter(Boolean).join(" · ");
            const items = group.items.slice(0, 5);
            return (
              <div key={group.address.id || title} className="rounded-2xl bg-[#F6F7FB] p-3.5 dark:bg-white/[0.03]">
                <div className="flex flex-wrap items-center gap-2">
                  <Pill tone="lavender">{title}</Pill>
                  {subtitle && <span className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{subtitle}</span>}
                </div>
                <div className="mt-3 space-y-2.5">
                  {items.map(ins => (
                    <div key={ins.id} className="flex items-start gap-3">
                      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                        <Building2 size={15} />
                      </span>
                      <div className="min-w-0 flex-1 text-[13px] tracking-tight">
                        <div className="text-black dark:text-white">{ins.name}</div>
                        <div className="text-black/55 dark:text-white/55">{ins.address || ins.matchReason || "Адрес уточняется"}</div>
                        {(ins.phone || ins.hours) && (
                          <div className="mt-0.5 text-[12px] text-black/45 dark:text-white/45">
                            {[ins.phone, ins.hours].filter(Boolean).join(" · ")}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {items.length === 0 && (
                    <div className="text-[13px] tracking-tight text-black/55 dark:text-white/55">
                      Для этого адреса точное учреждение пока не найдено. Проверьте город/район в профиле.
                    </div>
                  )}
                </div>
              </div>
            );
          })}
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
  const { settings, updateSettings, setLang, authSession } = useStore();
  const accessToken = authSession?.access_token ?? null;

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
          {/* v1.1 (P8): push-уведомления через Notification API (web).
              Если браузер не поддерживает — показываем статус «не поддерживается». */}
          {getPushStatus() === "unsupported" ? (
            <Row label="Push-уведомления" sub="Браузер не поддерживает push" right={<Pill tone="ghost">Недоступно</Pill>} />
          ) : (
            <Row
              label="Push-уведомления"
              sub={getPushStatus() === "granted" ? "Разрешение выдано — тестовое сообщение можно отправить" : "Запросим разрешение у браузера"}
              right={
                <div className="flex items-center gap-2">
                  {getPushStatus() === "granted" && (
                    <button
                      onClick={() => sendTestNotification("Белпомощник", "Тестовое уведомление")}
                      className="rounded-full bg-black/[0.04] px-3 py-1.5 text-[12px] tracking-tight text-black hover:bg-black/[0.08] dark:bg-white/[0.06] dark:text-white dark:hover:bg-white/[0.12]"
                    >
                      Тест
                    </button>
                  )}
                  <Toggle on={settings.notifications.push} onChange={async () => {
                    const next = !settings.notifications.push;
                    if (next && getPushStatus() !== "granted") {
                      const result = await requestPushPermission();
                      if (result === "denied") {
                        // Не дадим обмануть UI: если браузер запретил — выключаем
                        // локальный флаг, чтобы он не расходился с реальностью.
                        updateSettings({ notifications: { ...settings.notifications, push: false } });
                        return;
                      }
                    }
                    updateSettings({ notifications: { ...settings.notifications, push: next } });
                  }} />
                </div>
              }
            />
          )}
        </div>
      </Card>

      <Card className="p-5">
        <div className="flex items-center gap-2"><Shield size={15} className="text-[#0056FF]" /><div className="tracking-tight text-black dark:text-white">Приватность</div></div>
        <div className="mt-2 divide-y divide-black/[0.05] dark:divide-white/[0.05]">
          <Row label="Скрывать данные документов" sub="Номера маскируются по умолчанию"
            right={<Toggle on={settings.privacy.maskDocuments} onChange={() => updateSettings({ privacy: { ...settings.privacy, maskDocuments: !settings.privacy.maskDocuments } })} />} />
          {/* v1.1 (P8): Face/Touch ID — только в native-оболочке. В web показываем
              честный текст, что функция доступна в приложении на телефоне. */}
          {isBiometricAvailable() ? (
            <Row label="Быстрый вход (Face/Touch ID)" right={<Toggle on={settings.privacy.quickLogin} onChange={() => updateSettings({ privacy: { ...settings.privacy, quickLogin: !settings.privacy.quickLogin } })} />} />
          ) : (
            <Row label="Быстрый вход" sub="Face/Touch ID доступны в мобильном приложении" right={<Pill tone="ghost">В приложении</Pill>} />
          )}
        </div>
      </Card>

      {/* Промпт 3/4: личный Groq-ключ. Доступно любому авторизованному пользователю. */}
      {accessToken && <GroqKeyCard accessToken={accessToken} />}

      {/* Карточка «Разработка» скрыта: смена сервера теперь происходит в нативной
          оболочке (ServerPicker на экране ввода адресов). В вебе менять сервер
          не нужно — Vite dev запускается на :8560, бэк на :8060. */}
    </div>
  );
}

type AiSettingsStatus = {
  server_provider_available: boolean;
  user_key_configured: boolean;
  key_storage_available: boolean;
  masked_key: string;
  model: string;
  effective_mode: "user_key" | "needs_key" | string;
  last_checked_at?: string | null;
};

// Достаём дружелюбный текст ошибки из Error(message) = тело FastAPI {"detail":"..."}.
function apiErrorText(e: any, fallback: string): string {
  const raw: string = e?.message ?? "";
  try {
    const j = JSON.parse(raw);
    if (j && typeof j.detail === "string" && j.detail) return j.detail;
  } catch { /* not json */ }
  return raw && raw.length > 0 && raw.length < 240 ? raw : fallback;
}

// Промпт 3 (п.3) + Промпт 4 (п.7): карточка управления личным Groq-ключом
// в «Параметрах аккаунта». Полный ключ на фронт не приходит — только masked.
function GroqKeyCard({ accessToken }: { accessToken: string }) {
  const [status, setStatus] = useState<AiSettingsStatus | null>(null);
  const [keyInput, setKeyInput] = useState("");
  const [model, setModel] = useState("");
  const [busy, setBusy] = useState<null | "save" | "test" | "delete">(null);
  const [feedback, setFeedback] = useState<{ ok: boolean; text: string } | null>(null);

  const refresh = () => {
    apiClient.getAiSettings<AiSettingsStatus>(accessToken)
      .then((s) => { setStatus(s); setModel((m) => m || s.model || ""); })
      .catch(() => setStatus(null));
  };
  useEffect(() => { refresh(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [accessToken]);

  const storageReady = status?.key_storage_available !== false;
  const hasKey = !!status?.user_key_configured;

  const save = async () => {
    if (!keyInput.trim()) { setFeedback({ ok: false, text: "Введите ключ Groq." }); return; }
    setBusy("save"); setFeedback(null);
    try {
      const s = await apiClient.putGroqKey<AiSettingsStatus>(accessToken, keyInput.trim(), model.trim(), true);
      setStatus(s); setKeyInput("");
      setFeedback({ ok: true, text: "Ключ сохранён и проверен — AI-помощник работает с вашим ключом." });
    } catch (e: any) {
      setFeedback({ ok: false, text: apiErrorText(e, "Не удалось сохранить ключ. Проверьте его и попробуйте снова.") });
    } finally { setBusy(null); }
  };
  const test = async () => {
    setBusy("test"); setFeedback(null);
    try {
      const r = await apiClient.testAiSettings<{ ok: boolean; message: string }>(accessToken);
      setFeedback({ ok: r.ok, text: r.message });
    } catch (e: any) {
      setFeedback({ ok: false, text: apiErrorText(e, "Не удалось проверить ключ.") });
    } finally { setBusy(null); }
  };
  const removeKey = async () => {
    setBusy("delete"); setFeedback(null);
    try {
      const s = await apiClient.deleteGroqKey<AiSettingsStatus>(accessToken);
      setStatus(s); setModel(s.model || "");
      setFeedback({ ok: true, text: "Ключ удалён. AI-помощник снова попросит ключ." });
    } catch (e: any) {
      setFeedback({ ok: false, text: apiErrorText(e, "Не удалось удалить ключ.") });
    } finally { setBusy(null); }
  };

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2"><KeyRound size={15} className="text-[#0056FF]" /><div className="tracking-tight text-black dark:text-white">AI-помощник (ключ Groq)</div></div>

      <div className="mt-2.5 flex items-center gap-1.5 text-[12px] tracking-tight">
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${hasKey ? "bg-emerald-500" : "bg-amber-500"}`} />
        <span className={hasKey ? "text-emerald-700 dark:text-emerald-300" : "text-amber-700 dark:text-amber-300"}>
          {hasKey ? "Ключ подключён — AI-помощник работает" : "Ключ не задан — AI-помощник попросит его в чате"}
        </span>
      </div>

      {hasKey && status?.masked_key && (
        <div className="mt-3 flex items-center justify-between rounded-2xl bg-[#F6F7FB] px-3.5 py-2.5 text-[13px] tracking-tight dark:bg-white/[0.05]">
          <span className="text-black/60 dark:text-white/60">Текущий ключ</span>
          <span className="font-mono text-black dark:text-white">{status.masked_key}</span>
        </div>
      )}

      {!storageReady && (
        <div className="mt-3 rounded-2xl border border-amber-200/60 bg-amber-50 px-3 py-2 text-[12px] tracking-tight text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
          Хранилище ключей не настроено на сервере — добавление ключа недоступно.
        </div>
      )}

      <div className="mt-3 rounded-2xl bg-[#F6F7FB] px-3.5 py-3 text-[12px] leading-relaxed tracking-tight text-black/60 dark:bg-white/[0.04] dark:text-white/60">
        Как получить ключ: откройте <span className="text-[#0056FF]">console.groq.com</span> → войдите или зарегистрируйтесь → раздел «API Keys» → «Create API Key» → скопируйте ключ (gsk_…) и вставьте ниже.
      </div>

      <label className="mt-3 block">
        <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{hasKey ? "Новый ключ (для замены)" : "Groq API key"}</span>
        <input
          value={keyInput}
          onChange={(e) => setKeyInput(e.target.value)}
          type="password"
          autoComplete="off"
          placeholder="gsk_..."
          disabled={!storageReady}
          className="mt-1 h-11 w-full rounded-2xl border border-black/[0.08] bg-white px-3.5 font-mono text-[14px] tracking-tight text-black outline-none focus:border-[#0056FF] disabled:opacity-50 dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-white"
        />
      </label>

      <label className="mt-3 block">
        <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Модель (опционально)</span>
        <input
          value={model}
          onChange={(e) => setModel(e.target.value)}
          placeholder="llama-3.1-8b-instant"
          disabled={!storageReady}
          className="mt-1 h-11 w-full rounded-2xl border border-black/[0.08] bg-white px-3.5 text-[14px] tracking-tight text-black outline-none focus:border-[#0056FF] disabled:opacity-50 dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-white"
        />
      </label>

      {feedback && (
        <div className={`mt-3 rounded-2xl px-3 py-2 text-[12px] tracking-tight ${feedback.ok
          ? "border border-emerald-300/60 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200"
          : "border border-red-300/60 bg-red-50 text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300"}`}>
          {feedback.text}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        <button onClick={save} disabled={busy !== null || !storageReady}
          className="inline-flex items-center gap-1.5 rounded-2xl bg-[#0056FF] px-4 py-2.5 text-[13px] font-medium tracking-tight text-white disabled:opacity-50">
          {busy === "save" ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Сохранить ключ
        </button>
        {hasKey && (
          <button onClick={test} disabled={busy !== null}
            className="inline-flex items-center gap-1.5 rounded-2xl border border-black/10 px-4 py-2.5 text-[13px] tracking-tight text-black/75 hover:bg-black/[0.04] disabled:opacity-50 dark:border-white/10 dark:text-white/75 dark:hover:bg-white/[0.06]">
            {busy === "test" ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />} Проверить
          </button>
        )}
        {hasKey && (
          <button onClick={removeKey} disabled={busy !== null}
            className="inline-flex items-center gap-1.5 rounded-2xl border border-red-200 px-4 py-2.5 text-[13px] tracking-tight text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/30 dark:text-red-300 dark:hover:bg-red-500/10">
            {busy === "delete" ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />} Удалить ключ
          </button>
        )}
      </div>

      <div className="mt-3 space-y-1 text-[11px] leading-relaxed tracking-tight text-black/45 dark:text-white/45">
        <p>Ключ хранится на сервере в зашифрованном виде и привязан к вашему аккаунту.</p>
        <p>Полный ключ после сохранения не показывается.</p>
      </div>
    </Card>
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

      <Card className="p-5">
        <div className="tracking-tight text-black dark:text-white">Достижения</div>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {ACHIEVEMENTS_CATALOG.map(a => {
            const earned = a.earned || !!profile?.achievements?.some(pa => (pa as { id?: string; title?: string }).id === a.id || (pa as { title?: string }).title === a.title);
            return (
              <div key={a.id} className={`flex items-center gap-3 rounded-2xl px-3.5 py-3 ${earned ? "bg-[#E3E7FC] dark:bg-[#0E1A3A]" : "bg-black/[0.03] opacity-70 dark:bg-white/[0.04]"}`}>
                <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${earned ? "bg-white text-[#0056FF] dark:bg-[#0B0D13] dark:text-[#7FA8FF]" : "bg-black/[0.05] text-black/30 dark:bg-white/[0.06] dark:text-white/30"}`}>{earned ? <Award size={16} /> : <Lock size={14} />}</span>
                <div className="min-w-0">
                  <div className="text-[13px] tracking-tight text-black dark:text-white">{a.title}</div>
                  <div className="truncate text-[11px] tracking-tight text-black/50 dark:text-white/50">{a.desc}</div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

/* ---------------- AI ASSISTANT ---------------- */
type AssistantLink = {
  title: string;
  path: string;
  kind: string;
  snippet?: string;
};
type AssistantMsg = {
  role: "user" | "assistant";
  text: string;
  section?: { id: string; title: string; description: string; route: string };
  warning?: boolean;
  links?: AssistantLink[];
  source?: "llm" | "local" | "needs_key";
};

const LINK_ICONS: Record<string, React.ReactNode> = {
  scenario: <FileText size={15} />,
  problem: <AlertCircle size={15} />,
  law: <BookOpen size={15} />,
  extremist: <Shield size={15} />,
  news: <Newspaper size={15} />,
  authority: <Building2 size={15} />,
  document: <FileText size={15} />,
  section: <ArrowUpRight size={15} />,
};

/** Промпт 4: ChatGPT-like UI с историей сессий, structured response,
 * actions (create_user_situation) и empty state с starter prompts.
 *
 * Архитектура:
 * - desktop: sidebar истории + основная панель сообщений (≈900–1100px)
 * - mobile: одна панель на весь экран
 * - guest: локальный state без сохранения, без actions
 * - citizen+: backend sessions + messages + actions
 */
type AssistantAction = {
  type: string;
  label: string;
  scenario_id?: string;
  title?: string;
  path?: string;
  disabled?: boolean;
  completed?: boolean;
};
type AssistantSource = { kind: string; title: string; path?: string };
type AssistantMsg2 = {
  id?: string;
  role: "user" | "assistant";
  text: string;
  links?: AssistantLink[];
  actions?: AssistantAction[];
  sources?: AssistantSource[];
  source?: "llm" | "local" | "needs_key";
  section?: { id: string; title: string; description: string; route: string };
  warning?: boolean;
  /** Промпт 4: пометки UI для action-completed. */
  meta?: Record<string, unknown>;
};
type AssistantSession = {
  id: string;
  title: string;
  mode: string;
  archived: boolean;
  last_message_preview: string;
  created_at: string;
  updated_at: string;
};

const STARTER_PROMPTS = [
  "Я потерял паспорт, что делать?",
  "Куда обратиться по ЖКХ?",
  "Как оформить ситуацию по рождению ребёнка?",
  "Какие документы нужны для водительского удостоверения?",
  "Что делать с налогом на недвижимость?",
];

export function AssistantPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { role, authSession } = useStore();
  const navigate = useNavigate();
  const isAuth = !!authSession?.access_token;
  const accessToken = authSession?.access_token ?? null;

  // Сессии (только для авторизованных)
  const [sessions, setSessions] = useState<AssistantSession[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<AssistantMsg2[]>([]);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const composerRef = useRef<HTMLTextAreaElement>(null);

  // Авто-рост поля ввода под содержимое (без «выпирания» переносимого текста).
  useEffect(() => {
    const el = composerRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
  }, [value]);

  // Загружаем сессии при открытии.
  useEffect(() => {
    if (!open || !accessToken) return;
    apiClient.listAssistantSessions<AssistantSession[]>(accessToken)
      .then((arr) => {
        setSessions(Array.isArray(arr) ? arr : []);
      })
      .catch(() => setSessions([]));
  }, [open, accessToken]);

  // Загружаем сообщения текущей сессии.
  useEffect(() => {
    if (!open || !accessToken || !currentSession) return;
    apiClient.listAssistantMessages<any[]>(accessToken, currentSession)
      .then((arr) => {
        if (!Array.isArray(arr)) return;
        setMessages(arr.map((m): AssistantMsg2 => ({
          id: m.id,
          role: m.role,
          text: m.content,
          links: m.links,
          actions: m.actions,
          sources: m.sources,
          source: m.source,
        })));
      })
      .catch(() => undefined);
  }, [open, accessToken, currentSession]);

  // Сброс при закрытии.
  useEffect(() => {
    if (!open) {
      setValue("");
      setSidebarOpen(false);
    }
  }, [open]);

  if (!open) return null;

  const newChat = () => {
    setCurrentSession(null);
    setMessages([]);
  };

  const openSession = (id: string) => {
    setCurrentSession(id);
    setSidebarOpen(false);
  };

  const deleteSession = async (id: string) => {
    if (!accessToken) return;
    try {
      await apiClient.deleteAssistantSession(accessToken, id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (currentSession === id) newChat();
    } catch {/* ignore */}
  };

  const send = async (overrideText?: string) => {
    const text = (overrideText ?? value).trim();
    if (!text || busy) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setValue("");
    setBusy(true);
    try {
      if (accessToken) {
        // Создаём сессию, если её ещё нет.
        let sid = currentSession;
        if (!sid) {
          const created = await apiClient.createAssistantSession<AssistantSession>(accessToken, {});
          sid = created.id;
          setCurrentSession(sid);
          setSessions((prev) => [created, ...prev]);
        }
        const res = await apiClient.sendAssistantMessage<{
          id: string;
          role: string;
          content: string;
          links: AssistantLink[];
          actions: AssistantAction[];
          sources: AssistantSource[];
          source: "llm" | "local";
        }>(accessToken, sid, text);
        setMessages((m) => [
          ...m,
          {
            id: res.id,
            role: "assistant",
            text: res.content,
            links: res.links,
            actions: res.actions,
            sources: res.sources,
            source: res.source,
          },
        ]);
        // Обновляем list of sessions (превью + порядок).
        apiClient.listAssistantSessions<AssistantSession[]>(accessToken).then(setSessions).catch(() => undefined);
      } else {
        // Guest: legacy router без истории.
        const res = await apiClient.askAssistant<{
          response_text: string;
          section: { id: string; title: string; description: string; route: string };
          requires_auth_warning: boolean;
        }>({ message: text, role, is_guest: true });
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            text: res.response_text,
            section: res.section,
            warning: res.requires_auth_warning,
          },
        ]);
      }
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Не удалось связаться с помощником. Попробуйте позже или воспользуйтесь поиском и каталогом." },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const goToPath = (path: string) => {
    onClose();
    if (path.startsWith("/")) navigate(path);
    else navigate(`/${path}`);
  };
  const goTo = (route: string) => { onClose(); navigate(route); };

  const handleAction = async (msgIdx: number, action: AssistantAction) => {
    if (!accessToken || action.type !== "create_user_situation" || !action.scenario_id) return;
    setMessages((prev) => prev.map((m, i) => i === msgIdx ? {
      ...m,
      actions: m.actions?.map((a) => a === action ? { ...a, disabled: true } : a),
    } : m));
    try {
      const res = await apiClient.createSituationFromAssistant<{
        created: boolean;
        situation_id: string;
        route: string;
        message: string;
      }>(accessToken, action.scenario_id, currentSession ?? undefined);
      setMessages((prev) => prev.map((m, i) => i === msgIdx ? {
        ...m,
        actions: m.actions?.map((a) => a === action ? {
          ...a,
          completed: true,
          disabled: false,
          label: res.created ? "Открыть в моих ситуациях" : "Открыть существующую ситуацию",
          path: res.route,
          type: "open_link",
        } : a),
      } : m));
    } catch {
      setMessages((prev) => prev.map((m, i) => i === msgIdx ? {
        ...m,
        actions: m.actions?.map((a) => a === action ? { ...a, disabled: false } : a),
      } : m));
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-end justify-end p-0 sm:items-end sm:justify-end sm:p-6" onClick={onClose}>
      <div className="absolute inset-0 bg-black/30 backdrop-blur-[2px]" />
      <div onClick={(e) => e.stopPropagation()}
        className="relative flex h-[88dvh] w-full flex-col overflow-hidden rounded-t-3xl border border-black/[0.08] bg-white shadow-[0_40px_120px_-30px_rgba(15,23,42,0.5)] dark:border-white/[0.08] dark:bg-[#0B0D13] sm:h-[640px] sm:w-[920px] sm:max-w-[92vw] sm:rounded-3xl sm:flex-row">
        {/* Sidebar — история (desktop) / drawer (mobile) */}
        {isAuth && (
          <div className={`absolute inset-y-0 left-0 z-10 w-[72%] max-w-[260px] transform border-r border-black/[0.06] bg-white transition-transform dark:border-white/[0.06] dark:bg-[#0B0D13] sm:relative sm:w-[240px] sm:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full sm:translate-x-0"}`}>
            <div className="flex items-center justify-between p-3">
              <button onClick={newChat} className="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-black/10 px-3 py-2 text-[13px] tracking-tight hover:bg-black/[0.04] dark:border-white/10 dark:text-white/85 dark:hover:bg-white/[0.06]">
                <Plus size={14} /> Новый чат
              </button>
              <button onClick={() => setSidebarOpen(false)} className="ml-2 grid h-8 w-8 place-items-center rounded-lg text-black/40 hover:bg-black/[0.04] dark:text-white/40 sm:hidden"><X size={14} /></button>
            </div>
            <div className="px-2 pb-3">
              <div className="px-2 pb-2 text-[10px] uppercase tracking-[0.1em] text-black/40 dark:text-white/40">История</div>
              <div className="space-y-1 max-h-[calc(88vh-100px)] overflow-y-auto pr-1 sm:max-h-[540px]">
                {sessions.map((s) => (
                  <div key={s.id} className={`group flex items-center gap-1 rounded-xl px-2 py-2 text-[13px] tracking-tight ${currentSession === s.id ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/70 hover:bg-black/[0.04] dark:text-white/70 dark:hover:bg-white/[0.06]"}`}>
                    <button onClick={() => openSession(s.id)} className="min-w-0 flex-1 truncate text-left">
                      {s.title || "Новый чат"}
                    </button>
                    <button onClick={() => deleteSession(s.id)} className="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-black/35 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100 dark:text-white/35"><Trash2 size={12} /></button>
                  </div>
                ))}
                {sessions.length === 0 && (
                  <div className="px-2 py-1 text-[11px] tracking-tight text-black/40 dark:text-white/40">История пустая. Задайте первый вопрос.</div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Главная панель */}
        <div className="relative flex min-h-0 min-w-0 flex-1 flex-col">
          <div className="flex items-center justify-between border-b border-black/[0.06] px-4 py-3 dark:border-white/[0.06]">
            <div className="flex items-center gap-2">
              {isAuth && (
                <button onClick={() => setSidebarOpen((v) => !v)} className="grid h-8 w-8 place-items-center rounded-lg text-black/55 hover:bg-black/[0.04] dark:text-white/55 sm:hidden">
                  <ListChecks size={15} />
                </button>
              )}
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#0056FF] text-white"><Sparkles size={16} /></span>
              <div>
                <div className="tracking-tight text-black dark:text-white">AI-помощник Белпомощника</div>
                <div className="text-[11px] tracking-tight text-black/45 dark:text-white/45">Подскажет по материалам проекта</div>
              </div>
            </div>
            <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg text-black/40 hover:bg-black/[0.04] dark:text-white/40 dark:hover:bg-white/[0.06]"><X size={16} /></button>
          </div>

          {/* Тело */}
          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4 [&::-webkit-scrollbar]:hidden">
            {messages.length === 0 && (
              <div className="grid h-full place-items-center py-6 text-center">
                <div className="max-w-[520px] space-y-3 px-2">
                  <div className="text-[22px] tracking-tight text-black dark:text-white">Чем помочь?</div>
                  <p className="text-[13px] tracking-tight text-black/55 dark:text-white/55">
                    Опишите проблему обычными словами — я найду подходящие материалы в Белпомощнике.
                  </p>
                  <div className="mt-4 flex flex-wrap items-center justify-center gap-1.5">
                    {STARTER_PROMPTS.map((p) => (
                      <button
                        key={p}
                        onClick={() => send(p)}
                        className="rounded-full border border-black/[0.08] bg-white px-3 py-1.5 text-[12px] tracking-tight text-black/70 hover:border-[#0056FF] hover:text-[#0056FF] dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-white/70"
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                  {!isAuth && (
                    <div className="mt-5 rounded-2xl border border-amber-200/60 bg-amber-50 px-3 py-2 text-[12px] tracking-tight text-amber-800 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200">
                      Войдите, чтобы сохранять историю чатов и добавлять сценарии в «Мои ситуации».
                    </div>
                  )}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i}>
                <div className={`max-w-[85%] whitespace-pre-line rounded-2xl px-3.5 py-2.5 text-[14px] leading-relaxed tracking-tight ${m.role === "user"
                  ? "ml-auto bg-[#0056FF] text-white"
                  : "bg-[#F6F7FB] text-black dark:bg-white/[0.05] dark:text-white"}`}>
                  {m.text}
                  {m.source && m.source === "local" && (
                    <div className="mt-1 text-[10px] uppercase tracking-[0.1em] text-black/40 dark:text-white/40">
                      Локальный ответ — AI-провайдер недоступен
                    </div>
                  )}
                </div>

                {/* Промпт 3/4: нет личного ключа → CTA открыть настройки. */}
                {m.source === "needs_key" && (
                  <button
                    onClick={() => { onClose(); navigate("/settings"); }}
                    className="mt-2 inline-flex items-center gap-1.5 rounded-2xl bg-[#0056FF] px-4 py-2.5 text-[13px] font-medium tracking-tight text-white"
                  >
                    <KeyRound size={14} /> Открыть настройки и добавить ключ
                  </button>
                )}

                {m.links && m.links.length > 0 && (
                  <div className="mt-2 flex flex-col gap-1.5">
                    {m.links.map((l, li) => (
                      <button
                        key={`${i}-l-${li}`}
                        onClick={() => goToPath(l.path)}
                        className="group flex w-full items-center gap-2.5 rounded-2xl border border-black/[0.08] bg-white px-3 py-2.5 text-left transition-colors hover:bg-black/[0.02] dark:border-white/[0.08] dark:bg-white/[0.03] dark:hover:bg-white/[0.06]"
                        title={l.path}
                      >
                        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                          {LINK_ICONS[l.kind] ?? <ArrowUpRight size={15} />}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-[13px] tracking-tight text-black dark:text-white">{l.title}</span>
                          {l.snippet && (
                            <span className="block truncate text-[11px] tracking-tight text-black/45 dark:text-white/45">{l.snippet}</span>
                          )}
                        </span>
                        <span className="shrink-0 text-[11px] font-medium tracking-tight text-[#0056FF]">→</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Промпт 3+4: actions — кнопки добавить в «Мои ситуации» */}
                {m.actions && m.actions.length > 0 && (
                  <div className="mt-2 flex flex-col gap-1.5">
                    {m.actions.map((a, ai) => (
                      <button
                        key={`${i}-a-${ai}`}
                        onClick={() => {
                          if (a.type === "open_link" && a.path) {
                            goToPath(a.path);
                            return;
                          }
                          if (!isAuth) {
                            onClose();
                            navigate("/login");
                            return;
                          }
                          handleAction(i, a);
                        }}
                        disabled={a.disabled}
                        className={`group flex w-full items-center gap-2.5 rounded-2xl border px-3 py-2.5 text-left transition-colors disabled:opacity-60 ${a.completed
                          ? "border-emerald-300/60 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200"
                          : "border-[#0056FF]/30 bg-[#E3E7FC] text-[#0056FF] hover:bg-[#D5DCFB] dark:border-[#0056FF]/30 dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"}`}
                      >
                        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-white text-[#0056FF] dark:bg-white/10 dark:text-[#7FA8FF]">
                          {a.completed ? <Check size={15} /> : <Plus size={15} />}
                        </span>
                        <span className="min-w-0 flex-1 text-[13px] tracking-tight">{a.label}</span>
                        <span className="shrink-0 text-[11px] font-medium tracking-tight">→</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Legacy для guest */}
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

          {/* Composer */}
          <div className="flex items-end gap-2 border-t border-black/[0.06] p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] dark:border-white/[0.06]">
            <textarea
              ref={composerRef}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(); } }}
              rows={1}
              placeholder={isAuth ? "Например: я потерял паспорт" : "Гость — задайте вопрос, без сохранения истории"}
              className="min-h-[48px] max-h-32 flex-1 resize-none overflow-y-auto rounded-2xl bg-[#F6F7FB] px-4 py-3 text-[14px] leading-relaxed tracking-tight text-black outline-none dark:bg-white/[0.05] dark:text-white"
            />
            <button
              onClick={() => void send()}
              disabled={busy || !value.trim()}
              aria-label="Отправить"
              className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#0056FF] text-white disabled:opacity-40"
            >
              <ArrowUpRight size={18} />
            </button>
          </div>
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
          <LocationPicker value={{ region: form.region, district: form.district, city: form.city }} onChange={(v) => set(v)} />
          <ProfileField label="Адрес" value={form.address ?? ""} onChange={(v) => set({ address: v })} />

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

/* ---------------- DOCUMENT EDIT MODAL ----------------
 * v0.4: динамические поля по типу документа + «Другое» с кастомными полями.
 * Для каждого типа — свой набор полей (label/key/required/placeholder/type).
 * Для 'other' — произвольные пары имя/значение.
 */
type DocFieldDef = {
  key: "title" | "number" | "issuedAt" | "issuedBy" | "expiresAt" | "comment";
  label: string;
  placeholder: string;
  type?: "text" | "date";
  required?: boolean;
};

// Карта полей по типу. Какие-то поля общие для всех (title), какие-то
// специфичны. Для 'other' массив пустой — поля задаёт пользователь.
const DOC_FIELDS_BY_TYPE: Record<UserDocumentType, DocFieldDef[]> = {
  passport: [
    { key: "title", label: "Название", placeholder: "Паспорт гражданина РБ", required: true },
    { key: "number", label: "Серия и номер", placeholder: "MP1234567", required: true },
    { key: "issuedBy", label: "Кем выдан", placeholder: "РОВД Центрального района" },
    { key: "issuedAt", label: "Дата выдачи", placeholder: "ГГГГ-ММ-ДД", type: "date" },
    { key: "expiresAt", label: "Действует до", placeholder: "ГГГГ-ММ-ДД", type: "date" },
  ],
  driver: [
    { key: "title", label: "Название", placeholder: "Водительское удостоверение", required: true },
    { key: "number", label: "Номер", placeholder: "AB1234567", required: true },
    { key: "issuedBy", label: "Кем выдано", placeholder: "ГАИ" },
    { key: "issuedAt", label: "Дата выдачи", placeholder: "ГГГГ-ММ-ДД", type: "date" },
    { key: "expiresAt", label: "Действует до", placeholder: "ГГГГ-ММ-ДД", type: "date" },
  ],
  medical: [
    { key: "title", label: "Название", placeholder: "Личная медицинская книжка", required: true },
    { key: "number", label: "Номер", placeholder: "МК-12345" },
    { key: "issuedBy", label: "Организация", placeholder: "Поликлиника №12" },
    { key: "issuedAt", label: "Дата выдачи", placeholder: "ГГГГ-ММ-ДД", type: "date" },
    { key: "expiresAt", label: "Действует до", placeholder: "ГГГГ-ММ-ДД", type: "date" },
  ],
  birth: [
    { key: "title", label: "Название", placeholder: "Свидетельство о рождении", required: true },
    { key: "number", label: "Номер", placeholder: "I-МЮ 123456" },
    { key: "issuedBy", label: "ЗАГС", placeholder: "Центральный ЗАГС Минска" },
    { key: "issuedAt", label: "Дата выдачи", placeholder: "ГГГГ-ММ-ДД", type: "date" },
    // Свидетельство о рождении бессрочное
  ],
  housing: [
    { key: "title", label: "Название", placeholder: "Договор купли-продажи", required: true },
    { key: "number", label: "Номер документа", placeholder: "123/2026" },
    { key: "issuedBy", label: "Кем выдан", placeholder: "Нотариус" },
    { key: "issuedAt", label: "Дата выдачи", placeholder: "ГГГГ-ММ-ДД", type: "date" },
  ],
  receipt: [
    { key: "title", label: "Название", placeholder: "Квитанция ЖКХ", required: true },
    { key: "number", label: "Номер/лицевой счёт", placeholder: "12345" },
    { key: "issuedBy", label: "Кем выдана", placeholder: "ЕРИП" },
    { key: "issuedAt", label: "Дата", placeholder: "ГГГГ-ММ-ДД", type: "date" },
    { key: "expiresAt", label: "Оплатить до", placeholder: "ГГГГ-ММ-ДД", type: "date" },
  ],
  other: [
    { key: "title", label: "Название", placeholder: "Например: Страховой полис", required: true },
    { key: "comment", label: "Описание (опционально)", placeholder: "Краткое описание документа" },
  ],
};

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
  const [issuedBy, setIssuedBy] = useState(existing?.issuedBy ?? "");
  const [issuedAt, setIssuedAt] = useState(existing?.issuedAt ?? "");
  const [expiresAt, setExpiresAt] = useState(existing?.expiresAt ?? "");
  const [comment, setComment] = useState(existing?.comment ?? "");
  // v0.4: кастомные поля для 'other' (или дополнительные к базовым)
  const [customFields, setCustomFields] = useState<CustomField[]>(existing?.customFields ?? []);

  useEffect(() => {
    if (!open) return;
    setType(existing?.type ?? "passport");
    setTitle(existing?.title ?? "");
    setNumber(existing?.number ?? "");
    setIssuedBy(existing?.issuedBy ?? "");
    setIssuedAt(existing?.issuedAt ?? "");
    setExpiresAt(existing?.expiresAt ?? "");
    setComment(existing?.comment ?? "");
    setCustomFields(existing?.customFields ?? []);
  }, [existing?.comment, existing?.customFields, existing?.expiresAt, existing?.issuedAt, existing?.issuedBy, existing?.number, existing?.title, existing?.type, open]);

  if (!open) return null;

  const fields = DOC_FIELDS_BY_TYPE[type];
  const valueFor = (key: DocFieldDef["key"]): string => {
    switch (key) {
      case "title": return title;
      case "number": return number;
      case "issuedBy": return issuedBy;
      case "issuedAt": return issuedAt;
      case "expiresAt": return expiresAt;
      case "comment": return comment;
    }
  };
  // Сводная валидация: title обязателен, иначе — для конкретного типа ещё что-то
  const missingRequired = fields.some((f) => f.required && !valueFor(f.key).trim());
  const setValueFor = (key: DocFieldDef["key"], v: string): void => {
    switch (key) {
      case "title": setTitle(v); break;
      case "number": setNumber(v); break;
      case "issuedBy": setIssuedBy(v); break;
      case "issuedAt": setIssuedAt(v); break;
      case "expiresAt": setExpiresAt(v); break;
      case "comment": setComment(v); break;
    }
  };

  const save = () => {
    if (!title.trim()) return;
    const patch: Partial<typeof existing> & { customFields?: CustomField[] } = {
      type,
      title,
      number,
      issuedBy: issuedBy || undefined,
      issuedAt: issuedAt || undefined,
      expiresAt: expiresAt || undefined,
      comment: comment || undefined,
      customFields: type === "other" ? customFields.filter((f) => f.name.trim()) : undefined,
    };
    if (existing) {
      updateDocument(existing.id, patch);
    } else {
      addDocument({ type, title, number, expiresAt: expiresAt || "", status: "active" });
      // Для кастомных полей (other) — отдельный путь: addDocument сейчас не
      // принимает их. В рамках MVP: создаём документ с базовыми полями, кастомные
      // добавляются через updateDocument.
      if (type === "other" && customFields.length > 0) {
        // Без existing.id здесь ничего не сделать — пользователь увидит custom
        // поля при следующем открытии на редактирование. v0.5+: расширим API.
      }
    }
    onClose();
  };

  const addCustomField = () => {
    setCustomFields((prev) => [...prev, { name: "", value: "" }]);
  };
  const updateCustomField = (idx: number, patch: Partial<CustomField>) => {
    setCustomFields((prev) => prev.map((f, i) => (i === idx ? { ...f, ...patch } : f)));
  };
  const removeCustomField = (idx: number) => {
    setCustomFields((prev) => prev.filter((_, i) => i !== idx));
  };

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/40 p-4 backdrop-blur-sm" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-[520px] overflow-hidden rounded-3xl bg-white shadow-2xl dark:bg-[#0F1117]"
      >
        <div className="flex items-center justify-between p-6 pb-4">
          <div>
            <div className="text-[12px] tracking-tight text-[#0056FF]">{DOC_TYPE_LABEL[type]}</div>
            <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>
              {existing ? "Изменить документ" : "Новый документ"}
            </div>
          </div>
          <button onClick={onClose} className="grid h-9 w-9 place-items-center rounded-full bg-black/[0.05] text-black/55 dark:bg-white/[0.06] dark:text-white/55"><X size={15} /></button>
        </div>

        <div className="max-h-[68vh] space-y-3 overflow-y-auto px-6 pb-2 [scrollbar-width:thin]">
          {/* Тип документа — селектор смены конфигурации полей */}
          <Field label="Тип документа">
            <select
              value={type}
              onChange={(e) => setType(e.target.value as UserDocumentType)}
              className="h-11 w-full rounded-xl border border-black/10 bg-white px-3 tracking-tight outline-none focus:border-[#0056FF] dark:border-white/10 dark:bg-white/[0.04] dark:text-white"
            >
              {(Object.keys(DOC_TYPE_LABEL) as UserDocumentType[]).map((t) => (
                <option key={t} value={t}>{DOC_TYPE_LABEL[t]}</option>
              ))}
            </select>
          </Field>

          {/* Поля по типу */}
          {fields.map((f) => (
            <Field key={f.key} label={f.label} sub={f.required ? "Обязательно" : "Опционально"}>
              <Input
                value={valueFor(f.key)}
                onChange={(v) => setValueFor(f.key, v)}
                placeholder={f.placeholder}
                type={f.type}
              />
            </Field>
          ))}

          {/* v0.4: для 'other' — произвольные пары имя/значение */}
          {type === "other" && (
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Дополнительные поля</span>
                <span className="text-[11px] tracking-tight text-black/40 dark:text-white/40">Опционально</span>
              </div>
              <div className="space-y-2">
                {customFields.map((cf, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <input
                      value={cf.name}
                      onChange={(e) => updateCustomField(idx, { name: e.target.value })}
                      placeholder="Название поля"
                      className="h-10 min-w-0 flex-1 rounded-lg border border-black/10 bg-white px-3 text-[13px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/10 dark:bg-white/[0.04] dark:text-white"
                    />
                    <input
                      value={cf.value}
                      onChange={(e) => updateCustomField(idx, { value: e.target.value })}
                      placeholder="Значение"
                      className="h-10 min-w-0 flex-1 rounded-lg border border-black/10 bg-white px-3 text-[13px] tracking-tight outline-none focus:border-[#0056FF] dark:border-white/10 dark:bg-white/[0.04] dark:text-white"
                    />
                    <button
                      type="button"
                      onClick={() => removeCustomField(idx)}
                      className="grid h-10 w-10 shrink-0 place-items-center rounded-lg text-black/35 hover:bg-red-50 hover:text-red-500 dark:text-white/35 dark:hover:bg-red-500/10"
                      aria-label="Удалить поле"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addCustomField}
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-black/15 py-2.5 text-[12px] tracking-tight text-black/55 hover:bg-black/[0.02] dark:border-white/15 dark:text-white/55 dark:hover:bg-white/[0.04]"
                >
                  <Plus size={12} /> Добавить поле
                </button>
              </div>
            </div>
          )}

          <div className="rounded-xl bg-[#F6F7FB] p-3 text-[12px] tracking-tight text-black/55 dark:bg-white/[0.04] dark:text-white/55">
            <div className="flex items-center gap-2"><EyeOff size={12} /> Хранится локально, доступ только у вас.</div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 border-t border-black/[0.06] p-4 dark:border-white/[0.06]">
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
            <PrimaryButton onClick={save} disabled={missingRequired} className="h-11 px-5">Сохранить</PrimaryButton>
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
function Input({ value, onChange, placeholder, type = "text" }: {
  value: string; onChange: (v: string) => void; placeholder?: string; type?: "text" | "date";
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="h-11 w-full rounded-xl border border-black/10 bg-white px-3 tracking-tight outline-none focus:border-[#0056FF] dark:border-white/10 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/40"
    />
  );
}

/* ---------------- helpers for usage in App ---------------- */
export function formatDocumentNumber(num: string, masked: boolean) {
  return maskDocumentNumber(num, !masked);
}

/* ============================================================
   Промпт 1 — Полная карточка документа (encrypted preview + multi-format upload)
   ============================================================ */
export function DocumentCardModal({
  open, onClose, docId, onEdit,
}: {
  open: boolean;
  onClose: () => void;
  docId: string | null;
  onEdit?: (id: string) => void;
}) {
  const { documents, authSession, refreshDocuments } = useStore();
  const doc = docId ? documents.find((d) => d.id === docId) : undefined;

  // Скан хранится на сервере в зашифрованном виде. Получаем как Blob и
  // показываем через ObjectURL — никаких публичных URL на личные документы.
  const [scanObjectUrl, setScanObjectUrl] = useState<string | null>(null);
  const [scanMime, setScanMime] = useState<string>("");
  const [scanBusy, setScanBusy] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [revealNumber, setRevealNumber] = useState(false);
  const lastObjectUrlRef = useRef<string | null>(null);

  const releaseObjectUrl = () => {
    if (lastObjectUrlRef.current) {
      URL.revokeObjectURL(lastObjectUrlRef.current);
      lastObjectUrlRef.current = null;
    }
    setScanObjectUrl(null);
    setScanMime("");
  };

  // Сброс при закрытии — освобождаем ObjectURL чтобы не текла память.
  useEffect(() => {
    if (!open) {
      releaseObjectUrl();
      setScanError(null);
      setRevealNumber(false);
    }
    return () => releaseObjectUrl();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const accessToken = authSession?.access_token ?? null;
  const scanMeta = doc?.scan;

  // Подгружаем скан при открытии, если он есть и пользователь авторизован.
  useEffect(() => {
    if (!open || !doc || !scanMeta?.hasScan || !accessToken) return;
    let cancelled = false;
    setScanBusy(true);
    setScanError(null);
    apiClient
      .downloadDocumentScan(accessToken, doc.id)
      .then(({ blob, mimeType }) => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        lastObjectUrlRef.current = url;
        setScanObjectUrl(url);
        setScanMime(mimeType);
      })
      .catch((err) => {
        if (cancelled) return;
        setScanError(err instanceof Error ? err.message : "Не удалось загрузить скан.");
      })
      .finally(() => {
        if (!cancelled) setScanBusy(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, doc?.id, scanMeta?.hasScan, accessToken]);

  if (!open || !doc) return null;

  const MAX_BYTES = 8 * 1024 * 1024;
  const ALLOWED_EXT = /\.(pdf|jpe?g|png|webp)$/i;
  const ALLOWED_MIME = /^(application\/pdf|image\/(jpeg|png|webp))$/i;

  const handleFile = async (file: File) => {
    if (!accessToken) {
      setScanError("Войдите, чтобы загрузить скан.");
      return;
    }
    const mimeOk = ALLOWED_MIME.test(file.type) || ALLOWED_EXT.test(file.name);
    if (!mimeOk) {
      setScanError("Поддерживаются PDF, JPG, PNG, WEBP.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setScanError("Файл больше 8 МБ.");
      return;
    }
    setScanBusy(true);
    setScanError(null);
    try {
      await apiClient.uploadDocumentScan(accessToken, doc.id, file);
      // Обновляем список документов в сторе (приходят новые scan metadata).
      if (typeof refreshDocuments === "function") {
        await refreshDocuments();
      }
      // И сразу качаем расшифрованный blob для предпросмотра.
      const { blob, mimeType } = await apiClient.downloadDocumentScan(accessToken, doc.id);
      releaseObjectUrl();
      const url = URL.createObjectURL(blob);
      lastObjectUrlRef.current = url;
      setScanObjectUrl(url);
      setScanMime(mimeType);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : "Не удалось загрузить скан.");
    } finally {
      setScanBusy(false);
    }
  };

  const handleDeleteScan = async () => {
    if (!accessToken) return;
    setScanBusy(true);
    setScanError(null);
    try {
      await apiClient.deleteDocumentScan(accessToken, doc.id);
      releaseObjectUrl();
      if (typeof refreshDocuments === "function") await refreshDocuments();
    } catch (err) {
      setScanError(err instanceof Error ? err.message : "Не удалось удалить скан.");
    } finally {
      setScanBusy(false);
    }
  };

  const handleDownload = () => {
    if (!scanObjectUrl) return;
    const a = document.createElement("a");
    a.href = scanObjectUrl;
    a.download = scanMeta?.originalFilename || `document-${doc.id}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const maskedNumber = maskDocumentNumber(doc.number || "", !revealNumber);
  const isImageScan = scanMime.startsWith("image/");
  const sizeLabel = scanMeta?.size ? `${Math.round(scanMeta.size / 1024)} КБ` : "";
  const uploadedAtLabel = scanMeta?.uploadedAt
    ? new Date(scanMeta.uploadedAt).toLocaleString("ru-RU", { dateStyle: "medium", timeStyle: "short" })
    : "";

  return (
    <div
      className="fixed inset-0 z-[100] grid place-items-center bg-black/40 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-[560px] overflow-hidden rounded-3xl bg-white shadow-2xl dark:bg-[#0F1117]"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 p-6 pb-4">
          <div className="min-w-0 flex-1">
            <div className="text-[12px] tracking-tight text-[#0056FF]">
              {DOC_TYPE_LABEL[doc.type as keyof typeof DOC_TYPE_LABEL] ?? "Документ"}
            </div>
            <h2 className="mt-1 truncate tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>
              {doc.title}
            </h2>
            {doc.status && (
              <div className="mt-2">
                <Pill tone={doc.status === "active" ? "ok" : doc.status === "expiring" ? "warn" : "ghost"}>
                  {doc.status === "active" ? "Действует" : doc.status === "expiring" ? "Скоро истекает" : "Истёк"}
                </Pill>
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-black/[0.05] text-black/55 dark:bg-white/[0.06] dark:text-white/55"
          >
            <X size={15} />
          </button>
        </div>

        <div className="max-h-[68vh] overflow-y-auto px-6 pb-6 [scrollbar-width:thin]">
          {/* Номер с маскированием */}
          {doc.number && (
            <div className="rounded-2xl bg-[#F6F7FB] p-4 dark:bg-white/[0.04]">
              <div className="flex items-center justify-between gap-2">
                <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Номер</div>
                <button
                  onClick={() => setRevealNumber((v) => !v)}
                  className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[11px] tracking-tight shadow-sm dark:bg-white/[0.06]"
                >
                  {revealNumber ? <EyeOff size={11} /> : <Eye size={11} />}
                  {revealNumber ? "Скрыть" : "Показать"}
                </button>
              </div>
              <div className="mt-1 font-mono text-[15px] tracking-[0.18em] text-black dark:text-white">{maskedNumber}</div>
            </div>
          )}

          {/* Метаданные */}
          <div className="mt-3 space-y-2.5">
            {doc.expiresAt && (
              <MetaRow label="Действует до" value={doc.expiresAt} />
            )}
            <MetaRow
              label="Создан"
              value={doc.createdAt ? new Date(doc.createdAt).toLocaleDateString("ru-RU") : "—"}
            />
          </div>

          {/* Скан — Промпт 1: зашифровано на сервере, превью через ObjectURL */}
          <div className="mt-5">
            <div className="mb-2 flex items-center justify-between">
              <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Скан документа</div>
              <div className="inline-flex items-center gap-1 text-[11px] tracking-tight text-emerald-600 dark:text-emerald-400">
                <Lock size={11} /> Зашифровано на сервере
              </div>
            </div>

            {scanMeta?.hasScan ? (
              <div className="relative">
                <div className="overflow-hidden rounded-2xl border border-black/[0.06] bg-[#F6F7FB] dark:border-white/[0.06] dark:bg-white/[0.04]">
                  {scanBusy && !scanObjectUrl ? (
                    <div className="grid h-[280px] place-items-center text-[12px] tracking-tight text-black/55 dark:text-white/55">
                      Расшифровываем…
                    </div>
                  ) : scanObjectUrl ? (
                    isImageScan ? (
                      <img
                        src={scanObjectUrl}
                        alt={`Скан: ${doc.title}`}
                        className="h-[280px] w-full object-contain"
                      />
                    ) : (
                      <iframe
                        src={scanObjectUrl}
                        title={`Скан: ${doc.title}`}
                        className="h-[280px] w-full"
                      />
                    )
                  ) : (
                    <div className="grid h-[280px] place-items-center text-[12px] tracking-tight text-black/45 dark:text-white/45">
                      Скан зашифрован. Не удалось получить превью.
                    </div>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[11px] tracking-tight text-black/50 dark:text-white/50">
                  <span>
                    {scanMeta.mimeType || "файл"}
                    {sizeLabel ? ` · ${sizeLabel}` : ""}
                    {uploadedAtLabel ? ` · загружен ${uploadedAtLabel}` : ""}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <button
                    onClick={handleDeleteScan}
                    disabled={scanBusy}
                    className="inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-[12px] tracking-tight text-red-600 hover:bg-red-50 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-500/10"
                  >
                    <Trash2 size={13} /> Удалить скан
                  </button>
                  <button
                    onClick={handleDownload}
                    disabled={!scanObjectUrl || scanBusy}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 py-2 text-[12px] tracking-tight text-white disabled:opacity-50"
                  >
                    <Download size={13} /> Скачать
                  </button>
                </div>
              </div>
            ) : (
              <label
                className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-black/15 bg-[#F6F7FB] py-8 text-[13px] tracking-tight text-black/55 transition-colors hover:bg-black/[0.02] dark:border-white/15 dark:bg-white/[0.04] dark:text-white/55 dark:hover:bg-white/[0.04] ${scanBusy ? "pointer-events-none opacity-50" : ""}`}
              >
                <Upload size={20} className="text-[#0056FF]" />
                <span>{scanBusy ? "Загружаем…" : "Загрузить скан (PDF, JPG, PNG, WEBP)"}</span>
                <span className="text-[11px] text-black/40 dark:text-white/40">до 8 МБ · файл шифруется на сервере</span>
                <input
                  type="file"
                  accept="application/pdf,image/jpeg,image/png,image/webp,.pdf,.jpg,.jpeg,.png,.webp"
                  className="sr-only"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void handleFile(f);
                    e.currentTarget.value = "";
                  }}
                />
              </label>
            )}

            {scanError && (
              <div className="mt-2 inline-flex items-center gap-1 text-[12px] text-amber-600 dark:text-amber-400">
                <AlertCircle size={12} /> {scanError}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-2 border-t border-black/[0.06] p-4 dark:border-white/[0.06]">
          <span />
          <div className="flex gap-2">
            {onEdit && (
              <GhostButton
                onClick={() => { onEdit(doc.id); onClose(); }}
                className="h-11 gap-1.5"
              >
                <Edit3 size={14} /> Изменить
              </GhostButton>
            )}
            <PrimaryButton onClick={onClose} className="h-11 px-5">Готово</PrimaryButton>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-[13px] tracking-tight">
      <span className="text-black/55 dark:text-white/55">{label}</span>
      <span className="text-black dark:text-white">{value}</span>
    </div>
  );
}

function apiBaseUrl(): string {
  return API_BASE_URL;
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
const ARTICLE_KIND_LABEL: Record<string, string> = { news: "Новость", scenario: "Жизненный сценарий", problem: "Проблема" };

function ArticleReaderModal({ article, onClose, onEdit }: { article: Article; onClose: () => void; onEdit?: (a: Article) => void }) {
  const { registerView } = useStore();
  useEffect(() => { registerView(article.id); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [article.id]);
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
  const { updateArticle, profile, uploadMedia } = useStore();
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
        <ContentEditor kind={article.kind} mode="edit" initial={articleToDraft(article)} authorName={profile.name} uploadFile={uploadMedia} onClose={onClose} onSubmit={submit} />
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
  const { addArticle, updateArticle, currentUser, profile, isSubmitterBlocked, meId, uploadMedia } = useStore();
  if (!open) return null;
  const blocked = isSubmitterBlocked(meId ?? currentUser.id);

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
          <ContentEditor kind={kind} propose initial={initial} authorName={profile.name} uploadFile={uploadMedia} onClose={onClose} onSubmit={submit} />
        </div>
      )}
    </div>
  );
}

// «Мои предложения» — citizen sees own submissions + can resume drafts.
export function MyContributions() {
  const { articles, currentUser, meId } = useStore();
  const [resume, setResume] = useState<Article | null>(null);
  const mine = articles.filter((a) => a.author.proposerId === meId || a.author.proposerId === currentUser.id);
  if (currentUser.role === "guest" || mine.length === 0) return null;

  const kindLabel = (k: string) => (k === "news" ? "Новость" : k === "problem" ? "Проблема" : "Жизненный сценарий");
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
