import { FormEvent, useEffect, useMemo, useState } from "react";
import { AlertTriangle, Bell, CheckCircle2, KeyRound, Lock, Megaphone, RotateCcw, Save, Server, Settings2, Shield, X } from "lucide-react";
import { useStore } from "../../data/store";
import { ControlCenterAuditLog, ControlCenterStatus, SystemState } from "../../data/types";
import { apiClient } from "../../services/api";

declare global {
  interface Window {
    belpomoshnikControl?: () => void;
  }
}

type Tab = "status" | "maintenance" | "banner" | "flags" | "branding" | "broadcast" | "actions" | "audit";

const TABS: { id: Tab; title: string }[] = [
  { id: "status", title: "Статус" },
  { id: "maintenance", title: "Режимы" },
  { id: "banner", title: "Баннер" },
  { id: "flags", title: "Функции" },
  { id: "branding", title: "Брендинг" },
  { id: "broadcast", title: "Уведомления" },
  { id: "actions", title: "Сценарии" },
  { id: "audit", title: "Журнал" },
];

const emptyStatus: ControlCenterStatus = {
  backend_online: false,
  database_connected: false,
  total_users: 0,
  active_users: 0,
  blocked_users: 0,
  notifications_today: 0,
  publications_count: 0,
  problems_count: 0,
  scenarios_count: 0,
  authorities_count: 0,
  regions_count: 0,
  maintenance_mode: false,
  readonly_mode: false,
  banner_enabled: false,
  ai_status: "",
  push_status: "",
  scheduler_status: "",
  frontend_version: "",
  backend_version: "",
};

function boolText(value: boolean) {
  return value ? "включено" : "выключено";
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
      {label}
      {children}
    </label>
  );
}

function inputClass() {
  return "h-11 rounded-2xl border border-slate-200 bg-white px-4 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:border-white/10 dark:bg-white/10 dark:text-white";
}

function textareaClass() {
  return "min-h-24 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 dark:border-white/10 dark:bg-white/10 dark:text-white";
}

function PrimaryAction({ children, onClick, type = "button" }: { children: React.ReactNode; onClick?: () => void; type?: "button" | "submit" }) {
  return (
    <button
      type={type}
      onClick={onClick}
      className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl bg-blue-600 px-5 text-sm font-bold text-white shadow-lg shadow-blue-600/20 transition hover:-translate-y-0.5 hover:bg-blue-700 active:translate-y-0"
    >
      {children}
    </button>
  );
}

function SecondaryAction({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 text-sm font-bold text-slate-800 transition hover:-translate-y-0.5 hover:border-blue-200 hover:text-blue-700 dark:border-white/10 dark:bg-white/10 dark:text-white"
    >
      {children}
    </button>
  );
}

function StatCard({ label, value, tone = "default" }: { label: string; value: string | number; tone?: "default" | "good" | "warn" }) {
  const toneClass = tone === "good"
    ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200"
    : tone === "warn"
      ? "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-200"
      : "bg-slate-50 text-slate-800 dark:bg-white/10 dark:text-white";
  return (
    <div className={`rounded-3xl p-4 ${toneClass}`}>
      <div className="text-xs font-semibold uppercase tracking-[0.12em] opacity-70">{label}</div>
      <div className="mt-2 text-2xl font-black">{value}</div>
    </div>
  );
}

function UnlockPane({ onUnlock }: { onUnlock: (password: string) => Promise<void> }) {
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onUnlock(password);
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Доступ запрещён");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto grid max-w-md gap-5 rounded-[32px] border border-slate-200 bg-white p-6 shadow-2xl shadow-slate-900/10 dark:border-white/10 dark:bg-slate-950">
      <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-blue-50 text-blue-600 dark:bg-blue-500/10">
        <KeyRound size={26} />
      </div>
      <div>
        <h2 className="text-2xl font-black text-slate-950 dark:text-white">Центр управления платформой</h2>
        <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
          Доступ открыт только владельцу проекта. Команда в консоли показывает окно, но пароль проверяется сервером.
        </p>
      </div>
      <Field label="Пароль доступа">
        <input
          className={inputClass()}
          type="password"
          autoFocus
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Введите пароль"
        />
      </Field>
      {error && <div className="rounded-2xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-700 dark:bg-red-500/10 dark:text-red-200">{error}</div>}
      <PrimaryAction type="submit">
        <Lock size={18} />
        {busy ? "Проверяем..." : "Открыть"}
      </PrimaryAction>
    </form>
  );
}

