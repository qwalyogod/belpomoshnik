import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";
import { ServerPicker } from "./app/ServerPicker.tsx";
import { startBackgroundHealthLoop } from "./app/services/connection";
import "./styles/index.css";

// Запускаем фоновый health-ping ДО React-рендера, чтобы при cold start
// на capacitor://localhost он уже работал и сбрасывал залипший баннер.
startBackgroundHealthLoop();

const rootEl = document.getElementById("root")!;
createRoot(rootEl).render(
  <>
    <ServerPicker />
    <App />
  </>,
);
