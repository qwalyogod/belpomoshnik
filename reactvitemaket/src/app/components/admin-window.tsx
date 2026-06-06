import React, { useCallback, useEffect, useRef, useState } from "react";
import { X, Maximize2, Minimize2 } from "lucide-react";
import { AdminPanel } from "./desktop";
import { useStore } from "../data/store";
import { ShellContext } from "../App";

const WIN = { w: 1060, h: 700 };

function AdminWindow({ open, isMobile, editor, signal, onClose }: { open: boolean; isMobile: boolean; editor: boolean; signal: number; onClose: () => void }) {
  const [maximized, setMaximized] = useState(false);
  const [pos, setPos] = useState({ x: 80, y: 60 });
  const [animating, setAnimating] = useState(false);
  const drag = useRef<{ sx: number; sy: number; ox: number; oy: number } | null>(null);

  const center = useCallback(() => {
    const w = WIN.w;
    const h = Math.min(WIN.h, window.innerHeight - 40);
    setPos({ x: Math.max(8, (window.innerWidth - w) / 2), y: Math.max(8, (window.innerHeight - h) / 2) });
    setAnimating(true);
    window.setTimeout(() => setAnimating(false), 360);
  }, []);

  // Center on open + recenter every time the trigger fires (signal bump),
  // which also recovers a window dragged off-screen.
  useEffect(() => {
    if (open && !isMobile) center();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signal, open, isMobile]);

  const onHeaderDown = (e: React.MouseEvent) => {
    if (maximized || isMobile) return;
    drag.current = { sx: e.clientX, sy: e.clientY, ox: pos.x, oy: pos.y };
    const move = (ev: MouseEvent) => {
      if (!drag.current) return;
      setPos({ x: drag.current.ox + ev.clientX - drag.current.sx, y: drag.current.oy + ev.clientY - drag.current.sy });
    };
    const up = () => {
      drag.current = null;
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
    };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  if (!open) return null;
  const fullscreen = isMobile || maximized;
  const style: React.CSSProperties = fullscreen
    ? {}
    : { left: pos.x, top: pos.y, width: WIN.w, height: Math.min(WIN.h, window.innerHeight - 40) };

  return (
    // Container does NOT block the app behind (pointer-events-none); only the
    // window captures clicks, so the project stays navigable underneath.
    <div className="pointer-events-none fixed inset-0 z-[100]">
      <div
        style={style}
        className={`pointer-events-auto absolute flex flex-col overflow-hidden bg-white shadow-[0_40px_120px_-20px_rgba(15,23,42,0.6)] dark:bg-[#0B0D13] ${fullscreen ? "inset-0 rounded-none" : "rounded-2xl border border-black/10 dark:border-white/15"} ${animating ? "transition-all duration-300 ease-out" : ""}`}
      >
        <div
          onMouseDown={onHeaderDown}
          onDoubleClick={() => !isMobile && setMaximized(m => !m)}
          className={`flex shrink-0 items-center justify-between bg-[#0B0D13] px-4 py-2.5 text-white ${fullscreen ? "" : "cursor-move"}`}
        >
          <div className="flex items-center gap-2 text-[13px] tracking-tight">
            <span className="grid h-6 w-6 place-items-center rounded-md bg-white/15 text-[12px]">{editor ? "E" : "A"}</span>
            {editor ? "Редактор контента" : "Админ-панель"}
          </div>
          <div className="flex items-center gap-1">
            {!isMobile && (
              <button onClick={() => setMaximized(m => !m)} className="grid h-7 w-7 place-items-center rounded-md text-white/80 hover:bg-white/10" title={maximized ? "Свернуть" : "На весь экран"}>
                {maximized ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
              </button>
            )}
            <button onClick={onClose} className="grid h-7 w-7 place-items-center rounded-md text-white/80 hover:bg-red-500" title="Закрыть">
              <X size={15} />
            </button>
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">
          <AdminPanel fill editor={editor} mobile={isMobile} />
        </div>
      </div>
    </div>
  );
}

// Lives inside the store + shell context so it can read role + admin-open state.
export function AdminWindowMount() {
  const { role } = useStore();
  const { isMobile, adminOpen, adminSignal, closeAdmin } = React.useContext(ShellContext);
  if (role !== "admin" && role !== "editor") return null;
  return <AdminWindow open={adminOpen} isMobile={isMobile} editor={role === "editor"} signal={adminSignal} onClose={closeAdmin} />;
}