function StatusTab({ statusData }: { statusData: ControlCenterStatus }) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <StatCard label="Backend" value={statusData.backend_online ? "online" : "offline"} tone={statusData.backend_online ? "good" : "warn"} />
      <StatCard label="База данных" value={statusData.database_connected ? "ok" : "error"} tone={statusData.database_connected ? "good" : "warn"} />
      <StatCard label="Пользователи" value={statusData.total_users} />
      <StatCard label="Активные" value={statusData.active_users} tone="good" />
      <StatCard label="Заблокированные" value={statusData.blocked_users} tone={statusData.blocked_users ? "warn" : "default"} />
      <StatCard label="Уведомления сегодня" value={statusData.notifications_today} />
      <StatCard label="Публикации" value={statusData.publications_count} />
      <StatCard label="Проблемы" value={statusData.problems_count} />
      <StatCard label="Сценарии" value={statusData.scenarios_count} />
      <StatCard label="Учреждения" value={statusData.authorities_count} />
      <StatCard label="Регионы" value={statusData.regions_count} />
      <StatCard label="Push" value={statusData.push_status || "unknown"} />
      <div className="rounded-3xl border border-slate-200 p-4 dark:border-white/10 md:col-span-3">
        <div className="grid gap-3 text-sm text-slate-600 dark:text-slate-300 md:grid-cols-3">
          <div>Обслуживание: <b>{boolText(statusData.maintenance_mode)}</b></div>
          <div>Только чтение: <b>{boolText(statusData.readonly_mode)}</b></div>
          <div>Баннер: <b>{boolText(statusData.banner_enabled)}</b></div>
          <div>AI: <b>{statusData.ai_status}</b></div>
          <div>Scheduler: <b>{statusData.scheduler_status}</b></div>
          <div>Версия API: <b>{statusData.backend_version}</b></div>
        </div>
      </div>
    </div>
  );
}

