import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";
import { startHealthLoop } from "./app/services/connection";
import "./styles/index.css";

// Фоновый health-ping до рендера — баннер связи корректен с холодного старта.
startHealthLoop();

const rootEl = document.getElementById("root")!;
createRoot(rootEl).render(<App />);
