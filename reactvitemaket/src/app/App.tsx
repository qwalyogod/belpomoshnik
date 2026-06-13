import { useEffect, useMemo, useRef, useState } from "react";
import { Outlet, useNavigate, useLocation, RouterProvider } from "react-router";
import { router } from "./routes";
import { motion, AnimatePresence } from "motion/react";
import {
  Sun, Moon, Search, FileText, Home, Bell, User, Shield, Wallet, Heart, Briefcase, Hammer,
  ArrowRight, ChevronRight, Check, Lock, AlertCircle, CalendarClock, MapPin, Sparkles,
  Plus, ScanLine, EyeOff, Building2, Clock, Bookmark, ArrowUpRight, Settings,
  Users, BookOpen, LayoutGrid, Baby, ChevronLeft, X, LogOut, UserPlus, Newspaper,
} from "lucide-react";
import { Logo, Pill, Card, PrimaryButton, GhostButton, UserAvatarCircle } from "./components/belp-ui";
import { AppStoreProvider, useStore, readAvatarForUser } from "./data/store";
import { buildReminders } from "./services/reminders";
import { applyAccessibilitySettings } from "./services/a11y";
import { scrollContentToTop } from "./services/scroll";
import { AdminWindowMount } from "./components/admin-window";
import { ControlCenter, MaintenanceScreen, SystemBanner } from "./components/control-center/ControlCenter";
import { GuestGuardBridge } from "./components/GuestGuardBridge";
import { ConnectionBanner } from "./components/ConnectionBanner";
import { CATEGORIES } from "./data/mock";
import type { SystemState } from "./data/types";

const catLabelApp = (id: string) => CATEGORIES.find(c => c.id === id)?.name ?? id;
import {
  ScenarioDetail, MySituationDetail, SettingsPage, LearningPage,
  SearchOverlay, DocumentEditModal, GuestGuardModal, AssistantPanel,
} from "./components/extra-screens";

/* ============================================================
   SHARED STATE — current "page" in the app
   ============================================================ */
type Page =
  | "home" | "situations" | "situation" | "documents" | "legal" | "notifications"
  | "profile" | "catalog" | "scenario" | "mysituation" | "settings" | "learning" | "admin" | "finance" | "news" | "sources";

/* Top-level (корневые) маршруты — здесь показываем нижнее меню MobileNav
   и НЕ показываем back-кнопку. Это «главные» разделы приложения, в которые
   пользователь возвращается тапом по таб-бару. */
const TOP_LEVEL_ROUTES = new Set<string>([
  "/", "/catalog", "/scenarios", "/situations", "/documents",
  "/finance", "/news", "/notifications", "/profile", "/about",
  "/onboarding", "/learning", "/problems",
]);

/* Auth-страницы: ни MobileShell, ни MobileNav, ни back-кнопка. */
const AUTH_ROUTES = new Set<string>(["/login", "/register", "/welcome"]);

/* Hidden nav: админ/редактор — это служебные разделы, в таб-баре не нужны. */
const NAV_HIDDEN_ROUTES = new Set<string>(["/admin", "/editor", "/extremist"]);

/** Роль имеет доступ к служебным разделам (редактор/админ).
 *  Поддерживаем оба варианта значений: новые ("content_editor"/"platform_admin")
 *  и legacy ("editor"/"admin") из старых quickAccounts в localStorage. */
function isStaffRole(role: string | undefined | null): boolean {
  return role === "content_editor" || role === "platform_admin" || role === "editor" || role === "admin";
}

function isAdminRole(role: string | undefined | null): boolean {
  return role === "platform_admin" || role === "admin";
}

function isTopLevelRoute(pathname: string): boolean {
  // Служебные / auth / скрытые разделы — не top-level.
  if (isAuthPage(pathname) || isNavHidden(pathname)) return false;
  // Любой /scenarios/:id, /situations/:id, /problem-detail/:id, /law-detail/:id, /news/:id — DETAIL.
  if (/^\/(scenarios|situations|problem-detail|law-detail|news)\/[^/]+/.test(pathname)) return false;
  // Точное совпадение с top-level маршрутами.
  if (TOP_LEVEL_ROUTES.has(pathname)) return true;
  return false;
}

function isAuthPage(pathname: string): boolean {
  return AUTH_ROUTES.has(pathname);
}

function isNavHidden(pathname: string): boolean {
  if (NAV_HIDDEN_ROUTES.has(pathname)) return true;
  return Array.from(NAV_HIDDEN_ROUTES).some((route) => pathname.startsWith(`${route}/`));
}

/* ============================================================
   MOBILE APP
   ============================================================ */
export function MobileShell({ dark, setDark }: { dark: boolean; setDark: (d: boolean) => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const page = location.pathname.split("/")[1] || "home";
  const { role } = useStore();
  const [guardOpen, setGuardOpen] = useState(false);
  const [docModal, setDocModal] = useState<{ open: boolean; id: string | null }>({ open: false, id: null });

  const protectedGuard = () => {
    if (role === "guest") {
      setGuardOpen(true);
      return false;
    }
    return true;
  };

  const showBottomNav = isTopLevelRoute(location.pathname);
  const showMobileShell = !isAuthPage(location.pathname);

  // Цвет фона shell-а для fade-gradient. Зависит от темы:
  //   light: #F6F7FB (светло-серый)
  //   dark:  #07080C (почти-чёрный)
  const fadeColor = dark ? "#07080C" : "#F6F7FB";

  if (!showMobileShell) {
    // /login, /register, /welcome — без MobileShell, без MobileNav, без MobileTopBar.
    return (
      <div className="relative min-h-[100dvh] w-full overflow-x-hidden bg-[#F6F7FB] dark:bg-[#07080C]">
        <Outlet context={{ dark, setDark, protectedGuard, onAddDoc: () => { if (protectedGuard()) setDocModal({ open: true, id: null }); }, onEditDoc: (id: string) => { if (protectedGuard()) setDocModal({ open: true, id }); } }} />
      </div>
    );
  }

  return (
    // На mobile скроллим страницу нативно (не вложенным overflow-auto) — это
    // совпадает с поведением iOS-нативных приложений и решает проблему «главная
    // не скроллится у гостя». overflow-x-hidden защищает от горизонтального
    // дрейфа при появлении боковых оверлеев. min-h-[100dvh] даёт странице
    // высоту viewport и плюс естественный overflow.
    <div
      className="relative min-h-[100dvh] w-full overflow-x-hidden bg-[#F6F7FB] dark:bg-[#07080C]"
      style={{
        // Fallback-значения CSS-переменных до рендера header/nav.
        // Сами header и nav переопределят их в своих style (см. MobileBrandBar
        // и MobileNav). Это гарантирует, что контент сразу получит правильный
        // padding, даже если header/nav ещё не замаунтились.
        ["--belp-mobile-header-h" as string]: "calc(3.85rem + env(safe-area-inset-top))",
        ["--belp-mobile-nav-h" as string]: "calc(7rem + env(safe-area-inset-bottom))",
      }}
    >
      {/* P12: MobileBrandBar — fixed top-0 (НЕ sticky), потому что iOS
          WKWebView ломает position: sticky когда любой предок имеет
          overflow-x-hidden (что у нас есть для защиты от горизонтального
          дрейфа). Поэтому контенту ниже нужен явный padding-top.
          Высота берётся из CSS-переменной --belp-mobile-header-h, которую
          выставляет сам header (см. MobileBrandBar). */}
      <MobileBrandBar />
      <div
        style={{
          paddingTop: "var(--belp-mobile-header-h, calc(3.85rem + env(safe-area-inset-top)))",
          paddingBottom: "var(--belp-mobile-nav-h, calc(7rem + env(safe-area-inset-bottom)))",
        }}
      >
        {/* P12: ускорили переход между страницами и убрали initial opacity 0 —
            на mobile это давало визуальный «флэш пустоты» при переходе на
            /settings и /law-detail. Появление мгновенное, y-сдвиг лёгкий. */}
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={location.pathname}
            initial={{ y: 6 }}
            animate={{ y: 0 }}
            exit={{ y: -4, opacity: 0 }}
            transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
          >
            <Outlet context={{ dark, setDark, protectedGuard, onAddDoc: () => { if (protectedGuard()) setDocModal({ open: true, id: null }); }, onEditDoc: (id: string) => { if (protectedGuard()) setDocModal({ open: true, id }); } }} />
          </motion.div>
        </AnimatePresence>
      </div>
      {showBottomNav && <MobileBottomFade color={fadeColor} />}
      {showBottomNav && <MobileNav active={page as Page} onChange={(p) => { if (p === page) scrollContentToTop("smooth"); else navigate(`/${p === 'home' ? '' : p}`); }} />}
      <DocumentEditModal open={docModal.open} editingId={docModal.id} onClose={() => setDocModal({ open: false, id: null })} />
      <GuestGuardModal
        open={guardOpen}
        onClose={() => setGuardOpen(false)}
        onSignIn={() => { setGuardOpen(false); navigate("/login"); }}
        onRegister={() => { setGuardOpen(false); navigate("/register"); }}
      />
      <ConnectionBanner />
    </div>
  );
}

function MobileBottomFade({ color }: { color: string }) {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-x-0 bottom-0 z-20"
      style={{
        height: "calc(var(--belp-mobile-nav-h, calc(7rem + env(safe-area-inset-bottom))) + 5.5rem)",
        background: `linear-gradient(to bottom, ${color}00 0%, ${color}26 18%, ${color}a8 48%, ${color}f2 66%, ${color} 100%)`,
      }}
    />
  );
}

// v0.10: ВСЁ, что нужно для mobile header (back/title/bell), теперь
// рендерится в MobileBrandBar внутри shell. MobileTopBar сохранён как
// no-op для обратной совместимости (страницы его ещё вызывают), но ничего
// не рисует. Удалим все его вызовы в следующем проходе.
export function MobileTopBar(_props: { title: string; onBack?: () => void; right?: React.ReactNode }) {
  return null;
}

/* v0.9: «бренд-бар» — логотип + название + кнопка уведомлений.
   Рендерится внутри MobileShell один раз, на каждой странице.
   На главной показывается полный (лого+название+уведомления),
   на остальных — только кнопка уведомлений. */
/* v0.10: единый mobile header. На главной (/, /onboarding, /welcome) —
   лого+имя «Белпомощник», на остальных — back+title раздела, всегда —
   колокольчик справа. Title берётся из pathname (fallback — сегмент URL). */
const MOBILE_TITLES: Record<string, string> = {
  "/": "Белпомощник",
  "/onboarding": "Добро пожаловать",
  "/welcome": "Добро пожаловать",
  "/catalog": "Каталог помощи",
  "/scenarios": "Жизненные сценарии",
  "/situations": "Мои ситуации",
  "/documents": "Мои документы",
  "/finance": "ЖКХ и налоги",
  "/news": "Новости",
  "/notifications": "Уведомления",
  "/profile": "Профиль",
  "/settings": "Настройки",
  "/learning": "Обучение",
  "/about": "О приложении",
  "/login": "Войти",
  "/register": "Регистрация",
  "/admin": "Админ-панель",
  "/editor": "Редактор контента",
  "/problems": "Проблемы",
  "/law-detail": "Закон-апдейт",
  "/problem-detail": "Проблема",
  "/extremist": "Экстремистский контент",
};

function mobileTitleFromPath(pathname: string): string {
  if (MOBILE_TITLES[pathname]) return MOBILE_TITLES[pathname];
  // для динамических: /situations/:id, /scenarios/:id, /law-detail/:id
  for (const key of Object.keys(MOBILE_TITLES)) {
    if (pathname.startsWith(`${key}/`)) return MOBILE_TITLES[key];
  }
  return "Белпомощник";
}