function ControlCenterBody({
  token,
  statusData,
  auditLogs,
  loadStatus,
  loadAudit,
}: {
  token: string;
  statusData: ControlCenterStatus;
  auditLogs: ControlCenterAuditLog[];
  loadStatus: () => Promise<void>;
  loadAudit: () => Promise<void>;
}) {
  const { systemState, refreshSystemState } = useStore();
  const [tab, setTab] = useState<Tab>("status");
  const [message, setMessage] = useState("");
  const [maintenance, setMaintenance] = useState(systemState.maintenance);
  const [readonly, setReadonly] = useState(systemState.readonly);
  const [banner, setBanner] = useState(systemState.banner);
  const [featureFlags, setFeatureFlags] = useState(systemState.featureFlags);
  const [branding, setBranding] = useState(systemState.branding);
  const [broadcast, setBroadcast] = useState({
    title: "Важное уведомление",
    description: "",
    notification_type: "system",
    route: "/notifications",
    audience: "test_users",
    region: "",
    confirm_all_users: false,
  });

  useEffect(() => {
    setMaintenance(systemState.maintenance);
    setReadonly(systemState.readonly);
    setBanner(systemState.banner);
    setFeatureFlags(systemState.featureFlags);
    setBranding(systemState.branding);
  }, [systemState]);

  async function afterAction(doneMessage: string) {
    setMessage(doneMessage);
    await refreshSystemState();
    await loadStatus();
    await loadAudit();
  }

  async function saveMaintenance() {
    await apiClient.updateControlMaintenance<SystemState>(token, maintenance);
    await apiClient.updateControlReadonly<SystemState>(token, readonly);
    await afterAction("Режимы платформы обновлены");
  }

  async function saveBanner() {
    await apiClient.updateControlBanner<SystemState>(token, banner);
    await afterAction("Системный баннер обновлён");
  }

  async function saveFlags() {
    await apiClient.updateControlFeatureFlags<SystemState>(token, featureFlags);
    await afterAction("Функции обновлены");
  }

  async function saveBranding() {
    await apiClient.updateControlBranding<SystemState>(token, branding);
    await afterAction("Брендинг обновлён");
  }

  async function sendBroadcast() {
    const result = await apiClient.sendControlBroadcast<Record<string, unknown>>(token, broadcast);
    await afterAction(`Уведомления созданы: ${String(result.created ?? 0)} из ${String(result.targeted ?? 0)}`);
  }

  async function runAction(action: string) {
    await apiClient.runControlAction<Record<string, unknown>>(token, action);
    await afterAction("Системный сценарий выполнен");
  }

  const featureEntries = useMemo(() => Object.entries(featureFlags), [featureFlags]);

  return (
    <div className="grid h-full grid-rows-[auto_1fr] overflow-hidden">
      <div className="flex gap-2 overflow-x-auto border-b border-slate-200 px-6 py-4 dark:border-white/10">
        {TABS.map(item => (
          <button
            key={item.id}
            type="button"
            onClick={() => setTab(item.id)}
            className={`h-10 shrink-0 rounded-2xl px-4 text-sm font-bold transition ${tab === item.id ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-white/10 dark:text-slate-200"}`}
          >
            {item.title}
          </button>
        ))}
      </div>
      <div className="overflow-y-auto p-6">
        {message && (
          <div className="mb-4 flex items-center gap-3 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
            <CheckCircle2 size={18} />
            {message}
          </div>
        )}

        {tab === "status" && <StatusTab statusData={statusData} />}

        {tab === "maintenance" && (
          <div className="grid gap-5 lg:grid-cols-2">
            <div className="grid gap-4 rounded-3xl border border-slate-200 p-5 dark:border-white/10">
              <h3 className="text-xl font-black">Техническое обслуживание</h3>
              <label className="flex items-center gap-3 text-sm font-bold">
                <input type="checkbox" checked={maintenance.enabled} onChange={event => setMaintenance(prev => ({ ...prev, enabled: event.target.checked }))} />
                Включить режим обслуживания
              </label>
              <Field label="Заголовок">
                <input className={inputClass()} value={maintenance.title} onChange={event => setMaintenance(prev => ({ ...prev, title: event.target.value }))} />
              </Field>
              <Field label="Сообщение">
                <textarea className={textareaClass()} value={maintenance.message} onChange={event => setMaintenance(prev => ({ ...prev, message: event.target.value }))} />
              </Field>
              <Field label="Уровень">
                <select className={inputClass()} value={maintenance.level} onChange={event => setMaintenance(prev => ({ ...prev, level: event.target.value }))}>
                  <option value="notice">Информация</option>
                  <option value="warning">Предупреждение</option>
                  <option value="full_lock">Полная блокировка</option>
                </select>
              </Field>
            </div>
            <div className="grid gap-4 rounded-3xl border border-slate-200 p-5 dark:border-white/10">
              <h3 className="text-xl font-black">Режим только чтения</h3>
              <label className="flex items-center gap-3 text-sm font-bold">
                <input type="checkbox" checked={readonly.enabled} onChange={event => setReadonly(prev => ({ ...prev, enabled: event.target.checked }))} />
                Запретить изменения данных
              </label>
              <Field label="Сообщение">
                <textarea className={textareaClass()} value={readonly.message} onChange={event => setReadonly(prev => ({ ...prev, message: event.target.value }))} />
              </Field>
              <PrimaryAction onClick={saveMaintenance}>
                <Save size={18} />
                Сохранить режимы
              </PrimaryAction>
            </div>
          </div>
        )}

        {tab === "banner" && (
          <div className="grid max-w-3xl gap-4 rounded-3xl border border-slate-200 p-5 dark:border-white/10">
            <h3 className="text-xl font-black">Системный баннер</h3>
            <label className="flex items-center gap-3 text-sm font-bold">
              <input type="checkbox" checked={banner.enabled} onChange={event => setBanner(prev => ({ ...prev, enabled: event.target.checked }))} />
              Показывать пользователям
            </label>
            <Field label="Текст">
              <textarea className={textareaClass()} value={banner.text} onChange={event => setBanner(prev => ({ ...prev, text: event.target.value }))} />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Тип">
                <select className={inputClass()} value={banner.type} onChange={event => setBanner(prev => ({ ...prev, type: event.target.value }))}>
                  <option value="info">Информация</option>
                  <option value="success">Успех</option>
                  <option value="warning">Предупреждение</option>
                  <option value="danger">Важно</option>
                </select>
              </Field>
              <Field label="Аудитория">
                <select className={inputClass()} value={banner.audience} onChange={event => setBanner(prev => ({ ...prev, audience: event.target.value }))}>
                  <option value="all">Все</option>
                  <option value="citizens">Граждане</option>
                  <option value="staff">Редакция и админы</option>
                </select>
              </Field>
              <Field label="Подпись ссылки">
                <input className={inputClass()} value={banner.linkLabel} onChange={event => setBanner(prev => ({ ...prev, linkLabel: event.target.value }))} />
              </Field>
              <Field label="URL ссылки">
                <input className={inputClass()} value={banner.linkUrl} onChange={event => setBanner(prev => ({ ...prev, linkUrl: event.target.value }))} />
              </Field>
            </div>
            <PrimaryAction onClick={saveBanner}>
              <Megaphone size={18} />
              Сохранить баннер
            </PrimaryAction>
          </div>
        )}

        {tab === "flags" && (
          <div className="grid max-w-3xl gap-3">
            <h3 className="text-xl font-black">Функции платформы</h3>
            {featureEntries.map(([key, value]) => (
              <label key={key} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold dark:border-white/10 dark:bg-white/5">
                <span>{key}</span>
                <input type="checkbox" checked={value} onChange={event => setFeatureFlags(prev => ({ ...prev, [key]: event.target.checked }))} />
              </label>
            ))}
            <PrimaryAction onClick={saveFlags}>
              <Settings2 size={18} />
              Сохранить функции
            </PrimaryAction>
          </div>
        )}

        {tab === "branding" && (
          <div className="grid max-w-3xl gap-4 rounded-3xl border border-slate-200 p-5 dark:border-white/10">
            <h3 className="text-xl font-black">Брендинг</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Название">
                <input className={inputClass()} value={branding.appName} onChange={event => setBranding(prev => ({ ...prev, appName: event.target.value }))} />
              </Field>
              <Field label="Короткое название">
                <input className={inputClass()} value={branding.shortName} onChange={event => setBranding(prev => ({ ...prev, shortName: event.target.value }))} />
              </Field>
              <Field label="Текст логотипа">
                <input className={inputClass()} value={branding.logoText} onChange={event => setBranding(prev => ({ ...prev, logoText: event.target.value }))} />
              </Field>
              <Field label="Акцентный цвет">
                <input className={inputClass()} value={branding.accentColor} onChange={event => setBranding(prev => ({ ...prev, accentColor: event.target.value }))} />
              </Field>
              <Field label="URL логотипа">
                <input className={inputClass()} value={branding.logoUrl} onChange={event => setBranding(prev => ({ ...prev, logoUrl: event.target.value }))} />
              </Field>
              <Field label="Заголовок главной">
                <input className={inputClass()} value={branding.homeTitle} onChange={event => setBranding(prev => ({ ...prev, homeTitle: event.target.value }))} />
              </Field>
            </div>
            <Field label="Подзаголовок главной">
              <textarea className={textareaClass()} value={branding.homeSubtitle} onChange={event => setBranding(prev => ({ ...prev, homeSubtitle: event.target.value }))} />
            </Field>
            <PrimaryAction onClick={saveBranding}>
              <Shield size={18} />
              Сохранить брендинг
            </PrimaryAction>
          </div>
        )}

        {tab === "broadcast" && (
          <div className="grid max-w-3xl gap-4 rounded-3xl border border-slate-200 p-5 dark:border-white/10">
            <h3 className="text-xl font-black">Отправить уведомление</h3>
            <Field label="Заголовок">
              <input className={inputClass()} value={broadcast.title} onChange={event => setBroadcast(prev => ({ ...prev, title: event.target.value }))} />
            </Field>
            <Field label="Текст">
              <textarea className={textareaClass()} value={broadcast.description} onChange={event => setBroadcast(prev => ({ ...prev, description: event.target.value }))} />
            </Field>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Аудитория">
                <select className={inputClass()} value={broadcast.audience} onChange={event => setBroadcast(prev => ({ ...prev, audience: event.target.value }))}>
                  <option value="test_users">Тестовые пользователи</option>
                  <option value="citizens">Граждане</option>
                  <option value="editors">Редакторы</option>
                  <option value="admins">Администраторы</option>
                  <option value="region">Регион</option>
                  <option value="all">Все пользователи</option>
                </select>
              </Field>
              <Field label="Регион">
                <input className={inputClass()} value={broadcast.region} onChange={event => setBroadcast(prev => ({ ...prev, region: event.target.value }))} />
              </Field>
              <Field label="Маршрут">
                <input className={inputClass()} value={broadcast.route} onChange={event => setBroadcast(prev => ({ ...prev, route: event.target.value }))} />
              </Field>
              <label className="flex items-center gap-3 pt-8 text-sm font-bold">
                <input type="checkbox" checked={broadcast.confirm_all_users} onChange={event => setBroadcast(prev => ({ ...prev, confirm_all_users: event.target.checked }))} />
                Подтвердить отправку всем
              </label>
            </div>
            <PrimaryAction onClick={sendBroadcast}>
              <Bell size={18} />
              Отправить
            </PrimaryAction>
          </div>
        )}

        {tab === "actions" && (
          <div className="grid gap-4 md:grid-cols-3">
            <button type="button" onClick={() => runAction("create-test-notifications")} className="rounded-3xl border border-slate-200 p-5 text-left transition hover:-translate-y-1 hover:shadow-xl dark:border-white/10">
              <Bell className="text-blue-600" />
              <div className="mt-4 text-lg font-black">Проверочные уведомления</div>
              <p className="mt-2 text-sm text-slate-500">Создать in-app уведомления для тестовых аккаунтов.</p>
            </button>
            <button type="button" onClick={() => runAction("prepare-presentation-state")} className="rounded-3xl border border-slate-200 p-5 text-left transition hover:-translate-y-1 hover:shadow-xl dark:border-white/10">
              <Server className="text-blue-600" />
              <div className="mt-4 text-lg font-black">Состояние для показа</div>
              <p className="mt-2 text-sm text-slate-500">Включить спокойный информационный баннер.</p>
            </button>
            <button type="button" onClick={() => runAction("reset-transient-system-state")} className="rounded-3xl border border-slate-200 p-5 text-left transition hover:-translate-y-1 hover:shadow-xl dark:border-white/10">
              <RotateCcw className="text-blue-600" />
              <div className="mt-4 text-lg font-black">Сброс временных режимов</div>
              <p className="mt-2 text-sm text-slate-500">Выключить обслуживание, readonly и баннер.</p>
            </button>
          </div>
        )}

        {tab === "audit" && (
          <div className="grid gap-3">
            <div className="flex justify-end">
              <SecondaryAction onClick={loadAudit}>
                <RotateCcw size={16} />
                Обновить
              </SecondaryAction>
            </div>
            {auditLogs.map(row => (
              <div key={row.id} className="rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-white/10 dark:bg-white/5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <b>{row.action}</b>
                  <span className="text-slate-500">{new Date(row.created_at).toLocaleString("ru-RU")}</span>
                </div>
                <div className="mt-2 text-slate-500">{row.entity_type || "system"} {row.entity_id ? `#${row.entity_id}` : ""} · {row.status} · {row.ip_address}</div>
              </div>
            ))}
            {!auditLogs.length && <div className="rounded-3xl border border-dashed border-slate-200 p-8 text-center text-slate-500 dark:border-white/10">Журнал пока пуст.</div>}
          </div>
        )}
      </div>
    </div>
  );
}

