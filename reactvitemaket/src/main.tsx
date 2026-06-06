import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";
import { ServerPicker } from "./app/ServerPicker.tsx";
import "./styles/index.css";

const rootEl = document.getElementById("root")!;
createRoot(rootEl).render(
  <>
    <ServerPicker />
    <App />
  </>,
);
