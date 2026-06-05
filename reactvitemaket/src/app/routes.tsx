import React from "react";
import { createBrowserRouter, useOutletContext, useParams, useNavigate } from "react-router";
import { useStore } from "./data/store";
import { ShellContext, RootLayout } from "./App";
import { MobileHome, DesktopHome } from "./App";
import { AdminPanel } from "./components/desktop";
import { ScenarioDetail, MySituationDetail, SettingsPage, LearningPage } from "./components/extra-screens";
import { CatalogPage, SituationsPage, DocumentsPage, LegalPage, LawDetailPage, NotificationsPage, ProfilePage, ProblemDetailPage, LoginPage, RegisterPage, AboutPage, ProblemsPage, FinancePage, NewsPage } from "./pages";

function ResponsivePage({ mobile: MobileComp, desktop: DesktopComp }: { mobile: React.ElementType; desktop: React.ElementType }) {
  const { isMobile, dark, setDark } = React.useContext(ShellContext);
  const navigate = useNavigate();
  const context = useOutletContext<any>();
  
  if (isMobile) {
    return <MobileComp dark={dark} setDark={setDark} onNavigate={(p: string) => navigate(`/${p === 'home' ? '' : p}`)} onBack={() => navigate(-1)} onOpen={() => navigate('/situations/1')} {...context} />;
  }
  return <DesktopComp dark={dark} setDark={setDark} onOpen={(p: string) => navigate(`/${p === 'home' ? '' : p}`)} onBack={() => navigate(-1)} onLearning={() => navigate('/learning')} onSettings={() => navigate('/settings')} {...context} />;
}

function ScenarioPageWrapper() {
  const { id } = useParams<{ id: string }>();
  const { scenarioById, loadScenarioDetail } = useStore();
  const navigate = useNavigate();
  const context = useOutletContext<any>();
  const [loadingDetail, setLoadingDetail] = React.useState(false);
  
  const scenario = id ? scenarioById(id) : undefined;

  React.useEffect(() => {
    if (!id || (scenario && scenario.stages.length > 0)) return;
    let active = true;
    setLoadingDetail(true);
    loadScenarioDetail(id)
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoadingDetail(false);
      });
    return () => {
      active = false;
    };
  }, [id, scenario?.stages.length, loadScenarioDetail]);

  if (!scenario && loadingDetail) {
    return <div className="p-10 text-black/60 dark:text-white/60">Загружаем сценарий...</div>;
  }

  if (!scenario) return <div className="p-10">Сценарий не найден</div>;
  
  return (
    <ScenarioDetail 
      scenario={scenario} 
      onBack={() => navigate(-1)} 
      onOpenMySituation={(sId) => navigate(`/situations/${sId}`)}
      onOpenScenario={(sId) => navigate(`/scenarios/${sId}`)}
      onProtected={context?.protectedGuard ?? (() => true)}
    />
  );
}

function SettingsWrapper() {
  const { themeMode, setThemeMode } = React.useContext(ShellContext);
  return <SettingsPage themeMode={themeMode} setThemeMode={setThemeMode} />;
}

function AdminPageWrapper() {
  const { role } = useStore();
  const navigate = useNavigate();

  if (role !== "admin") {
    return (
      <div className="mx-auto w-full max-w-[720px] px-5 py-10">
        <div className="rounded-[28px] border border-black/[0.08] bg-white p-6 shadow-[0_18px_60px_-42px_rgba(15,23,42,0.45)] dark:border-white/[0.08] dark:bg-white/[0.04]">
          <div className="text-[12px] font-medium uppercase tracking-[0.14em] text-[#0056FF]">Доступ ограничен</div>
          <h1 className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 28, lineHeight: 1.1 }}>
            Админ-панель доступна только администратору
          </h1>
          <p className="mt-3 max-w-[560px] text-[15px] leading-relaxed text-black/60 dark:text-white/60">
            Для просмотра раздела переключитесь на пользователя с ролью администратора или войдите в соответствующий аккаунт.
          </p>
          <button
            type="button"
            onClick={() => navigate("/")}
            className="mt-5 rounded-2xl bg-[#0056FF] px-5 py-3 text-[14px] font-medium tracking-tight text-white shadow-[0_16px_34px_-22px_rgba(0,86,255,0.75)]"
          >
            Вернуться на главную
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1320px] px-5 py-8">
      <AdminPanel />
    </div>
  );
}

function EditorPageWrapper() {
  const { role } = useStore();
  const navigate = useNavigate();

  if (role !== "editor" && role !== "admin") {
    return (
      <div className="mx-auto w-full max-w-[720px] px-5 py-10">
        <div className="rounded-[28px] border border-black/[0.08] bg-white p-6 shadow-[0_18px_60px_-42px_rgba(15,23,42,0.45)] dark:border-white/[0.08] dark:bg-white/[0.04]">
          <div className="text-[12px] font-medium uppercase tracking-[0.14em] text-[#0056FF]">Доступ ограничен</div>
          <h1 className="mt-3 tracking-tight text-black dark:text-white" style={{ fontSize: 28, lineHeight: 1.1 }}>
            Редакторская панель доступна редактору контента
          </h1>
          <p className="mt-3 max-w-[560px] text-[15px] leading-relaxed text-black/60 dark:text-white/60">
            Для работы с материалами переключитесь на пользователя с ролью редактора или администратора.
          </p>
          <button
            type="button"
            onClick={() => navigate("/")}
            className="mt-5 rounded-2xl bg-[#0056FF] px-5 py-3 text-[14px] font-medium tracking-tight text-white shadow-[0_16px_34px_-22px_rgba(0,86,255,0.75)]"
          >
            Вернуться на главную
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[1320px] px-5 py-8">
      <AdminPanel editor />
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    Component: RootLayout,
    children: [
      { index: true, element: <ResponsivePage mobile={MobileHome} desktop={DesktopHome} /> },
      { path: "situations", element: <SituationsPage /> },
      { path: "situations/:id", element: <MySituationPageWrapper /> },
      { path: "catalog", element: <CatalogPage /> },
      { path: "scenarios", element: <CatalogPage /> },
      { path: "scenarios/:id", element: <ScenarioPageWrapper /> },
      { path: "documents", element: <DocumentsPage /> },
      { path: "finance", element: <FinancePage /> },
      { path: "legal", element: <LegalPage /> },
      { path: "news", element: <NewsPage /> },
      { path: "law-detail/:id", element: <LawDetailPage /> },
      { path: "notifications", element: <NotificationsPage /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "settings", element: <SettingsWrapper /> },
      { path: "learning", element: <LearningPage /> },
      { path: "problem-detail/:id", element: <ProblemDetailPage /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      { path: "about", element: <AboutPage /> },
      { path: "problems", element: <ProblemsPage /> },
      { path: "admin", element: <AdminPageWrapper /> },
      { path: "editor", element: <EditorPageWrapper /> }
    ]
  }
]);

function MySituationPageWrapper() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  if (!id) return null;
  return <MySituationDetail situationId={id} onBack={() => navigate(-1)} />;
}