export function ControlCenter() {
  const { controlCenterOpen, openControlCenter, closeControlCenter } = useStore();
  const [token, setToken] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [statusData, setStatusData] = useState<ControlCenterStatus>(emptyStatus);
  const [auditLogs, setAuditLogs] = useState<ControlCenterAuditLog[]>([]);

  useEffect(() => {
    window.belpomoshnikControl = () => openControlCenter();
    return () => {
      if (window.belpomoshnikControl) delete window.belpomoshnikControl;
    };
  }, [openControlCenter]);

  async function loadStatus(nextToken = token) {
    if (!nextToken) return;
    const result = await apiClient.getControlCenterStatus<ControlCenterStatus>(nextToken);
    setStatusData(result);
  }

  async function loadAudit(nextToken = token) {
    if (!nextToken) return;
    const result = await apiClient.getControlAuditLog<ControlCenterAuditLog[]>(nextToken);
    setAuditLogs(result);
  }

  async function unlock(password: string) {
    const result = await apiClient.unlockControlCenter<{ control_token: string; expires_at: string; ttl_minutes: number }>(password);
    setToken(result.control_token);
    setExpiresAt(result.expires_at);
    await loadStatus(result.control_token);
    await loadAudit(result.control_token);
  }

  async function lockAndClose() {
    if (token) {
      try { await apiClient.lockControlCenter(token); } catch { /* token might be expired */ }
    }
    setToken("");
    setExpiresAt("");
    closeControlCenter();
  }

  if (!controlCenterOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xl">
      <div className="grid h-[min(860px,94dvh)] w-[min(1120px,96vw)] grid-rows-[auto_1fr] overflow-hidden rounded-[36px] border border-white/20 bg-slate-50 text-slate-950 shadow-2xl dark:bg-slate-950 dark:text-white">
        <header className="flex items-center justify-between gap-4 border-b border-slate-200 px-6 py-5 dark:border-white/10">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-600 text-white">
                <Shield size={22} />
              </div>
              <div>
                <h1 className="text-xl font-black">Центр управления платформой</h1>
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                  {token ? `Сессия активна${expiresAt ? ` до ${new Date(expiresAt).toLocaleTimeString("ru-RU")}` : ""}` : "Требуется пароль"}
                </p>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={lockAndClose}
            className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-slate-700 shadow-sm transition hover:bg-red-50 hover:text-red-600 dark:bg-white/10 dark:text-white"
            aria-label="Закрыть центр управления"
          >
            <X size={22} />
          </button>
        </header>
        <div className="min-h-0 overflow-hidden">
          {token ? (
            <ControlCenterBody
              token={token}
              statusData={statusData}
              auditLogs={auditLogs}
              loadStatus={() => loadStatus()}
              loadAudit={() => loadAudit()}
            />
          ) : (
            <div className="flex h-full items-center justify-center p-6">
              <UnlockPane onUnlock={unlock} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function SystemBanner() {
  const { systemState } = useStore();
  const banner = systemState.banner;
  const storageKey = `belpomoshnik.banner.dismissed.${banner.version}`;
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem(storageKey) === "1"; } catch { return false; }
  });

  useEffect(() => {
    try { setDismissed(localStorage.getItem(storageKey) === "1"); } catch { setDismissed(false); }
  }, [storageKey]);

  if (!banner.enabled || !banner.text || dismissed) return null;

  const tone = banner.type === "danger"
    ? "bg-red-600 text-white"
    : banner.type === "warning"
      ? "bg-amber-500 text-white"
      : banner.type === "success"
        ? "bg-emerald-600 text-white"
        : "bg-blue-600 text-white";

  return (
    <div className={`fixed left-4 right-4 top-4 z-[90] mx-auto flex max-w-5xl items-center justify-between gap-4 rounded-3xl px-5 py-3 text-sm font-bold shadow-2xl shadow-slate-900/20 ${tone}`}>
      <div className="flex items-center gap-3">
        <Megaphone size={18} />
        <span>{banner.text}</span>
      </div>
      <div className="flex items-center gap-3">
        {banner.linkUrl && (
          <a className="underline underline-offset-4" href={banner.linkUrl} target="_blank" rel="noreferrer">
            {banner.linkLabel || "Подробнее"}
          </a>
        )}
        {banner.dismissible && (
          <button
            type="button"
            onClick={() => {
              try { localStorage.setItem(storageKey, "1"); } catch { /* ignore */ }
              setDismissed(true);
            }}
            className="rounded-full bg-white/20 p-1"
            aria-label="Скрыть баннер"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}

export function MaintenanceScreen() {
  const { systemState, refreshSystemState } = useStore();
  const maintenance = systemState.maintenance;
  if (!maintenance.enabled || maintenance.level !== "full_lock") return null;
  return (
    <div className="fixed inset-0 z-[180] flex items-center justify-center bg-slate-950/85 p-6 backdrop-blur-xl">
      <div className="max-w-lg rounded-[36px] bg-white p-8 text-center shadow-2xl dark:bg-slate-950 dark:text-white">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-amber-50 text-amber-600 dark:bg-amber-500/10">
          <AlertTriangle size={30} />
        </div>
        <h2 className="mt-6 text-3xl font-black">{maintenance.title || "Техническое обслуживание"}</h2>
        <p className="mt-3 text-slate-500 dark:text-slate-400">
          {maintenance.message || "Сервис временно недоступен. Попробуйте открыть приложение немного позже."}
        </p>
        {maintenance.until && <p className="mt-3 text-sm font-semibold text-slate-400">Ориентировочно до: {maintenance.until}</p>}
        <button
          type="button"
          onClick={refreshSystemState}
          className="mt-6 inline-flex h-12 items-center justify-center rounded-2xl bg-blue-600 px-6 font-bold text-white"
        >
          Проверить снова
        </button>
      </div>
    </div>
  );
}
