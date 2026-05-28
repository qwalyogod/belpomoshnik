import React from 'react';
import { createBrowserRouter, useRouteError } from "react-router";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import { Catalog } from "./pages/Catalog";
import { ProblemDetails } from "./pages/ProblemDetails";
import { MySituations } from "./pages/MySituations";
import { SituationDetails } from "./pages/SituationDetails";
import { MyDocuments } from "./pages/MyDocuments";
import { Notifications } from "./pages/Notifications";
import { Laws } from "./pages/Laws";
import { LawDetails } from "./pages/LawDetails";
import { Profile } from "./pages/Profile";
import { Admin } from "./pages/Admin";

function ErrorBoundary() {
  let error = useRouteError() as any;
  console.error(error);
  return (
    <div className="p-10 text-red-500">
      <h1 className="text-2xl font-bold">Error</h1>
      <pre className="mt-4 bg-red-50 p-4 rounded">{error?.message || String(error)}</pre>
      <pre className="mt-2 text-xs text-gray-500">{error?.stack}</pre>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    ErrorBoundary: ErrorBoundary,
    children: [
      { index: true, Component: Home },
      { path: "catalog", Component: Catalog },
      { path: "problem/:id", Component: ProblemDetails },
      { path: "situations", Component: MySituations },
      { path: "situations/:id", Component: SituationDetails },
      { path: "documents", Component: MyDocuments },
      { path: "notifications", Component: Notifications },
      { path: "laws", Component: Laws },
      { path: "laws/:id", Component: LawDetails },
      { path: "profile", Component: Profile },
      { path: "admin", Component: Admin },
      { path: "*", Component: () => <div className="text-center py-20 text-2xl font-bold text-gray-500">Страница не найдена 404</div> },
    ],
  },
]);