export function MobileBrandBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { role } = useStore();
  // Top-level (главные разделы: /, /news, /profile, /catalog...) — НЕ back,
  // показываем логотип. Detail (/scenarios/:id, /situations/:id,
  // /problem-detail/:id, /law-detail/:id) — back-кнопка.
  const isTopLevel = isTopLevelRoute(location.pathname);
  const title = mobileTitleFromPath(location.pathname);
  return (
    <div
      className="fixed inset-x-0 top-0 z-40 flex items-center justify-between gap-2 border-b border-black/[0.04] bg-[#F6F7FB]/85 px-4 pb-3 backdrop-blur-md dark:border-white/[0.04] dark:bg-[#07080C]/85"
      style={{
        paddingTop: "calc(0.75rem + env(safe-area-inset-top))",
        // Высота хедера = padding-top (12px + safe-area) + h-10 (40px)
        // + pb-3 (12px) + border (1px) = ~3.85rem + safe-area.
        // CSS-переменная для синхронизации padding-top контента
        // в MobileShell (см. ниже).
        ["--belp-mobile-header-h" as string]: "calc(3.85rem + env(safe-area-inset-top))",
      }}
    >
      {/* Левая зона: back (на detail) ИЛИ логотип (на top-level) */}
      {isTopLevel ? (
        <button
          onClick={() => navigate("/")}
          aria-label="На главную"
          className="shrink-0"
        >
          <Logo size={26} />
        </button>
      ) : (
        <div className="flex w-10 shrink-0 items-center">
          <button
            onClick={() => navigate(-1)}
            aria-label="Назад"
            className="grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"
          >
            <ChevronLeft size={18} className="text-black dark:text-white" />
          </button>
        </div>
      )}

      {/* Центр: title на всех страницах. На главной — "Белпомощник",
          на остальных — название раздела (Каталог помощи, Профиль и т.д.). */}
      <div className="min-w-0 flex-1 text-center">
        <div className="truncate text-[15px] font-semibold tracking-tight text-black dark:text-white">
          {title}
        </div>
      </div>

      {/* Правая зона: гость видит «Войти» (настройки/уведомления ему недоступны),
          остальные — settings + bell. */}
      <div className="flex shrink-0 items-center justify-end gap-1.5">
        {role === "guest" ? (
          <button
            onClick={() => navigate("/login")}
            className="grid h-10 place-items-center rounded-full bg-[#0056FF] px-4 text-[13px] font-medium tracking-tight text-white shadow-sm"
          >
            Войти
          </button>
        ) : (
          <>
            <button
              onClick={() => navigate("/settings")}
              aria-label="Настройки"
              className="grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"
            >
              <Settings size={17} className="text-black dark:text-white" />
            </button>
            <button
              onClick={() => navigate("/notifications")}
              aria-label="Уведомления"
              className="relative grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"
            >
              <Bell size={17} className="text-black dark:text-white" />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// Mobile «зажми Профиль» → переключение пользователей (как user-switcher на desktop).
function MobileUserSwitcher({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const { currentUser, quickAccounts, signInAs, signOut } = useStore();
  if (!open) return null;
  const accounts = [{ id: "guest", name: "Гость", email: "", role: "guest" as const }, ...quickAccounts];
  const choose = (id: string) => { signInAs(id); onClose(); navigate("/"); };
  return (
    <div className="fixed inset-0 z-[100] flex items-end bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <motion.div
        initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 320, damping: 32 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full rounded-t-[28px] border-t border-black/[0.06] bg-white px-4 pb-9 pt-3 dark:border-white/[0.06] dark:bg-[#0F1117]"
      >
        <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-black/15 dark:bg-white/20" />
        <div className="px-1 pb-2 text-[12px] uppercase tracking-[0.12em] text-black/40 dark:text-white/40">Сменить пользователя</div>
        <div className="space-y-1">
          {accounts.map((a) => {
            const activeAcc = a.id === "guest" ? currentUser.role === "guest" : currentUser.id === a.id;
            return (
              <button key={a.id} onClick={() => choose(a.id)} className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition-colors ${activeAcc ? "bg-[#E3E7FC] dark:bg-[#0E1A3A]" : "hover:bg-black/[0.03] dark:hover:bg-white/[0.04]"}`}>
                <UserAvatarCircle src={a.id === "guest" ? undefined : readAvatarForUser(a.id)} name={a.name} email={a.email} size={40} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[14px] tracking-tight text-black dark:text-white">{a.name}</span>
                  <span className="block truncate text-[12px] tracking-tight text-black/45 dark:text-white/45">{roleTitle(a.role)}</span>
                </span>
                {activeAcc && <Check size={16} className="text-[#0056FF] dark:text-[#7FA8FF]" />}
              </button>
            );
          })}
        </div>
        {currentUser.role !== "guest" && (
          <button onClick={() => { signOut(); onClose(); navigate("/"); }} className="mt-2 flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-red-500 transition-colors hover:bg-red-50 dark:hover:bg-red-500/10">
            <span className="grid h-10 w-10 shrink-0 place-items-center"><LogOut size={18} /></span> Выйти из аккаунта
          </button>
        )}
      </motion.div>
    </div>
  );
}

function MobileNav({ active, onChange }: { active: Page; onChange: (p: Page) => void }) {
  const { openAssistant } = React.useContext(ShellContext);
  const { role, systemState } = useStore();
  const isGuest = role === "guest";
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const holdTimer = useRef<number | undefined>(undefined);
  const held = useRef(false);

  // «Профиль»: короткий тап → переход, зажатие (450мс) → переключение пользователей.
  const profileHandlers = {
    onPointerDown: () => { held.current = false; holdTimer.current = window.setTimeout(() => { held.current = true; setSwitcherOpen(true); }, 450); },
    onPointerUp: () => { if (holdTimer.current) { clearTimeout(holdTimer.current); holdTimer.current = undefined; } if (!held.current) onChange("profile"); },
    onPointerLeave: () => { if (holdTimer.current) { clearTimeout(holdTimer.current); holdTimer.current = undefined; } },
    onContextMenu: (e: React.MouseEvent) => e.preventDefault(),
  };

  const renderTab = (t: { id: Page; i: React.ReactNode; n: string }, isProfile = false) => {
    const isActive = active === t.id;
    const handlers = isProfile ? profileHandlers : { onClick: () => onChange(t.id) };
    return (
      <button key={t.id} {...handlers} className="relative flex flex-1 select-none flex-col items-center gap-0.5 py-1.5">
        {isActive && <motion.span layoutId="mobile-nav" className="absolute inset-x-2 inset-y-0 rounded-2xl bg-[#E3E7FC] dark:bg-[#0E1A3A]" transition={{ type: "spring", stiffness: 380, damping: 30 }} />}
        <span className={`relative ${isActive ? "text-[#0056FF] dark:text-[#7FA8FF]" : "text-black/55 dark:text-white/55"}`}>{t.i}</span>
        <span className={`relative text-[10px] tracking-tight ${isActive ? "text-[#0056FF] dark:text-[#7FA8FF]" : "text-black/55 dark:text-white/55"}`}>{t.n}</span>
      </button>
    );
  };
  const leftBase: { id: Page; i: React.ReactNode; n: string }[] = [
    { id: "home", i: <Home size={20} />, n: "Главная" },
    { id: "catalog", i: <LayoutGrid size={20} />, n: "Каталог" },
  ];
  // Гость не ведёт «Мои ситуации» (нужен аккаунт) — ему показываем «Новости»;
  // залогиненному — быстрый доступ к ситуациям.
  const rightBase: { id: Page; i: React.ReactNode; n: string }[] = isGuest
    ? [
        { id: "news", i: <Newspaper size={20} />, n: "Новости" },
        { id: "profile", i: <User size={20} />, n: "Профиль" },
      ]
    : [
        { id: "situations", i: <FileText size={20} />, n: "Ситуации" },
        { id: "profile", i: <User size={20} />, n: "Профиль" },
      ];
  const left = orderNavigationItems(
    leftBase.filter((item) => isPageEnabledBySystemState(item.id, systemState)),
    systemState.navigationLayout.mobile,
  );
  const right = orderNavigationItems(
    rightBase.filter((item) => isPageEnabledBySystemState(item.id, systemState)),
    systemState.navigationLayout.mobile,
  );
  const assistantEnabled = systemState.featureFlags.assistant !== false;
  return (
    <>
      {/* Mobile-nav прибит к viewport через `fixed`, а не к shell через `absolute`,
          чтобы он оставался на месте при нативном page-scroll (когда shell
          длиннее viewport, иначе нав повисает посреди контента).
          CSS-переменная --belp-mobile-nav-h синхронизирует padding-bottom
          контента в MobileShell, чтобы последние элементы не обрезались. */}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-0 z-30 px-4 pb-4"
        style={{
          paddingBottom: "calc(1rem + env(safe-area-inset-bottom))",
          ["--belp-mobile-nav-h" as string]: "calc(7rem + env(safe-area-inset-bottom))",
        }}
      >
        <div className="pointer-events-auto relative flex items-stretch rounded-[26px] border border-black/[0.06] bg-white/95 px-2 py-2.5 shadow-[0_20px_60px_-20px_rgba(15,23,42,0.35)] backdrop-blur-xl dark:border-white/[0.08] dark:bg-[#0F1117]/95">
          {left.map((t) => renderTab(t))}
          {assistantEnabled && <div className="w-16 shrink-0" />}
          {right.map((t) => renderTab(t, t.id === "profile"))}
          {assistantEnabled && (
            <button
              onClick={openAssistant}
              aria-label="ИИ-помощник"
              className="absolute left-1/2 -top-6 grid h-16 w-16 -translate-x-1/2 place-items-center rounded-full border-4 border-[#F6F7FB] bg-[#0056FF] text-white shadow-[0_16px_34px_-10px_rgba(0,86,255,0.85)] transition-transform active:scale-95 dark:border-[#07080C]"
            >
              <Sparkles size={24} />
            </button>
          )}
        </div>
      </div>
      <MobileUserSwitcher open={switcherOpen} onClose={() => setSwitcherOpen(false)} />
    </>
  );
}

function MobileHome({ onNavigate, dark, setDark }: { onNavigate: (p: Page) => void; dark: boolean; setDark: (d: boolean) => void }) {
  const cats: { i: React.ReactNode; n: string; r?: Page; to?: string }[] = [
    { i: <FileText size={20} />, n: "Документы", r: "documents" },
    { i: <Home size={20} />, n: "ЖКХ", r: "finance" },
    { i: <Wallet size={20} />, n: "Налоги", r: "finance" },
    { i: <Heart size={20} />, n: "Семья", to: "/catalog?category=family&type=all" },
    { i: <Briefcase size={20} />, n: "Работа", to: "/catalog?category=work&type=all" },
    { i: <Newspaper size={20} />, n: "Новости", r: "news" },
  ];
  const navigate = useNavigate();
  const { situations, scenarioById, situationProgress, documents, utilityAccounts, taxes, settings, legal, currentUser, notes, profile, toggleNote } = useStore();
  const active = situations
    .map(s => { const sc = scenarioById(s.scenarioId); return sc ? { id: s.id, title: sc.title, progress: situationProgress(s), status: s.status } : null; })
    .filter(Boolean) as { id: string; title: string; progress: number; status: string }[];
  const primary = active.find(s => s.status !== "done");
  const deadlines = buildReminders(documents, utilityAccounts, taxes, settings);
  const nextDeadline = deadlines[0];
  const firstDoc = documents[0];
  const firstLegal = legal[0];
  const firstName = currentUser.role === "guest" ? "" : (currentUser.name || "").split(" ")[0];
  return (
    <div className="h-full overflow-y-auto px-5 pb-32 [&::-webkit-scrollbar]:hidden">
      {/* v0.9: логотип+название+уведомления рендерятся в MobileBrandBar
          (sticky сверху), здесь убрали чтобы не дублировать. */}
      <div className="mt-3">
        <div className="tracking-tight text-black/50 dark:text-white/50">Добрый день{firstName ? `, ${firstName}` : ""}</div>
        <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 28, lineHeight: 1.1 }}>
          Какая у вас<br />ситуация?
        </div>
      </div>

      <button onClick={() => onNavigate("catalog")} className="mt-5 flex w-full items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3.5 text-left shadow-[0_8px_24px_-16px_rgba(15,23,42,0.2)] dark:border-white/[0.06] dark:bg-[#0F1117]">
        <Search size={18} className="text-black/40 dark:text-white/40" />
        <span className="flex-1 tracking-tight text-black/40 dark:text-white/40">Например: потерял паспорт</span>
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
          <Sparkles size={14} />
        </span>
      </button>

      <div className="mt-5 grid grid-cols-3 gap-2.5">
        {cats.map((c) => (
          <button key={c.n} onClick={() => c.to ? navigate(c.to) : c.r && onNavigate(c.r)} className="flex flex-col items-start gap-2 rounded-2xl border border-black/[0.06] bg-white px-3 py-3 text-left transition-all active:scale-[0.98] dark:border-white/[0.06] dark:bg-[#0F1117]">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{c.i}</span>
            <span className="tracking-tight text-black dark:text-white">{c.n}</span>
          </button>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <div className="tracking-tight text-black dark:text-white">Мои ситуации</div>
        <button onClick={() => onNavigate("situations")} className="text-[13px] tracking-tight text-[#0056FF]">Все</button>
      </div>
      {primary ? (
        <button onClick={() => navigate(`/situations/${primary.id}`)} className="mt-3 block w-full overflow-hidden rounded-3xl p-5 text-left text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
          style={{ background: "linear-gradient(135deg,#001A66 0%,#0056FF 60%,#2277FF 100%)" }}>
          <div className="flex items-center justify-between">
            <Pill tone="ghost"><span className="text-white/90">В процессе</span></Pill>
            <span className="text-[12px] tracking-tight text-white/70">{primary.progress}%</span>
          </div>
          <div className="mt-3 tracking-tight" style={{ fontSize: 20, lineHeight: 1.2 }}>{primary.title}</div>
          <div className="mt-1 text-[13px] tracking-tight text-white/75">Продолжите выполнение задач по шагам</div>
          <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-white/20">
            <motion.div initial={{ width: 0 }} animate={{ width: `${primary.progress}%` }} transition={{ duration: 1 }} className="h-full rounded-full bg-white" />
          </div>
          <div className="mt-4 flex items-center justify-between">
            <span className="inline-flex items-center gap-1.5 text-[12px] tracking-tight text-white/80"><CalendarClock size={13} /> {active.length} активных</span>
            <span className="inline-flex items-center gap-1 text-[13px] tracking-tight">Продолжить <ArrowRight size={14} /></span>
          </div>
        </button>
      ) : (
        <button onClick={() => onNavigate("catalog")} className="mt-3 block w-full overflow-hidden rounded-3xl p-5 text-left text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
          style={{ background: "linear-gradient(135deg,#001A66 0%,#0056FF 60%,#2277FF 100%)" }}>
          <Pill tone="ghost"><span className="text-white/90">Нет активных ситуаций</span></Pill>
          <div className="mt-3 tracking-tight" style={{ fontSize: 19, lineHeight: 1.25 }}>Выберите сценарий, чтобы начать</div>
          <span className="mt-4 inline-flex items-center gap-1 text-[13px] tracking-tight">Открыть каталог <ArrowRight size={14} /></span>
        </button>
      )}

      <div className="mt-3 grid grid-cols-2 gap-3">
        <Card className="p-4">
          <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
            <AlertCircle size={15} /><span className="text-[12px] tracking-tight">Ближайший срок</span>
          </div>
          <div className="mt-1.5 truncate tracking-tight text-black dark:text-white">{nextDeadline ? nextDeadline.title : "Нет сроков"}</div>
          <div className="mt-0.5 line-clamp-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">{nextDeadline ? nextDeadline.body : "Всё под контролем"}</div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
            <Shield size={15} /><span className="text-[12px] tracking-tight">Документ</span>
          </div>
          <div className="mt-1.5 truncate tracking-tight text-black dark:text-white">{firstDoc ? firstDoc.title : "Не добавлен"}</div>
          <div className="mt-0.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">{firstDoc ? (firstDoc.expiresAt ? `Действует до ${firstDoc.expiresAt}` : "Без срока") : "Добавьте документ"}</div>
        </Card>
      </div>

      {/* v1.1 (P4): ближайшие заметки пользователя. Видны только гражданину,
          не гостю. Если заметок нет — карточка не показывается. */}
      {currentUser.role !== "guest" && (() => {
        const activeNotes = notes
          .filter(n => !n.done)
          .sort((a, b) => (a.reminderAt || "9999").localeCompare(b.reminderAt || "9999"))
          .slice(0, 3);
        if (activeNotes.length === 0) return null;
        const primaryAddress = profile?.addresses?.find(a => a.isPrimary)?.label || profile?.city || "";
        return (
          <div className="mt-6">
            <div className="flex items-center justify-between">
              <div className="tracking-tight text-black dark:text-white">Мои заметки</div>
              <button onClick={() => navigate("/profile")} className="text-[13px] tracking-tight text-[#0056FF]">Все</button>
            </div>
            <Card className="mt-3 p-4 space-y-2.5">
              {primaryAddress && (
                <div className="flex items-center gap-1.5 text-[11px] tracking-tight text-black/50 dark:text-white/50">
                  <MapPin size={11} /> {primaryAddress}
                </div>
              )}
              {activeNotes.map(n => (
                <div key={n.id} className="flex items-start gap-2.5">
                  <button
                    onClick={() => toggleNote(n.id)}
                    className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-md border border-black/15 dark:border-white/15"
                    title="Отметить выполненной"
                  >
                    {n.done && <Check size={12} className="text-[#0056FF]" />}
                  </button>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[13px] tracking-tight text-black dark:text-white">{n.text}</div>
                    <div className="mt-0.5 text-[11px] tracking-tight text-black/50 dark:text-white/50">
                      {n.category}{n.reminderAt ? ` · до ${n.reminderAt}` : ""}
                    </div>
                  </div>
                </div>
              ))}
            </Card>
          </div>
        );
      })()}

      <div className="mt-6 flex items-center justify-between">
        <div className="tracking-tight text-black dark:text-white">Важное для вас</div>
        <button onClick={() => onNavigate("legal")} className="text-[13px] tracking-tight text-[#0056FF]">Все</button>
      </div>
      {firstLegal && (
        <button onClick={() => navigate(`/law-detail/${firstLegal.id}`)} className="mt-3 block w-full text-left">
          <Card className="p-4">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <FileText size={16} />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Pill tone="lavender">{catLabelApp(firstLegal.category)}</Pill>
                  <span className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{firstLegal.effectiveDate}</span>
                </div>
                <div className="mt-2 tracking-tight text-black dark:text-white">{firstLegal.title}</div>
                <div className="mt-1 line-clamp-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">{firstLegal.summary}</div>
              </div>
            </div>
          </Card>
        </button>
      )}
    </div>
  );
}

function MobileCatalog({ onBack, onOpen }: { onBack: () => void; onOpen: () => void }) {
  const events = [
    { i: <Baby size={20} />, n: "Рождение ребёнка", c: "12 шагов" },
    { i: <Home size={20} />, n: "Переезд", c: "8 шагов" },
    { i: <FileText size={20} />, n: "Потеря паспорта", c: "5 шагов" },
    { i: <Building2 size={20} />, n: "Покупка жилья", c: "14 шагов" },
    { i: <Briefcase size={20} />, n: "Открытие ИП", c: "9 шагов" },
    { i: <Hammer size={20} />, n: "Увольнение", c: "6 шагов" },
  ];
  return (
    <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
      <MobileTopBar title="Жизненные сценарии" onBack={onBack} />
      <div className="px-5">
        <div className="flex items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3 dark:border-white/[0.06] dark:bg-[#0F1117]">
          <Search size={16} className="text-black/40 dark:text-white/40" />
          <input placeholder="Найти ситуацию" className="flex-1 bg-transparent tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40" />
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3">
          {events.map((e, i) => (
            <button key={e.n} onClick={onOpen} className="block text-left">
              <Card interactive className="p-4">
                <div className="mb-10 grid h-11 w-11 place-items-center rounded-2xl"
                  style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>
                  {e.i}
                </div>
                <div className="tracking-tight text-black dark:text-white">{e.n}</div>
                <div className="mt-0.5 text-[12px] tracking-tight text-black/50 dark:text-white/50">{e.c}</div>
              </Card>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function MobileSituations({ onBack, onNavigate }: { onBack: () => void; onNavigate: (p: Page) => void }) {
  const items = [
    { t: "Восстановление паспорта", s: "Шаг 3 из 5", p: 60, status: "В процессе", warn: true },
    { t: "Открытие ИП", s: "Шаг 1 из 9", p: 11, status: "В процессе", warn: false },
    { t: "Замена водительского", s: "Не начато", p: 0, status: "Запланировано", warn: false },
    { t: "Получение медкнижки", s: "Завершено", p: 100, status: "Готово", warn: false },
  ];
  return (
    <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
      <MobileTopBar title="Мои ситуации" onBack={onBack} right={
        <button className="grid h-10 w-10 place-items-center rounded-full bg-[#0056FF] text-white shadow-sm"><Plus size={16} /></button>
      } />
      <div className="px-5 space-y-3">
        {items.map((s) => (
          <button key={s.t} onClick={() => onNavigate("situation")} className="block w-full text-left">
            <Card interactive className="p-4">
              <div className="flex items-center gap-2">
                <Pill tone={s.p === 100 ? "ok" : s.warn ? "warn" : "lavender"}>{s.status}</Pill>
                {s.warn && <span className="text-[11px] tracking-tight text-amber-600 dark:text-amber-400">срок 14 дней</span>}
              </div>
              <div className="mt-2 tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{s.t}</div>
              <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{s.s}</div>
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
                <div className="h-full rounded-full" style={{ width: `${s.p}%`, background: s.p === 100 ? "#10B981" : "linear-gradient(90deg,#0056FF,#2277FF)" }} />
              </div>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}

function MobileSituationDetail({ onBack }: { onBack: () => void }) {
  const steps = [
    { n: "Получить справку об утере", state: "done", when: "Готово", where: "РОВД Первомайского района" },
    { n: "Сделать фото 4×5 на паспорт", state: "done", when: "Готово", where: "Фотосалон или дома" },
    { n: "Подать заявление в РОВД", state: "now", when: "Сегодня", where: "РОВД по месту жительства" },
    { n: "Оплатить госпошлину", state: "lock", when: "После шага 3", where: "Беларусбанк, ЕРИП" },
    { n: "Получить новый паспорт", state: "lock", when: "Через 14 дней", where: "РОВД Первомайского района" },
  ];
  return (
    <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
      <MobileTopBar title="Ситуация" onBack={onBack} right={
        <button className="grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"><Bookmark size={15} className="text-black dark:text-white" /></button>
      } />
      <div className="px-5">
        <div className="text-[12px] tracking-tight text-[#0056FF]">Документы · в процессе</div>
        <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 26, lineHeight: 1.15 }}>
          Восстановление<br />паспорта
        </div>
        <p className="mt-2 text-[14px] tracking-tight text-black/60 dark:text-white/60">
          Пошаговый план для жителей г. Минск. Учитывает все требования МВД.
        </p>

        <Card className="mt-5 p-4">
          <div className="flex items-center justify-between text-[12px] tracking-tight text-black/60 dark:text-white/60">
            <span>Прогресс</span><span>60%</span>
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
            <motion.div initial={{ width: 0 }} animate={{ width: "60%" }} transition={{ duration: 1 }} className="h-full rounded-full" style={{ background: "linear-gradient(90deg,#0056FF,#2277FF)" }} />
          </div>
        </Card>

        <div className="mt-6 tracking-tight text-black dark:text-white">Пошаговый план</div>
        <div className="relative mt-3">
          <div className="absolute left-[15px] bottom-2 top-2 w-px bg-black/10 dark:bg-white/10" />
          <div className="space-y-3">
            {steps.map((s, i) => (
              <div key={i} className="relative pl-10">
                <div className="absolute left-0 top-3 grid h-8 w-8 place-items-center rounded-full"
                  style={{
                    background: s.state === "done" ? "linear-gradient(135deg,#0056FF,#2277FF)" : s.state === "now" ? "white" : "transparent",
                    boxShadow: s.state === "now" ? "0 0 0 2px #0056FF, 0 0 0 6px #E3E7FC" : "none",
                  }}>
                  {s.state === "done" && <Check size={16} className="text-white" strokeWidth={2.6} />}
                  {s.state === "now" && <span className="h-2 w-2 rounded-full bg-[#0056FF]" />}
                  {s.state === "lock" && <Lock size={14} className="text-black/35 dark:text-white/30" />}
                </div>
                <Card className={`p-4 ${s.state === "lock" ? "opacity-60" : ""}`}>
                  <div className="flex items-center gap-2">
                    {s.state === "now" && <Pill tone="royal">Сейчас</Pill>}
                    {s.state === "done" && <Pill tone="ok">Выполнено</Pill>}
                    <span className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{s.when}</span>
                  </div>
                  <div className="mt-1.5 tracking-tight text-black dark:text-white">{s.n}</div>
                  <div className="mt-1 flex items-center gap-1.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                    <MapPin size={12} /> {s.where}
                  </div>
                  {s.state === "now" && (
                    <div className="mt-3 flex items-center gap-2">
                      <PrimaryButton className="h-10 px-4">Я сделал(а)</PrimaryButton>
                      <GhostButton className="h-10 px-4">Подробнее</GhostButton>
                    </div>
                  )}
                </Card>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function MobileDocuments({ onBack }: { onBack: () => void }) {
  return (
    <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
      <MobileTopBar title="Мои документы" onBack={onBack} right={
        <button className="grid h-10 w-10 place-items-center rounded-full bg-[#0056FF] text-white shadow-sm"><Plus size={16} /></button>
      } />
      <div className="px-5">
        <div className="flex items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
          <Shield size={13} className="text-emerald-600 dark:text-emerald-400" />
          Хранится локально, зашифровано
        </div>
        <div className="mt-4 overflow-hidden rounded-3xl p-5 text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
          style={{ background: "linear-gradient(135deg,#000000 0%,#001A66 50%,#0056FF 100%)" }}>
          <div className="flex items-center justify-between">
            <span className="text-[12px] tracking-tight text-white/70">Паспорт гражданина РБ</span>
            <button className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-[11px] tracking-tight backdrop-blur">
              <EyeOff size={12} /> Скрыть
            </button>
          </div>
          <div className="mt-6 tracking-tight">Иванов Алексей</div>
          <div className="mt-1 font-mono text-[13px] tracking-[0.2em] text-white/70">MP •••• •••• 4821</div>
          <div className="mt-5 grid grid-cols-3 gap-2 text-[11px] tracking-tight text-white/60">
            <div><div>Выдан</div><div className="mt-0.5 text-white">2021</div></div>
            <div><div>Действует</div><div className="mt-0.5 text-white">до 2031</div></div>
            <div><div>Орган</div><div className="mt-0.5 text-white">РОВД Мин.</div></div>
          </div>
        </div>
        <div className="mt-3 space-y-2.5">
          {[
            { n: "Медкнижка", s: "Действует до 12 авг 2027", ok: true },
            { n: "Водительское удостоверение", s: "Истекает через 6 месяцев", warn: true },
            { n: "Свидетельство о рождении ребёнка", s: "Бессрочно", ok: true },
            { n: "ИНН / Налоговая карта", s: "Бессрочно", ok: true },
          ].map((d) => (
            <Card key={d.n} className="flex items-center gap-3 p-4">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <FileText size={18} />
              </span>
              <div className="flex-1">
                <div className="tracking-tight text-black dark:text-white">{d.n}</div>
                <div className={`text-[12px] tracking-tight ${d.warn ? "text-amber-600 dark:text-amber-400" : "text-black/55 dark:text-white/55"}`}>{d.s}</div>
              </div>
              <ChevronRight size={16} className="text-black/30 dark:text-white/30" />
            </Card>
          ))}
        </div>
        <button className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-black/15 bg-transparent py-4 text-[14px] tracking-tight text-black/55 dark:border-white/15 dark:text-white/55">
          <ScanLine size={16} /> Сканировать новый документ
        </button>
      </div>
    </div>
  );
}

function MobileLegal({ onBack }: { onBack: () => void }) {
  const items = [
    { t: "Налоги", title: "Новый порядок имущественного вычета", d: "с 1 июля 2026", priority: true, you: true },
    { t: "ЖКХ", title: "Изменение тарифов на отопление в г. Минск", d: "с 1 октября 2026", priority: false, you: true },
    { t: "Документы", title: "Электронный паспорт: запуск второй очереди", d: "с 15 сентября 2026", priority: true, you: false },
    { t: "Семья", title: "Расширение списка получателей детских пособий", d: "с 1 января 2027", priority: false, you: false },
  ];
  return (
    <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
      <MobileTopBar title="Важное для вас" onBack={onBack} />
      <div className="px-5">
        <div className="text-[13px] tracking-tight text-black/55 dark:text-white/55">Подобрано по вашему профилю и городу</div>
        <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden">
          {["Все","Налоги","ЖКХ","Документы","Семья","Работа"].map((t, i) => (
            <span key={t} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${i===0 ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{t}</span>
          ))}
        </div>
        <div className="mt-4 space-y-3">
          {items.map((it) => (
            <Card key={it.title} interactive className="p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <Pill tone="lavender">{it.t}</Pill>
                {it.priority && <Pill tone="warn"><AlertCircle size={11} /> Важное</Pill>}
                {it.you && <Pill tone="ok">Касается вас</Pill>}
              </div>
              <div className="mt-2.5 tracking-tight text-black dark:text-white" style={{ fontSize: 16, lineHeight: 1.25 }}>{it.title}</div>
              <div className="mt-2 flex items-center justify-between text-[12px] tracking-tight text-black/50 dark:text-white/50">
                <span className="inline-flex items-center gap-1.5"><Clock size={12} /> {it.d}</span>
                <span className="inline-flex items-center gap-1 text-[#0056FF]">Подробнее <ArrowUpRight size={12} /></span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

function MobileNotifications({ onBack }: { onBack: () => void }) {
  const groups = [
    { title: "Сегодня", items: [
      { i: <CalendarClock size={15} />, t: "Срок оплаты налога — через 14 дней", s: "Налог на недвижимость", tone: "warn" },
      { i: <FileText size={15} />, t: "Опубликовано новое правовое обновление", s: "Налоги · касается вас", tone: "lav" },
    ]},
    { title: "Вчера", items: [
      { i: <Check size={15} />, t: "Шаг выполнен: справка получена", s: "Восстановление паспорта", tone: "ok" },
      { i: <Shield size={15} />, t: "Срок действия водительского — 6 мес", s: "Документы", tone: "warn" },
    ]},
  ];
  return (
    <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
      <MobileTopBar title="Уведомления" onBack={onBack} right={
        <button className="grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]"><X size={15} className="text-black dark:text-white" /></button>
      } />
      <div className="px-5 space-y-5">
        {groups.map(g => (
          <div key={g.title}>
            <div className="mb-2 text-[12px] tracking-tight text-black/45 dark:text-white/45">{g.title}</div>
            <div className="space-y-2">
              {g.items.map((it, i) => (
                <Card key={i} className="flex items-start gap-3 p-4">
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${
                    it.tone === "warn" ? "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300" :
                    it.tone === "ok" ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300" :
                    "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"
                  }`}>{it.i}</span>
                  <div className="flex-1">
                    <div className="tracking-tight text-black dark:text-white">{it.t}</div>
                    <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{it.s}</div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MobileProfile({ onBack, dark, setDark }: { onBack: () => void; dark: boolean; setDark: (d: boolean) => void }) {
  return (
    <div className="h-full overflow-y-auto pb-32 [&::-webkit-scrollbar]:hidden">
      <MobileTopBar title="Профиль" onBack={onBack} />
      <div className="px-5">
        <Card className="flex items-center gap-4 p-4">
          <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#0056FF] to-[#2277FF]" />
          <div className="flex-1">
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 17 }}>Алексей Иванов</div>
            <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Минск · Первомайский район</div>
          </div>
          <ChevronRight size={16} className="text-black/30 dark:text-white/30" />
        </Card>

        <div className="mt-5 mb-2 text-[12px] tracking-tight text-black/45 dark:text-white/45">Статусы</div>
        <div className="flex flex-wrap gap-2">
          {["Собственник жилья","Есть дети","ИП","Авто"].map(t => <Pill key={t} tone="lavender">{t}</Pill>)}
          <Pill tone="ghost">+ Добавить</Pill>
        </div>

        <div className="mt-5 mb-2 text-[12px] tracking-tight text-black/45 dark:text-white/45">Настройки</div>
        <Card className="divide-y divide-black/[0.05] p-0 dark:divide-white/[0.05]">
          {[
            { l: "Тёмная тема", on: dark, action: () => setDark(!dark) },
            { l: "Большой шрифт", on: false },
            { l: "Высокий контраст", on: false },
            { l: "Скрыть личные данные", on: true },
            { l: "Уведомления о сроках", on: true },
          ].map((s, i) => (
            <button key={i} onClick={s.action} className="flex w-full items-center justify-between px-4 py-3.5 text-left">
              <span className="tracking-tight text-black dark:text-white">{s.l}</span>
              <div className={`relative h-7 w-12 rounded-full transition-colors ${s.on ? "bg-[#0056FF]" : "bg-black/10 dark:bg-white/15"}`}>
                <motion.div layout className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow ${s.on ? "left-[22px]" : "left-0.5"}`} />
              </div>
            </button>
          ))}
        </Card>

        <button onClick={onBack} className="mt-5 w-full rounded-2xl border border-black/10 py-3.5 text-[14px] tracking-tight text-black/65 dark:border-white/10 dark:text-white/65">
          Выйти
        </button>
      </div>
    </div>
  );
}

/* ============================================================
   DESKTOP APP
   ============================================================ */
export function DesktopShell({ dark, setDark }: { dark: boolean; setDark: (d: boolean) => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const page = location.pathname.split("/")[1] || "home";

  const [searchOpen, setSearchOpen] = useState(false);
  const [docModal, setDocModal] = useState<{ open: boolean; id: string | null }>({ open: false, id: null });
  const [guardOpen, setGuardOpen] = useState(false);
  const { role, scenarioById } = useStore();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
      if (e.key === "Escape") setSearchOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const openScenario = (id: string) => navigate(`/scenarios/${id}`);
  const openMySituation = (id: string) => navigate(`/situations/${id}`);
  const protectedGuard = () => {
    if (role === "guest") { setGuardOpen(true); return false; }
    return true;
  };

  return (
    <div className="grid h-[100dvh] grid-cols-[260px_1fr] overflow-hidden bg-[#F4F5FA] dark:bg-[#05060A]">
      <DesktopSidebar active={page as Page} onChange={(p) => { if (p === page) scrollContentToTop("smooth"); else navigate(`/${p === 'home' ? '' : p}`); }} />
      <div className="flex flex-col overflow-hidden">
        <DesktopTopBar onSearch={() => setSearchOpen(true)} onNotifications={() => navigate("/notifications")} />
        <div data-scroll-root className="flex-1 overflow-y-auto">
          {/* Входящая страница НЕ стартует с opacity:0. Иначе при mode="wait"
              потерянный exit-complete callback (гонка ре-рендера при переходе,
              напр. на /settings) навсегда оставляет страницу невидимой —
              «виден только фон, помогает только перезагрузка». Анимируем только y.
              См. тот же фикс в мобильном shell выше. */}
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ y: 8 }} animate={{ y: 0 }} exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              className="px-10 py-8"
            >
              <Outlet context={{ openScenario, openMySituation, protectedGuard, onAddDoc: () => { if (protectedGuard()) setDocModal({ open: true, id: null }); }, onEditDoc: (id: string) => { if (protectedGuard()) setDocModal({ open: true, id }); } }} />
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
      <SearchOverlay
        open={searchOpen}
        onClose={() => setSearchOpen(false)}
        onOpenScenario={openScenario}
        onOpenLegal={() => navigate("/legal")}
        onOpenDocuments={() => navigate("/documents")}
      />
      <DocumentEditModal open={docModal.open} editingId={docModal.id} onClose={() => setDocModal({ open: false, id: null })} />
      <GuestGuardModal
        open={guardOpen}
        onClose={() => setGuardOpen(false)}
        onSignIn={() => { setGuardOpen(false); navigate("/login"); }}
        onRegister={() => { setGuardOpen(false); navigate("/register"); }}
      />
      <ConnectionBanner />
    </div>
  );
}

// v0.5: Каталог — первая основная функция (поиск информации), поэтому идёт
// первым. «Уведомления» убраны из меню — остались только как кнопка с
// колокольчиком в правом блоке. «Важное» (/legal) закрыто — редирект на
// /news (см. routes.tsx). В v0.7 лента новостей объединит обычные новости
// и закон-апдейты.
const TOP_NAV: { id: Page; icon: React.ReactNode; label: string; badge?: string }[] = [
  { id: "home", icon: <Home size={16} />, label: "Главная" },
  { id: "catalog", icon: <LayoutGrid size={16} />, label: "Каталог" },
  { id: "situations", icon: <FileText size={16} />, label: "Ситуации", badge: "3" },
  { id: "documents", icon: <Shield size={16} />, label: "Документы" },
  { id: "finance", icon: <Wallet size={16} />, label: "ЖКХ и налоги" },
  { id: "news", icon: <Newspaper size={16} />, label: "Новости" },
];

const FEATURE_BY_PAGE: Partial<Record<Page, string>> = {
  situations: "situations",
  documents: "documents",
  finance: "finance",
  news: "news",
  profile: "profile",
};

function isPageEnabledBySystemState(page: Page, systemState: SystemState): boolean {
  const key = FEATURE_BY_PAGE[page];
  if (!key) return true;
  return systemState.featureFlags[key] !== false;
}

function orderNavigationItems<T extends { id: Page }>(items: T[], order: string[] | undefined): T[] {
  if (!order?.length) return items;
  const rank = new Map(order.map((id, index) => [id, index]));
  return [...items].sort((a, b) => {
    const ar = rank.get(a.id) ?? 999;
    const br = rank.get(b.id) ?? 999;
    if (ar !== br) return ar - br;
    return items.indexOf(a) - items.indexOf(b);
  });
}

function HeaderUserMenu() {
  const navigate = useNavigate();
  const { currentUser, profile, quickAccounts, signInAs, signOut, resetSession } = useStore();
  const [open, setOpen] = useState(false);
  const isGuest = currentUser.role === "guest";
  const menuAccounts = [{ id: "guest", name: "Гость", email: "", role: "guest" }, ...quickAccounts];
  const switchTo = (id: string) => { signInAs(id); setOpen(false); navigate("/"); };
  return (
    <div className="relative">
      <button onClick={() => setOpen(v => !v)} className="flex items-center gap-2 rounded-full bg-[#F6F7FB] py-1 pl-1 pr-2.5 transition-colors hover:bg-black/[0.05] dark:bg-white/[0.05] dark:hover:bg-white/[0.08]">
        <UserAvatarCircle src={isGuest ? undefined : profile?.avatarDataUrl} name={isGuest ? "Гость" : currentUser.name} size={36} />
        <ChevronRight size={14} className={`text-black/35 transition-transform dark:text-white/35 ${open ? "rotate-90" : ""}`} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-[100]" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-[52px] z-[110] w-[320px] rounded-3xl border border-black/[0.08] bg-white p-3 shadow-[0_28px_80px_-38px_rgba(15,23,42,0.55)] dark:border-white/[0.08] dark:bg-[#0F1117]">
            <div className="px-2 pb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Сменить пользователя</div>
            <div className="max-h-[260px] space-y-1 overflow-y-auto [&::-webkit-scrollbar]:hidden">
              {menuAccounts.map(account => {
                const isActive = account.id === currentUser.id || (account.id === "guest" && currentUser.role === "guest");
                return (
                  <button key={account.id} onClick={() => switchTo(account.id)} className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition-colors ${isActive ? "bg-[#E3E7FC] dark:bg-[#0E1A3A]" : "hover:bg-black/[0.03] dark:hover:bg-white/[0.04]"}`}>
                    <UserAvatarCircle src={account.id === "guest" ? undefined : readAvatarForUser(account.id)} name={account.name} email={account.email} size={36} />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[14px] tracking-tight text-black dark:text-white">{account.name}</span>
                      <span className="block truncate text-[12px] tracking-tight text-black/50 dark:text-white/50">{roleTitle(account.role)}</span>
                    </span>
                    {isActive && <Check size={16} className="text-[#0056FF]" />}
                  </button>
                );
              })}
            </div>
            <div className="my-2 h-px bg-black/[0.06] dark:bg-white/[0.06]" />
            <button onClick={() => { setOpen(false); navigate("/profile"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.03] dark:text-white dark:hover:bg-white/[0.04]"><User size={16} className="text-black/45 dark:text-white/45" /> Профиль</button>
            <button onClick={() => { setOpen(false); navigate("/settings"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.03] dark:text-white dark:hover:bg-white/[0.04]"><Settings size={16} className="text-black/45 dark:text-white/45" /> Настройки</button>
            <button onClick={() => { setOpen(false); navigate("/register"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.03] dark:text-white dark:hover:bg-white/[0.04]"><UserPlus size={16} className="text-[#0056FF]" /> Добавить пользователя</button>
            <button onClick={() => { signOut(); setOpen(false); navigate("/"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-red-500 transition-colors hover:bg-red-50 dark:hover:bg-red-500/10"><LogOut size={16} /> Выйти из аккаунта</button>
            <button onClick={() => { resetSession(); setOpen(false); navigate("/"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[13px] tracking-tight text-black/55 transition-colors hover:bg-black/[0.03] dark:text-white/55 dark:hover:bg-white/[0.04]"><LogOut size={15} /> Выйти из всех</button>
          </div>
        </>
      )}
    </div>
  );
}

function DesktopHeaderShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const page = (location.pathname.split("/")[1] || "home") as Page;
  const [searchOpen, setSearchOpen] = useState(false);
  const [docModal, setDocModal] = useState<{ open: boolean; id: string | null }>({ open: false, id: null });
  const [guardOpen, setGuardOpen] = useState(false);
  const { role, systemState } = useStore();
  const { openAdmin } = React.useContext(ShellContext);
  const topNav = orderNavigationItems(
    TOP_NAV.filter((item) => isPageEnabledBySystemState(item.id, systemState)),
    systemState.navigationLayout.desktop,
  );
  const staffPanelEnabled = isStaffRole(role)
    && (isAdminRole(role) ? systemState.featureFlags.adminPanel !== false : systemState.featureFlags.editorPanel !== false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setSearchOpen(true); }
      if (e.key === "Escape") setSearchOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const openScenario = (id: string) => navigate(`/scenarios/${id}`);
  const openMySituation = (id: string) => navigate(`/situations/${id}`);
  const protectedGuard = () => { if (role === "guest") { setGuardOpen(true); return false; } return true; };
  const go = (p: Page) => { if (p === page) scrollContentToTop("smooth"); else navigate(`/${p === "home" ? "" : p}`); };

  return (
    <div className="flex h-[100dvh] flex-col overflow-hidden bg-[#F4F5FA] dark:bg-[#05060A]">
      <header className="relative z-50 flex items-center gap-4 border-b border-black/[0.06] bg-white/80 px-8 py-3 backdrop-blur dark:border-white/[0.06] dark:bg-[#0B0D13]/80">
        <button onClick={() => go("home")} className="shrink-0"><Logo size={26} /></button>
        <nav className="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto [&::-webkit-scrollbar]:hidden">
          {topNav.map(t => {
            const isActive = page === t.id;
            return (
              <button key={t.id} onClick={() => go(t.id)} className={`relative flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-[14px] tracking-tight transition-colors ${isActive ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/65 hover:bg-black/[0.03] dark:text-white/65 dark:hover:bg-white/[0.04]"}`}>
                {t.icon}<span>{t.label}</span>
                {t.badge && <span className="rounded-full bg-[#0056FF] px-1.5 text-[10px] text-white">{t.badge}</span>}
              </button>
            );
          })}
          {staffPanelEnabled && (
            <button onClick={openAdmin} className="flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-[14px] tracking-tight text-black/65 transition-colors hover:bg-black/[0.03] dark:text-white/65 dark:hover:bg-white/[0.04]"><Users size={16} />{isAdminRole(role) ? "Админ" : "Редактор"}</button>
          )}
        </nav>
        {/* v0.6: на desktop поиск inline в header — input + dropdown с подсказками.
            На tablet/mobile остаётся кнопка -> overlay. */}
        <HeaderSearch
          className="hidden lg:flex"
          onOpenScenario={openScenario}
          onOpenLegal={() => navigate("/legal")}
          onOpenDocuments={() => navigate("/documents")}
        />
        <button onClick={() => setSearchOpen(true)} className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-black shadow-sm lg:hidden dark:bg-white/[0.06] dark:text-white"><Search size={16} /></button>
        <button onClick={() => go("notifications")} className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white text-black shadow-sm dark:bg-white/[0.06] dark:text-white"><Bell size={16} /></button>
        <HeaderUserMenu />
      </header>

      <div data-scroll-root className="flex-1 overflow-y-auto">
        {/* То же, что и выше: без initial opacity:0, чтобы потерянный
            exit-complete не оставлял страницу невидимой до перезагрузки. */}
        <AnimatePresence mode="wait">
          <motion.div key={location.pathname} initial={{ y: 8 }} animate={{ y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.2 }} className="mx-auto max-w-[1180px] px-10 py-8">
            <Outlet context={{ openScenario, openMySituation, protectedGuard, onAddDoc: () => { if (protectedGuard()) setDocModal({ open: true, id: null }); }, onEditDoc: (id: string) => { if (protectedGuard()) setDocModal({ open: true, id }); } }} />
          </motion.div>
        </AnimatePresence>
      </div>

      <SearchOverlay open={searchOpen} onClose={() => setSearchOpen(false)} onOpenScenario={openScenario} onOpenLegal={() => navigate("/legal")} onOpenDocuments={() => navigate("/documents")} />
      <DocumentEditModal open={docModal.open} editingId={docModal.id} onClose={() => setDocModal({ open: false, id: null })} />
      <GuestGuardModal open={guardOpen} onClose={() => setGuardOpen(false)} onSignIn={() => { setGuardOpen(false); navigate("/login"); }} onRegister={() => { setGuardOpen(false); navigate("/register"); }} />
    </div>
  );
}

function DesktopSidebar({ active, onChange }: { active: Page; onChange: (p: Page) => void }) {
  const { currentUser, profile, role, quickAccounts, signInAs, signOut, resetSession, systemState } = useStore();
  const { openAdmin } = React.useContext(ShellContext);
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuAccounts = [{ id: "guest", name: "Гость", email: "Просмотр без аккаунта", role: "guest" }, ...quickAccounts];
  const item = (id: Page, icon: React.ReactNode, label: string, badge?: string) => {
    const isActive = active === id;
    return (
      <button onClick={() => onChange(id)} className={`relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left tracking-tight transition-colors ${isActive ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/65 hover:bg-black/[0.03] dark:text-white/65 dark:hover:bg-white/[0.04]"}`}>
        <span className="grid h-5 w-5 place-items-center">{icon}</span>
        <span className="flex-1 text-[14px]">{label}</span>
        {badge && <span className="rounded-full bg-[#0056FF] px-1.5 text-[10px] tracking-tight text-white">{badge}</span>}
      </button>
    );
  };
  const personalNav = orderNavigationItems(
    [
      { id: "home" as Page, icon: <Home size={16} />, label: "Главная" },
      { id: "catalog" as Page, icon: <LayoutGrid size={16} />, label: "Каталог" },
      { id: "situations" as Page, icon: <FileText size={16} />, label: "Мои ситуации", badge: "3" },
      { id: "documents" as Page, icon: <Shield size={16} />, label: "Документы" },
      { id: "news" as Page, icon: <Newspaper size={16} />, label: "Новости" },
    ].filter((entry) => isPageEnabledBySystemState(entry.id, systemState)),
    systemState.navigationLayout.tablet,
  );
  const toolsNav = orderNavigationItems(
    [
      { id: "finance" as Page, icon: <Wallet size={16} />, label: "ЖКХ и налоги" },
      { id: "profile" as Page, icon: <User size={16} />, label: "Профиль" },
    ].filter((entry) => isPageEnabledBySystemState(entry.id, systemState)),
    systemState.navigationLayout.tablet,
  );
  const staffPanelEnabled = isStaffRole(role)
    && (isAdminRole(role) ? systemState.featureFlags.adminPanel !== false : systemState.featureFlags.editorPanel !== false);
  const switchTo = (id: string) => { signInAs(id); setMenuOpen(false); navigate("/"); };
  return (
    <aside className="flex h-full flex-col border-r border-black/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-[#0B0D13]">
      <Logo size={26} />
      <div className="relative mt-6">
        <button onClick={() => setMenuOpen(v => !v)} className="flex w-full items-center gap-3 rounded-2xl bg-[#F6F7FB] px-3 py-2 text-left transition-colors hover:bg-black/[0.05] dark:bg-white/[0.04] dark:hover:bg-white/[0.07]">
          <UserAvatarCircle src={currentUser.role === "guest" ? undefined : profile?.avatarDataUrl} name={currentUser.role === "guest" ? "Гость" : currentUser.name} size={32} />
          <div className="min-w-0 flex-1">
            <div className="truncate tracking-tight text-black dark:text-white">{currentUser.role === "guest" ? "Гость" : currentUser.name}</div>
            <div className="truncate text-[11px] tracking-tight text-black/50 dark:text-white/50">{roleTitle(currentUser.role)}{currentUser.city ? ` · ${currentUser.city}` : ""}</div>
          </div>
          <ChevronRight size={14} className={`shrink-0 text-black/35 transition-transform dark:text-white/35 ${menuOpen ? "rotate-90" : ""}`} />
        </button>

        {menuOpen && (
          <>
            <div className="fixed inset-0 z-[100]" onClick={() => setMenuOpen(false)} />
            <div className="absolute left-full top-0 z-[110] ml-3 w-[320px] rounded-3xl border border-black/[0.08] bg-white p-3 shadow-[0_28px_80px_-38px_rgba(15,23,42,0.55)] dark:border-white/[0.08] dark:bg-[#0F1117]">
              <div className="px-2 pb-2 text-[11px] font-medium uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Сменить пользователя</div>
              <div className="max-h-[260px] space-y-1 overflow-y-auto [&::-webkit-scrollbar]:hidden">
                {menuAccounts.map(account => {
                  const isActive = account.id === currentUser.id || (account.id === "guest" && currentUser.role === "guest");
                  return (
                    <button key={account.id} onClick={() => switchTo(account.id)}
                      className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition-colors ${isActive ? "bg-[#E3E7FC] dark:bg-[#0E1A3A]" : "hover:bg-black/[0.03] dark:hover:bg-white/[0.04]"}`}>
                      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#F6F7FB] text-[13px] font-medium text-[#0056FF] dark:bg-white/[0.06] dark:text-[#7FA8FF]">{(account.name || "П").slice(0, 1).toUpperCase()}</span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[14px] tracking-tight text-black dark:text-white">{account.name}</span>
                        <span className="block truncate text-[12px] tracking-tight text-black/50 dark:text-white/50">{roleTitle(account.role)}</span>
                      </span>
                      {isActive && <Check size={16} className="text-[#0056FF]" />}
                    </button>
                  );
                })}
              </div>
              <div className="my-2 h-px bg-black/[0.06] dark:bg-white/[0.06]" />
              <button onClick={() => { setMenuOpen(false); navigate("/profile"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.03] dark:text-white dark:hover:bg-white/[0.04]"><User size={16} className="text-black/45 dark:text-white/45" /> Профиль</button>
              <button onClick={() => { setMenuOpen(false); navigate("/register"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.03] dark:text-white dark:hover:bg-white/[0.04]"><UserPlus size={16} className="text-[#0056FF]" /> Добавить пользователя</button>
              <button onClick={() => { signOut(); setMenuOpen(false); navigate("/"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-red-500 transition-colors hover:bg-red-50 dark:hover:bg-red-500/10"><LogOut size={16} /> Выйти из аккаунта</button>
              <button onClick={() => { resetSession(); setMenuOpen(false); navigate("/"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[13px] tracking-tight text-black/55 transition-colors hover:bg-black/[0.03] dark:text-white/55 dark:hover:bg-white/[0.04]"><LogOut size={15} /> Выйти из всех</button>
            </div>
          </>
        )}
      </div>
      <nav className="mt-6 space-y-1">
        <div className="px-3 pb-1.5 text-[10px] uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Личный кабинет</div>
        {personalNav.map((entry) => item(entry.id, entry.icon, entry.label, entry.badge))}
      </nav>
      <nav className="mt-6 space-y-1">
        <div className="px-3 pb-1.5 text-[10px] uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Инструменты</div>
        {toolsNav.map((entry) => item(entry.id, entry.icon, entry.label))}
        {staffPanelEnabled && (
          <button onClick={openAdmin} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left tracking-tight text-black/65 transition-colors hover:bg-black/[0.03] dark:text-white/65 dark:hover:bg-white/[0.04]">
            <span className="grid h-5 w-5 place-items-center"><Users size={16} /></span>
            <span className="flex-1 text-[14px]">{role === "editor" ? "Редактор контента" : "Админ-панель"}</span>
          </button>
        )}
      </nav>
      <div className="mt-auto pt-4">
        {item("settings", <Settings size={16} />, "Настройки")}
      </div>
    </aside>
  );
}

function roleTitle(role: string) {
  return ({
    guest: "Гость",
    citizen: "Гражданин",
    editor: "Редактор",
    admin: "Администратор",
    content_editor: "Редактор контента",
    platform_admin: "Администратор платформы",
  } as Record<string, string>)[role] ?? role;
}

/* ============================================================
   v0.6: inline-поиск в desktop header
   ============================================================ */
function HeaderSearch({
  className,
  onOpenScenario,
  onOpenLegal,
  onOpenDocuments,
}: {
  className?: string;
  onOpenScenario: (id: string) => void;
  onOpenLegal: () => void;
  onOpenDocuments: () => void;
}) {
  const navigate = useNavigate();
  const { scenarios, problems, documents, publicDocuments, authorities, legal } = useStore();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const rootRef = useRef<HTMLDivElement | null>(null);

  // Закрываем dropdown по клику вне
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  // ⌘K / Ctrl+K — фокус на input
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      }
      if (e.key === "Escape") {
        setOpen(false);
        inputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const pool = useMemo(() => {
    const p: { label: string; kind: string }[] = [];
    problems.forEach((x) => p.push({ label: x.title, kind: "проблема" }));
    scenarios.forEach((x) => p.push({ label: x.title, kind: "сценарий" }));
    publicDocuments.forEach((x) => p.push({ label: x.name, kind: "документ" }));
    documents.forEach((x) => p.push({ label: x.title, kind: "документ" }));
    authorities.forEach((x) => p.push({ label: x.name, kind: "учреждение" }));
    legal.forEach((x) => p.push({ label: x.title, kind: "закон-апдейт" }));
    return p;
  }, [problems, scenarios, publicDocuments, documents, authorities, legal]);

  const suggestions = useMemo(() => {
    if (!q.trim()) return pool.slice(0, 6);
    const lower = q.toLowerCase();
    return pool
      .filter((p) => p.label.toLowerCase().includes(lower))
      .slice(0, 8);
  }, [q, pool]);

  const commit = (value: string) => {
    if (!value.trim()) return;
    setQ(value);
    setOpen(false);
    // Простая маршрутизация по первому совпадению
    const firstScenario = scenarios.find((s) => s.title.toLowerCase().includes(value.toLowerCase()));
    if (firstScenario) { onOpenScenario(firstScenario.id); return; }
    const firstDoc = documents.find((d) => d.title.toLowerCase().includes(value.toLowerCase()));
    if (firstDoc) { onOpenDocuments(); return; }
    if (legal.some((l) => l.title.toLowerCase().includes(value.toLowerCase()))) { onOpenLegal(); return; }
    // Фолбэк: ведём в каталог с query
    navigate(`/catalog?q=${encodeURIComponent(value)}`);
  };

  return (
    <div ref={rootRef} className={`relative w-[320px] shrink-0 ${className ?? ""}`}>
      <div className="flex h-10 items-center gap-2 overflow-hidden rounded-2xl border border-black/[0.06] bg-[#F6F7FB] px-3 dark:border-white/[0.06] dark:bg-white/[0.04]">
        <Search size={15} className="shrink-0 text-black/40 dark:text-white/40" />
        <input
          ref={inputRef}
          value={q}
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => { if (e.key === "Enter") commit(q); }}
          placeholder="Поиск по сервису"
          className="min-w-0 flex-1 bg-transparent text-[13px] tracking-tight outline-none placeholder:text-black/40 dark:text-white dark:placeholder:text-white/40"
        />
        {q && (
          <button
            onClick={() => { setQ(""); inputRef.current?.focus(); }}
            className="shrink-0 text-black/35 hover:text-black/60 dark:text-white/35"
            aria-label="Очистить"
          >
            <X size={13} />
          </button>
        )}
        <span className="shrink-0 rounded-md bg-black/[0.05] px-1.5 py-0.5 text-[10px] text-black/50 dark:bg-white/[0.08] dark:text-white/60">⌘K</span>
      </div>

      {open && suggestions.length > 0 && (
        <div className="absolute left-0 right-0 top-[calc(100%+6px)] z-[100] max-h-[420px] overflow-y-auto rounded-2xl border border-black/[0.06] bg-white p-1.5 shadow-[0_24px_60px_-20px_rgba(15,23,42,0.25)] dark:border-white/[0.08] dark:bg-[#0F1117] [scrollbar-width:thin]">
          {!q.trim() && (
            <div className="px-3 pb-1.5 pt-2 text-[10px] uppercase tracking-[0.14em] text-black/40 dark:text-white/40">Подсказки</div>
          )}
          {suggestions.map((s, i) => (
            <button
              key={`${s.kind}:${s.label}:${i}`}
              onClick={() => commit(s.label)}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-[13px] tracking-tight text-black hover:bg-black/[0.04] dark:text-white dark:hover:bg-white/[0.04]"
            >
              <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <Search size={12} />
              </span>
              <span className="min-w-0 flex-1 truncate">{s.label}</span>
              <span className="shrink-0 text-[10px] uppercase tracking-[0.14em] text-black/35 dark:text-white/35">{s.kind}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function UserSwitcher() {
  const navigate = useNavigate();
  const { currentUser, quickAccounts, signInAs, signOut, resetSession } = useStore();
  const [open, setOpen] = useState(false);
  const initial = currentUser.role === "guest" ? "Г" : (currentUser.name || "П").slice(0, 1).toUpperCase();

  const choose = (id: string) => {
    signInAs(id);
    setOpen(false);
    navigate("/");
  };

  const logout = () => {
    signOut();
    setOpen(false);
    navigate("/");
  };

  const menuAccounts = [
    { id: "guest", name: "Гость", email: "Просмотр без аккаунта", role: "guest" },
    ...quickAccounts,
  ];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(value => !value)}
        className="flex items-center gap-3 rounded-2xl bg-white px-3 py-2 shadow-sm transition-transform hover:scale-[1.02] active:scale-[0.98] dark:bg-white/[0.06]"
      >
        <span className="grid h-9 w-9 place-items-center rounded-full bg-[#E3E7FC] text-[14px] font-medium text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
          {initial}
        </span>
        <span className="hidden min-w-[130px] text-left xl:block">
          <span className="block truncate text-[13px] font-medium tracking-tight text-black dark:text-white">{currentUser.role === "guest" ? "Гость" : currentUser.name}</span>
          <span className="block truncate text-[11px] tracking-tight text-black/45 dark:text-white/45">{roleTitle(currentUser.role)}</span>
        </span>
        <ChevronRight size={14} className={`text-black/35 transition-transform dark:text-white/35 ${open ? "rotate-90" : ""}`} />
      </button>

      {open && (
        <div className="absolute right-0 top-[52px] z-50 w-[340px] rounded-3xl border border-black/[0.08] bg-white p-3 shadow-[0_28px_80px_-38px_rgba(15,23,42,0.55)] dark:border-white/[0.08] dark:bg-[#0F1117]">
          <div className="px-2 pb-2">
            <div className="text-[12px] font-medium uppercase tracking-[0.14em] text-black/35 dark:text-white/35">Быстрый вход</div>
          </div>
          <div className="space-y-1">
            {menuAccounts.map(account => {
              const active = account.id === currentUser.id || (account.id === "guest" && currentUser.role === "guest");
              return (
                <button
                  key={account.id}
                  onClick={() => choose(account.id)}
                  className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition-colors ${active ? "bg-[#E3E7FC] dark:bg-[#0E1A3A]" : "hover:bg-black/[0.03] dark:hover:bg-white/[0.04]"}`}
                >
                  <UserAvatarCircle src={account.id === "guest" ? undefined : readAvatarForUser(account.id)} name={account.name} email={account.email} size={40} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[14px] tracking-tight text-black dark:text-white">{account.name}</span>
                    <span className="block truncate text-[12px] tracking-tight text-black/50 dark:text-white/50">{roleTitle(account.role)} · {account.email}</span>
                  </span>
                  {active && <Check size={16} className="text-[#0056FF]" />}
                </button>
              );
            })}
          </div>
          <div className="my-2 h-px bg-black/[0.06] dark:bg-white/[0.06]" />
          <button onClick={() => { setOpen(false); navigate("/register"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.03] dark:text-white dark:hover:bg-white/[0.04]">
            <UserPlus size={16} className="text-[#0056FF]" /> Добавить пользователя
          </button>
          <button onClick={() => { setOpen(false); navigate("/profile"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.03] dark:text-white dark:hover:bg-white/[0.04]">
            <User size={16} className="text-black/45 dark:text-white/45" /> Профиль
          </button>
          <button onClick={() => { setOpen(false); navigate("/settings"); }} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-black transition-colors hover:bg-black/[0.03] dark:text-white dark:hover:bg-white/[0.04]">
            <Settings size={16} className="text-black/45 dark:text-white/45" /> Настройки
          </button>
          <button onClick={logout} className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[14px] tracking-tight text-red-500 transition-colors hover:bg-red-50 dark:hover:bg-red-500/10">
            <LogOut size={16} /> Выйти в гостевой режим
          </button>
          <button onClick={() => { resetSession(); setOpen(false); navigate("/"); }} className="mt-1 w-full rounded-2xl px-3 py-2 text-left text-[12px] tracking-tight text-black/45 transition-colors hover:bg-black/[0.03] dark:text-white/45 dark:hover:bg-white/[0.04]">
            Сбросить быстрый список до стандартных ролей
          </button>
        </div>
      )}
    </div>
  );
}

function DesktopTopBar({ onSearch, onNotifications }: { onSearch: () => void; onNotifications: () => void }) {
  return (
    <div className="flex items-center gap-4 border-b border-black/[0.06] bg-white/70 px-10 py-4 backdrop-blur dark:border-white/[0.06] dark:bg-[#0B0D13]/70">
      <button onClick={onSearch} className="flex h-11 min-w-0 flex-1 items-center gap-3 overflow-hidden rounded-2xl border border-black/[0.06] bg-[#F6F7FB] px-4 text-left dark:border-white/[0.06] dark:bg-white/[0.04]">
        <Search size={16} className="shrink-0 text-black/40 dark:text-white/40" />
        <span className="min-w-0 flex-1 truncate whitespace-nowrap text-[14px] tracking-tight text-black/40 dark:text-white/40">Какая у вас ситуация? Например: открыть ИП в Минске</span>
        <span className="shrink-0 rounded-md bg-black/[0.05] px-1.5 py-0.5 text-[10px] tracking-tight text-black/50 dark:bg-white/[0.08] dark:text-white/60">⌘ K</span>
      </button>
      <button onClick={onNotifications} className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white text-black shadow-sm dark:bg-white/[0.06] dark:text-white"><Bell size={16} /></button>
    </div>
  );
}

function DesktopHome({ onOpen }: { onOpen: (p: Page) => void }) {
  const navigate = useNavigate();
  const { situations, scenarioById, situationProgress, documents, utilityAccounts, taxes, settings, legal, currentUser } = useStore();

  const active = situations
    .map(s => { const sc = scenarioById(s.scenarioId); return sc ? { id: s.id, title: sc.title, category: sc.category, progress: situationProgress(s), status: s.status } : null; })
    .filter(Boolean) as { id: string; title: string; category: string; progress: number; status: string }[];
  const primary = active.find(s => s.status !== "done");
  const deadlines = buildReminders(documents, utilityAccounts, taxes, settings).slice(0, 4);
  const legalTop = legal.slice(0, 3);
  const docsTop = documents.slice(0, 3);
  const firstName = currentUser.role === "guest" ? "" : (currentUser.name || "").split(" ")[0];

  return (
    <>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Личный кабинет</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30, lineHeight: 1.1 }}>Добрый день{firstName ? `, ${firstName}` : ""}</div>
        </div>
        <div className="flex gap-2">
          <GhostButton className="h-10 px-4" onClick={() => onOpen("catalog")}>Каталог</GhostButton>
          <PrimaryButton className="h-10 px-4" onClick={() => onOpen("situations")}>Мои ситуации</PrimaryButton>
        </div>
      </div>

      <div className="mt-7 grid grid-cols-3 gap-5">
        {primary ? (
          <button onClick={() => navigate(`/situations/${primary.id}`)} className="col-span-2 overflow-hidden rounded-3xl p-6 text-left text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
            style={{ background: "radial-gradient(120% 100% at 0% 0%, #2277FF 0%, #0056FF 45%, #001A66 100%)" }}>
            <div className="flex items-center justify-between">
              <Pill tone="ghost"><span className="text-white/90">Активная ситуация</span></Pill>
              <span className="text-[12px] tracking-tight text-white/70">{primary.progress}% выполнено</span>
            </div>
            <div className="mt-4 max-w-[440px] tracking-tight" style={{ fontSize: 26, lineHeight: 1.15 }}>{primary.title}</div>
            <div className="mt-1 max-w-[440px] text-[13px] tracking-tight text-white/75">{catLabelApp(primary.category)} · продолжите выполнение задач по шагам.</div>
            <div className="mt-5 h-1.5 w-full overflow-hidden rounded-full bg-white/20">
              <motion.div initial={{ width: 0 }} animate={{ width: `${primary.progress}%` }} transition={{ duration: 1 }} className="h-full rounded-full bg-white" />
            </div>
            <div className="mt-5 flex items-center gap-3">
              <span className="rounded-xl bg-white px-4 py-2 text-[13px] tracking-tight text-[#0056FF]">Продолжить →</span>
              <span className="rounded-xl border border-white/25 px-4 py-2 text-[13px] tracking-tight text-white">{active.length} активных</span>
            </div>
          </button>
        ) : (
          <button onClick={() => onOpen("catalog")} className="col-span-2 flex flex-col items-start justify-center overflow-hidden rounded-3xl p-6 text-left text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
            style={{ background: "radial-gradient(120% 100% at 0% 0%, #2277FF 0%, #0056FF 45%, #001A66 100%)" }}>
            <Pill tone="ghost"><span className="text-white/90">Нет активных ситуаций</span></Pill>
            <div className="mt-4 max-w-[440px] tracking-tight" style={{ fontSize: 24, lineHeight: 1.2 }}>Выберите жизненный сценарий, чтобы начать</div>
            <span className="mt-5 rounded-xl bg-white px-4 py-2 text-[13px] tracking-tight text-[#0056FF]">Открыть каталог →</span>
          </button>
        )}

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">Ближайшие сроки</div>
            <button onClick={() => onOpen("notifications")} className="text-[11px] tracking-tight text-[#0056FF]">Все</button>
          </div>
          <div className="mt-3 space-y-3">
            {deadlines.length === 0 && <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">Ближайших сроков нет.</div>}
            {deadlines.map((x) => {
              const warn = (x.body || "").includes("просрочено");
              return (
                <div key={x.id} className="flex items-start gap-3">
                  <span className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-xl ${warn ? "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300" : "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"}`}>
                    <CalendarClock size={15} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate tracking-tight text-black dark:text-white">{x.title}</div>
                    <div className={`truncate text-[12px] tracking-tight ${warn ? "text-amber-600 dark:text-amber-400" : "text-black/55 dark:text-white/55"}`}>{x.body}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      <div className="mt-7">
        <div className="flex items-center justify-between">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 17 }}>Каталог помощи</div>
          <button onClick={() => onOpen("catalog")} className="text-[12px] tracking-tight text-[#0056FF]">Открыть все</button>
        </div>
        <div className="mt-3 grid grid-cols-6 gap-3">
          {[
            { i: <FileText size={18} />, n: "Документы", c: 28, r: "documents" as Page },
            { i: <Home size={18} />, n: "ЖКХ", c: 14, r: "finance" as Page },
            { i: <Wallet size={18} />, n: "Налоги", c: 19, r: "finance" as Page },
            { i: <Heart size={18} />, n: "Семья", c: 22, to: "/catalog?category=family&type=all" },
            { i: <Briefcase size={18} />, n: "Работа", c: 17, to: "/catalog?category=work&type=all" },
            { i: <Hammer size={18} />, n: "Здоровье", c: 12, to: "/catalog?category=health&type=all" },
          ].map((c) => (
            <button key={c.n} onClick={() => c.to ? navigate(c.to) : onOpen(c.r)}>
              <Card interactive className="p-4 text-left">
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{c.i}</span>
                <div className="mt-7 tracking-tight text-black dark:text-white">{c.n}</div>
                <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{c.c} материалов</div>
              </Card>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-7 grid grid-cols-3 gap-5">
        <Card className="col-span-2 p-5">
          <div className="flex items-center justify-between">
            <div className="tracking-tight text-black dark:text-white">Важное для вас</div>
            <button onClick={() => onOpen("legal")} className="text-[12px] tracking-tight text-[#0056FF]">Все обновления</button>
          </div>
          <div className="mt-4 divide-y divide-black/[0.06] dark:divide-white/[0.06]">
            {legalTop.length === 0 && <div className="text-[13px] tracking-tight text-black/45 dark:text-white/45">Обновлений пока нет.</div>}
            {legalTop.map((x) => (
              <button key={x.id} onClick={() => navigate(`/law-detail/${x.id}`)} className="flex w-full items-start gap-4 py-3.5 text-left first:pt-0 last:pb-0">
                <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                  <FileText size={15} />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <Pill tone="lavender">{catLabelApp(x.category)}</Pill>
                    {x.priority && <Pill tone="warn"><AlertCircle size={10} /> Важное</Pill>}
                    <span className="text-[11px] tracking-tight text-black/40 dark:text-white/40">{x.effectiveDate}</span>
                  </div>
                  <div className="mt-1.5 tracking-tight text-black dark:text-white">{x.title}</div>
                </div>
                <ArrowUpRight size={16} className="mt-1 shrink-0 text-black/35 dark:text-white/35" />
              </button>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div className="tracking-tight text-black dark:text-white">Документы</div>
            <button onClick={() => onOpen("documents")} className="text-[12px] tracking-tight text-[#0056FF]">Хранилище</button>
          </div>
          <div className="mt-3 space-y-2">
            {docsTop.length === 0 && <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">Документы не добавлены.</div>}
            {docsTop.map((d) => {
              const ok = d.status === "active";
              const sub = d.status === "expired" ? "Истёк" : d.status === "expiring" ? "Скоро истекает" : d.expiresAt ? `Действует до ${d.expiresAt}` : "Без срока";
              return (
                <div key={d.id} className="flex items-center gap-3 rounded-2xl bg-[#F6F7FB] px-3 py-2.5 dark:bg-white/[0.03]">
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${ok ? "bg-white text-[#0056FF] dark:bg-white/[0.06]" : "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300"}`}>
                    <Shield size={15} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate tracking-tight text-black dark:text-white">{d.title}</div>
                    <div className={`text-[11px] tracking-tight ${ok ? "text-black/45 dark:text-white/45" : "text-amber-600 dark:text-amber-400"}`}>{sub}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>
    </>
  );
}

function DesktopSituationsList({ onOpen }: { onOpen: () => void }) {
  const items = [
    { t: "Восстановление паспорта", c: "Документы", s: "Шаг 3 из 5", p: 60, status: "В процессе", warn: true },
    { t: "Открытие ИП", c: "Работа", s: "Шаг 1 из 9", p: 11, status: "В процессе", warn: false },
    { t: "Замена водительского", c: "Документы", s: "Не начато", p: 0, status: "Запланировано", warn: false },
    { t: "Получение медкнижки", c: "Здоровье", s: "Завершено", p: 100, status: "Готово", warn: false },
  ];
  return (
    <>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Личный кабинет</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Мои ситуации</div>
        </div>
        <PrimaryButton className="h-10 px-4">+ Новая ситуация</PrimaryButton>
      </div>
      <div className="mt-7 grid grid-cols-2 gap-4">
        {items.map(s => (
          <button key={s.t} onClick={onOpen} className="block text-left">
            <Card interactive className="p-5">
              <div className="flex items-center justify-between">
                <Pill tone="lavender">{s.c}</Pill>
                <Pill tone={s.p === 100 ? "ok" : s.warn ? "warn" : "ghost"}>{s.status}</Pill>
              </div>
              <div className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>{s.t}</div>
              <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{s.s}</div>
              <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
                <div className="h-full rounded-full" style={{ width: `${s.p}%`, background: s.p === 100 ? "#10B981" : "linear-gradient(90deg,#0056FF,#2277FF)" }} />
              </div>
              <div className="mt-3 flex items-center justify-between text-[12px] tracking-tight text-black/55 dark:text-white/55">
                {s.warn ? <span className="text-amber-600 dark:text-amber-400">Срок 14 дней</span> : <span>Без срока</span>}
                <span className="text-[#0056FF]">Открыть →</span>
              </div>
            </Card>
          </button>
        ))}
      </div>
    </>
  );
}

function DesktopSituationDetail({ onBack }: { onBack: () => void }) {
  const steps = [
    { n: "Получить справку об утере", state: "done", when: "12 мая · Готово", where: "РОВД Первомайского района" },
    { n: "Сделать фото 4×5 на паспорт", state: "done", when: "15 мая · Готово", where: "Фотосалон или дома" },
    { n: "Подать заявление в РОВД", state: "now", when: "Сегодня", where: "РОВД по месту жительства · ул. Кальварийская, 14" },
    { n: "Оплатить госпошлину", state: "lock", when: "После шага 3", where: "Беларусбанк · ЕРИП код 12345" },
    { n: "Получить новый паспорт", state: "lock", when: "Через 14 дней", where: "РОВД Первомайского района" },
  ];
  return (
    <>
      <button onClick={onBack} className="inline-flex items-center gap-1.5 text-[13px] tracking-tight text-black/55 dark:text-white/55">
        <ChevronLeft size={14} /> Мои ситуации
      </button>

      <div className="mt-3 grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <Pill tone="lavender">Документы</Pill>
          <div className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 36, lineHeight: 1.05 }}>Восстановление паспорта</div>
          <p className="mt-2 max-w-[600px] tracking-tight text-black/60 dark:text-white/60">
            Пошаговый план для жителей г. Минск. Учитывает все требования МВД и сроки выдачи.
          </p>

          <Card className="mt-6 p-5">
            <div className="flex items-center justify-between text-[12px] tracking-tight text-black/55 dark:text-white/55">
              <span>Прогресс: 3 из 5 шагов</span><span>60%</span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
              <motion.div initial={{ width: 0 }} animate={{ width: "60%" }} transition={{ duration: 1 }} className="h-full rounded-full" style={{ background: "linear-gradient(90deg,#0056FF,#2277FF)" }} />
            </div>
          </Card>

          <div className="mt-6 tracking-tight text-black dark:text-white" style={{ fontSize: 18 }}>Пошаговый план</div>
          <div className="relative mt-4">
            <div className="absolute left-[15px] bottom-2 top-2 w-px bg-black/10 dark:bg-white/10" />
            <div className="space-y-3">
              {steps.map((s, i) => (
                <div key={i} className="relative pl-10">
                  <div className="absolute left-0 top-3 grid h-8 w-8 place-items-center rounded-full"
                    style={{
                      background: s.state === "done" ? "linear-gradient(135deg,#0056FF,#2277FF)" : s.state === "now" ? "white" : "transparent",
                      boxShadow: s.state === "now" ? "0 0 0 2px #0056FF, 0 0 0 6px #E3E7FC" : "none",
                    }}>
                    {s.state === "done" && <Check size={16} className="text-white" strokeWidth={2.6} />}
                    {s.state === "now" && <span className="h-2 w-2 rounded-full bg-[#0056FF]" />}
                    {s.state === "lock" && <Lock size={14} className="text-black/35 dark:text-white/30" />}
                  </div>
                  <Card className={`p-5 ${s.state === "lock" ? "opacity-60" : ""}`}>
                    <div className="flex items-center gap-2">
                      {s.state === "now" && <Pill tone="royal">Сейчас</Pill>}
                      {s.state === "done" && <Pill tone="ok">Выполнено</Pill>}
                      <span className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{s.when}</span>
                    </div>
                    <div className="mt-2 tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{s.n}</div>
                    <div className="mt-1 flex items-center gap-1.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                      <MapPin size={12} /> {s.where}
                    </div>
                    {s.state === "now" && (
                      <div className="mt-4 flex items-center gap-2">
                        <PrimaryButton className="h-10 px-4">Я сделал(а)</PrimaryButton>
                        <GhostButton className="h-10 px-4">Скачать шаблон</GhostButton>
                      </div>
                    )}
                  </Card>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <Card className="p-5">
            <div className="tracking-tight text-black dark:text-white">Куда обращаться</div>
            <div className="mt-3 rounded-2xl bg-[#F6F7FB] p-4 dark:bg-white/[0.03]">
              <div className="flex items-start gap-3">
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                  <Building2 size={16} />
                </span>
                <div>
                  <div className="tracking-tight text-black dark:text-white">РОВД Первомайского района</div>
                  <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">ул. Кальварийская, 14, Минск</div>
                  <div className="mt-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">Пн–Пт · 9:00–18:00</div>
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <div className="tracking-tight text-black dark:text-white">Документы</div>
            <div className="mt-3 space-y-2">
              {["Справка об утере","Фото 4×5 (2 шт.)","Квитанция об оплате","Заявление по форме"].map(d => (
                <div key={d} className="flex items-center gap-2 text-[13px] tracking-tight text-black/70 dark:text-white/70">
                  <Check size={14} className="text-[#0056FF]" /> {d}
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <div className="tracking-tight text-black dark:text-white">Сколько стоит</div>
            <div className="mt-2 tracking-tight text-black dark:text-white" style={{ fontSize: 24 }}>2 базовые величины</div>
            <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">≈ 74 BYN · оплата через ЕРИП</div>
          </Card>
        </div>
      </div>
    </>
  );
}

function DesktopCatalog({ onOpen, onOpenScenario }: { onOpen: () => void; onOpenScenario?: (id: string) => void }) {
  const { scenarios } = useStore();
  const events = [
    { i: <Baby size={20} />, n: "Рождение ребёнка", c: "12 шагов", cat: "Семья" },
    { i: <Home size={20} />, n: "Переезд", c: "8 шагов", cat: "Жильё" },
    { i: <FileText size={20} />, n: "Потеря паспорта", c: "5 шагов", cat: "Документы" },
    { i: <Building2 size={20} />, n: "Покупка жилья", c: "14 шагов", cat: "Жильё" },
    { i: <Briefcase size={20} />, n: "Открытие ИП", c: "9 шагов", cat: "Работа" },
    { i: <Hammer size={20} />, n: "��вольнение", c: "6 шагов", cat: "Работа" },
    { i: <Heart size={20} />, n: "Брак", c: "7 шагов", cat: "Семья" },
    { i: <Shield size={20} />, n: "Медкнижка", c: "4 шага", cat: "Здоровье" },
  ];
  return (
    <>
      <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Каталог</div>
      <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Жизненные ситуации</div>
      <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">
        Каждая ситуация — готовый план действий с документами, сроками и контактами учреждений.
      </p>
      <div className="mt-6 flex flex-wrap gap-2">
        {["Все","Документы","Жильё","Семья","Работа","Здоровье","Налоги"].map((t,i) => (
          <span key={t} className={`rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${i===0 ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{t}</span>
        ))}
      </div>
      <div className="mt-6 grid grid-cols-4 gap-4">
        {events.map((e, i) => (
          <button key={e.n} onClick={() => onOpenScenario && scenarios[i % scenarios.length] ? onOpenScenario(scenarios[i % scenarios.length].id) : onOpen()}>
            <Card interactive className="p-5 text-left">
              <div className="grid h-12 w-12 place-items-center rounded-2xl" style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>{e.i}</div>
              <div className="mt-8 tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{e.n}</div>
              <div className="mt-0.5 text-[12px] tracking-tight text-black/50 dark:text-white/50">{e.cat} · {e.c}</div>
            </Card>
          </button>
        ))}
      </div>
    </>
  );
}

function DesktopDocs({ onAdd }: { onAdd?: () => void }) {
  return (
    <>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Хранилище</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Мои документы</div>
          <div className="mt-2 flex items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
            <Shield size={13} className="text-emerald-600 dark:text-emerald-400" />
            Хранится локально, зашифровано · доступ только у вас
          </div>
        </div>
        <PrimaryButton className="h-10 px-4" onClick={onAdd}>+ Добавить документ</PrimaryButton>
      </div>

      <div className="mt-7 grid grid-cols-3 gap-5">
        <div className="overflow-hidden rounded-3xl p-6 text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
          style={{ background: "linear-gradient(135deg,#000000 0%,#001A66 50%,#0056FF 100%)" }}>
          <div className="flex items-center justify-between">
            <span className="text-[12px] tracking-tight text-white/70">Паспорт гражданина РБ</span>
            <button className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-[11px] tracking-tight backdrop-blur">
              <EyeOff size={12} /> Скрыть
            </button>
          </div>
          <div className="mt-8 tracking-tight">Иванов Алексей</div>
          <div className="mt-1 font-mono text-[13px] tracking-[0.2em] text-white/70">MP •••• •••• 4821</div>
          <div className="mt-6 grid grid-cols-3 gap-2 text-[11px] tracking-tight text-white/60">
            <div><div>Выдан</div><div className="mt-0.5 text-white">2021</div></div>
            <div><div>Действует</div><div className="mt-0.5 text-white">до 2031</div></div>
            <div><div>Орган</div><div className="mt-0.5 text-white">РОВД Мин.</div></div>
          </div>
        </div>

        {[
          { n: "Медкнижка", s: "Действует до 12 авг 2027", warn: false },
          { n: "Водительское удостоверение", s: "Истекает через 6 месяцев", warn: true },
        ].map((d) => (
          <Card key={d.n} className="p-5">
            <div className="flex items-center justify-between">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <FileText size={18} />
              </span>
              {d.warn && <Pill tone="warn">Скоро истекает</Pill>}
            </div>
            <div className="mt-6 tracking-tight text-black dark:text-white" style={{ fontSize: 16 }}>{d.n}</div>
            <div className={`text-[12px] tracking-tight ${d.warn ? "text-amber-600 dark:text-amber-400" : "text-black/55 dark:text-white/55"}`}>{d.s}</div>
          </Card>
        ))}
      </div>

      <Card className="mt-5 p-0">
        <table className="w-full">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-[0.12em] text-black/40 dark:text-white/40">
              <th className="px-5 py-3">Документ</th>
              <th className="py-3">Тип</th>
              <th className="py-3">Действует до</th>
              <th className="py-3">Статус</th>
              <th className="py-3"></th>
            </tr>
          </thead>
          <tbody className="text-[13px] tracking-tight text-black dark:text-white">
            {[
              { n: "Свидетельство о рождении ребёнка", t: "Семья", d: "Бессрочно", ok: true },
              { n: "ИНН / Налоговая карта", t: "Налоги", d: "Бессрочно", ok: true },
              { n: "Полис страхования жилья", t: "Жильё", d: "до 31 дек 2026", ok: true },
              { n: "Военный билет", t: "Документы", d: "Бессрочно", ok: true },
            ].map(r => (
              <tr key={r.n} className="border-t border-black/[0.05] dark:border-white/[0.05]">
                <td className="px-5 py-3.5">{r.n}</td>
                <td className="py-3.5"><Pill tone="lavender">{r.t}</Pill></td>
                <td className="py-3.5 text-black/65 dark:text-white/65">{r.d}</td>
                <td className="py-3.5"><Pill tone="ok"><Check size={11} /> Активен</Pill></td>
                <td className="py-3.5 pr-5 text-right"><ChevronRight size={15} className="inline text-black/35 dark:text-white/35" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}

function DesktopLegalFeed() {
  const items = [
    { t: "Налоги", title: "Новый порядок имущественного вычета для семей с детьми", d: "с 1 июля 2026", priority: true, you: true, desc: "Семьи с двумя и более детьми смогут вернуть до 13% от стоимости приобретённого жилья." },
    { t: "ЖКХ", title: "Изменение тарифов на отопление в г. Минск", d: "с 1 октября 2026", priority: false, you: true, desc: "Тарифы пересмотрены в соответствии с решением Минского горисполкома." },
    { t: "Документы", title: "Электронный паспорт: запуск второй очереди", d: "с 15 сентября 2026", priority: true, you: false, desc: "Возможность получить ID-карту в МФЦ всех областных центров." },
    { t: "Семья", title: "Расширение списка получателей детских пособий", d: "с 1 января 2027", priority: false, you: false, desc: "Включены семьи с приёмными детьми и опекуны." },
  ];
  return (
    <>
      <div className="text-[13px] tracking-tight text-black/50 dark:text-white/50">Лента</div>
      <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Важное для вас</div>
      <p className="mt-2 max-w-[560px] tracking-tight text-black/60 dark:text-white/60">
        Правовые обновления, подобранные по вашему профилю, городу и текущим ситуациям.
      </p>
      <div className="mt-6 flex flex-wrap gap-2">
        {["Все","Налоги","ЖКХ","Документы","Семья","Работа"].map((t,i) => (
          <span key={t} className={`rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${i===0 ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{t}</span>
        ))}
      </div>
      <div className="mt-6 grid grid-cols-2 gap-4">
        {items.map(it => (
          <Card key={it.title} interactive className="p-5">
            <div className="flex items-center gap-2 flex-wrap">
              <Pill tone="lavender">{it.t}</Pill>
              {it.priority && <Pill tone="warn"><AlertCircle size={11} /> Важное</Pill>}
              {it.you && <Pill tone="ok">Касается вас</Pill>}
            </div>
            <div className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 18, lineHeight: 1.25 }}>{it.title}</div>
            <p className="mt-2 text-[13px] tracking-tight text-black/60 dark:text-white/60">{it.desc}</p>
            <div className="mt-4 flex items-center justify-between text-[12px] tracking-tight text-black/50 dark:text-white/50">
              <span className="inline-flex items-center gap-1.5"><Clock size={12} /> {it.d}</span>
              <span className="inline-flex items-center gap-1 text-[#0056FF]">Подробнее <ArrowUpRight size={12} /></span>
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}

function DesktopNotif() {
  return (
    <>
      <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Уведомления</div>
      <div className="mt-6 space-y-5">
        {[
          { title: "Сегодня", items: [
            { i: <CalendarClock size={15} />, t: "Срок оплаты налога — через 14 дней", s: "Налог на недвижимость", tone: "warn" },
            { i: <FileText size={15} />, t: "Опубликовано новое правовое обновление", s: "Налоги · касается вас", tone: "lav" },
          ]},
          { title: "Вчера", items: [
            { i: <Check size={15} />, t: "Шаг выполнен: справка получена", s: "Восстановление паспорта", tone: "ok" },
            { i: <Shield size={15} />, t: "Срок действия водительского — 6 мес", s: "Документы", tone: "warn" },
          ]},
        ].map(g => (
          <div key={g.title}>
            <div className="mb-2 text-[12px] tracking-tight text-black/45 dark:text-white/45">{g.title}</div>
            <div className="grid grid-cols-2 gap-3">
              {g.items.map((it, i) => (
                <Card key={i} className="flex items-start gap-3 p-4">
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${
                    it.tone === "warn" ? "bg-amber-50 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300" :
                    it.tone === "ok" ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300" :
                    "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"
                  }`}>{it.i}</span>
                  <div className="flex-1">
                    <div className="tracking-tight text-black dark:text-white">{it.t}</div>
                    <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">{it.s}</div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function DesktopProfile({ onSettings, onLearning }: { onSettings?: () => void; onLearning?: () => void }) {
  return (
    <>
      <div className="flex items-end justify-between">
        <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 30 }}>Профиль и настройки</div>
        <div className="flex gap-2">
          <GhostButton className="h-10 px-4" onClick={onLearning}>Обучение</GhostButton>
          <PrimaryButton className="h-10 px-4" onClick={onSettings}>Настройки</PrimaryButton>
        </div>
      </div>
      <div className="mt-6 grid grid-cols-3 gap-5">
        <Card className="col-span-1 p-5">
          <div className="flex items-center gap-3">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-[#0056FF] to-[#2277FF]" />
            <div>
              <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 17 }}>Алексей Иванов</div>
              <div className="text-[12px] tracking-tight text-black/55 dark:text-white/55">aleksei@example.by</div>
            </div>
          </div>
          <div className="mt-5 space-y-2 text-[13px] tracking-tight text-black/70 dark:text-white/70">
            <div className="flex items-center justify-between"><span>Область</span><span className="text-black dark:text-white">Минская</span></div>
            <div className="flex items-center justify-between"><span>Район</span><span className="text-black dark:text-white">Первомайский</span></div>
            <div className="flex items-center justify-between"><span>Город</span><span className="text-black dark:text-white">Минск</span></div>
          </div>
          <GhostButton className="mt-5 h-10 w-full">Редактировать</GhostButton>
        </Card>

        <Card className="col-span-2 p-5">
          <div className="tracking-tight text-black dark:text-white">Статусы и интересы</div>
          <div className="mt-1 text-[12px] tracking-tight text-black/55 dark:text-white/55">Помогает подбирать правовые обновления и нужные ситуации</div>
          <div className="mt-4 flex flex-wrap gap-2">
            {["Собственник жилья","Есть дети","Арендатор","ИП","Студент","Пенсионер","Авто","Самозанятость"].map((t,i) => (
              <span key={t} className={`rounded-full px-3.5 py-1.5 text-[12px] tracking-tight ${i<3 ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "bg-white text-black/55 dark:bg-white/[0.04] dark:text-white/55"}`}>{t}</span>
            ))}
          </div>

          <div className="mt-7 tracking-tight text-black dark:text-white">Доступность и уведомления</div>
          <div className="mt-3 grid grid-cols-2 gap-x-6">
            {[
              { l: "Большой шрифт", on: false },
              { l: "Высокий контраст", on: false },
              { l: "Скрыть личные данные", on: true },
              { l: "Уведомления о сроках", on: true },
              { l: "Правовые обновления", on: true },
              { l: "Push-уведомления", on: false },
            ].map((s, i) => (
              <div key={i} className="flex items-center justify-between py-2.5">
                <span className="tracking-tight text-black/75 dark:text-white/75">{s.l}</span>
                <div className={`relative h-6 w-11 rounded-full transition-colors ${s.on ? "bg-[#0056FF]" : "bg-black/10 dark:bg-white/15"}`}>
                  <motion.div layout className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow ${s.on ? "left-[22px]" : "left-0.5"}`} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </>
  );
}

/* ============================================================
   ROOT LAYOUT AND APP
   ============================================================ */
import React from 'react';
export type ThemeMode = "light" | "dark" | "system";
export const ShellContext = React.createContext<{ isMobile: boolean; dark: boolean; setDark: (d: boolean) => void; themeMode: ThemeMode; setThemeMode: (m: ThemeMode) => void; openAssistant: () => void; adminOpen: boolean; adminSignal: number; openAdmin: () => void; closeAdmin: () => void }>({ isMobile: false, dark: false, setDark: () => {}, themeMode: "system", setThemeMode: () => {}, openAssistant: () => {}, adminOpen: false, adminSignal: 0, openAdmin: () => {}, closeAdmin: () => {} });

function AssistantFab() {
  const { openAssistant } = React.useContext(ShellContext);
  return (
    <button
      onClick={openAssistant}
      aria-label="ИИ-помощник"
      className="fixed bottom-6 right-6 z-[55] grid h-14 w-14 place-items-center rounded-full bg-[#0056FF] text-white shadow-[0_18px_44px_-12px_rgba(0,86,255,0.75)] transition-transform hover:scale-105 active:scale-95"
    >
      <Sparkles size={22} />
    </button>
  );
}

// Гость на '/' -> /welcome (лендинг). Остальное гость смотрит read-only;
// действия, требующие аккаунт (создать ситуацию, сохранить, добавить документ),
// гейтятся guest-guard модалкой через requireAccount/protectedGuard.
// /onboarding оставлен для залогиненных (первый запуск после регистрации).
function OnboardingGate() {
  const { role } = useStore();
  const navigate = useNavigate();
  const location = useLocation();
  useEffect(() => {
    if (role !== "guest") return;
    if (location.pathname === "/") navigate("/welcome", { replace: true });
  }, [role, location.pathname, navigate]);
  return null;
}

/* v1.1 (P8): AccessibilityBridge — применяет настройки к DOM.
   Должен рендериться ВНУТРИ <AppStoreProvider>, поэтому это отдельный
   компонент, который <RootLayout> вкладывает сразу после провайдера. */
function AccessibilityBridge() {
  const { settings } = useStore();
  useEffect(() => {
    applyAccessibilitySettings(settings);
  }, [settings]);
  return null;
}

/* При смене маршрута страница обязана открываться сверху, а не на позиции
   скролла предыдущей. Сбрасываем и окно (mobile native scroll), и desktop-
   контейнер [data-scroll-root]. Рендерит null — живёт в дереве RootLayout. */
function ScrollResetBridge() {
  const location = useLocation();
  useEffect(() => {
    scrollContentToTop("auto");
  }, [location.pathname]);
  return null;
}

export function RootLayout() {
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    try { return (localStorage.getItem("themeMode") as ThemeMode) || "system"; } catch { return "system"; }
  });
  const [systemDark, setSystemDark] = useState(() => {
    try { return window.matchMedia("(prefers-color-scheme: dark)").matches; } catch { return false; }
  });

  const [layout, setLayout] = useState<"mobile" | "tablet" | "desktop">("desktop");
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const [adminSignal, setAdminSignal] = useState(0);
  const isMobile = layout === "mobile";
  const location = useLocation();
  const isAuthRoute = isAuthPage(location.pathname);

  const dark = themeMode === "dark" || (themeMode === "system" && systemDark);
  const setDark = (d: boolean) => setThemeMode(d ? "dark" : "light");

  useEffect(() => {
    try { localStorage.setItem("themeMode", themeMode); } catch { /* ignore */ }
  }, [themeMode]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e: MediaQueryListEvent) => setSystemDark(e.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  useEffect(() => {
    const check = () => {
      const w = window.innerWidth;
      setLayout(w < 768 ? "mobile" : w < 1200 ? "tablet" : "desktop");
    };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  return (
    <AppStoreProvider>
      <ShellContext.Provider value={{ isMobile, dark, setDark, themeMode, setThemeMode, openAssistant: () => setAssistantOpen(true), adminOpen, adminSignal, openAdmin: () => { setAdminOpen(true); setAdminSignal(s => s + 1); }, closeAdmin: () => setAdminOpen(false) }}>
        {/* v1.1 (P8): применяем font-scale / high-contrast, когда меняются
            настройки пользователя. Этот компонент обязан рендериться ВНУТРИ
            <AppStoreProvider>, поэтому живёт в return-дереве RootLayout, а не
            в его теле. */}
        <AccessibilityBridge />
        <ScrollResetBridge />
        <GuestGuardBridge />
        <OnboardingGate />
        <SystemBanner />
        <MaintenanceScreen />
        <div className={dark ? "dark" : ""}>
          <div className="size-full bg-[#F4F5FA] text-black dark:bg-[#05060A] dark:text-white">
            {layout === "mobile" ? <MobileShell dark={dark} setDark={setDark} />
              : layout === "desktop" ? <DesktopHeaderShell />
              // На tablet на /login, /register, /welcome — без боковой DesktopShell
              // (там рисуется только центрированная auth-карточка). На остальных
              // страницах tablet = DesktopShell с левым сайдбаром.
              : isAuthRoute ? <DesktopAuthShell />
              : <DesktopShell dark={dark} setDark={setDark} />}
            <AssistantPanel open={assistantOpen} onClose={() => setAssistantOpen(false)} />
            {!isMobile && <AssistantFab />}
            <AdminWindowMount />
            <ControlCenter />
          </div>
        </div>
      </ShellContext.Provider>
    </AppStoreProvider>
  );
}

/* Tablet-режим на auth-страницах (/login, /register, /welcome): без боковой
   DesktopShell и без шапки. Только центрированный контент auth-формы на
   нейтральном фоне. */
function DesktopAuthShell() {
  const location = useLocation();
  return (
    <div className="flex min-h-[100dvh] items-center justify-center bg-[#F4F5FA] p-6 dark:bg-[#05060A]">
      <div className="w-full max-w-[440px]">
        <div className="mb-6 flex items-center justify-center">
          <Logo size={36} />
        </div>
        {/* Здесь Outlet рендерится через <Outlet /> в RootLayout? Нет — RootLayout
            рендерит <Outlet /> внутри выбранного shell-компонента. Чтобы не ломать
            текущий контракт, передаём pathname, чтобы страница могла его
            использовать. Но в нашей текущей структуре auth-shell должен сам
            рендерить <Outlet />. */}
        <Outlet key={location.pathname} />
      </div>
    </div>
  );
}

export {
  MobileHome, MobileSituations, MobileSituationDetail, MobileDocuments, MobileLegal, MobileNotifications, MobileProfile, MobileCatalog,
  DesktopHome, DesktopSituationsList, DesktopSituationDetail, DesktopDocs, DesktopLegalFeed, DesktopNotif, DesktopProfile, DesktopCatalog
};

export default function App() {
  return <RouterProvider router={router} />;
}
