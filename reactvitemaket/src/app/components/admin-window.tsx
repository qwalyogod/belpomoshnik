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
    startDrag(e.clientX, e.clientY);
  };

  // v0.8: long-press на фоне (не на header) 600мс -> включается drag.
  // Помогает на touch и тем, кто не нашёл узкий header-bar. Чтобы не
  // путать со скроллом/обычным тапом, жёсткий 600мс + drag начинается не
  // с момента mousedown, а с момента отпускания после удержания.
  const holdRef = useRef<{ timer: number; sx: number; sy: number; ox: number; oy: number; fired: boolean } | null>(null);
  const HOLD_MS = 600;

  const startDrag = (sx: number, sy: number) => {
    drag.current = { sx, sy, ox: pos.x, oy: pos.y };
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

  const onBgPointerDown = (e: React.PointerEvent) => {
    // Не запускаем hold, если нажали на интерактивный элемент (кнопка, input, link)
    const target = e.target as HTMLElement;
    if (target.closest("button, a, input, textarea, select, [role='button'], [data-no-drag]")) return;
    if (maximized || isMobile) return;
    if (drag.current) return;

    holdRef.current = {
      timer: window.setTimeout(() => {
        const h = holdRef.current;
        if (!h || h.fired) return;
        h.fired = true;
        // Стартуем drag из текущей позиции курсора/тача
        startDrag(e.clientX, e.clientY);
      }, HOLD_MS),
      sx: e.clientX,
      sy: e.clientY,
      ox: pos.x,
      oy: pos.y,
      fired: false,
    };
  };
  const onBgPointerMove = (e: React.PointerEvent) => {
    const h = holdRef.current;
    if (!h || h.fired) return;
    // Отменяем hold, если палец/мышь сдвинулся > 8px — это скролл/тап, не удержание
    if (Math.abs(e.clientX - h.sx) > 8 || Math.abs(e.clientY - h.sy) > 8) {
      window.clearTimeout(h.timer);
      holdRef.current = null;
    }
  };
  const onBgPointerUp = () => {
    const h = holdRef.current;
    if (!h) return;
    window.clearTimeout(h.timer);
    holdRef.current = null;
  };

  // Очистка таймера при unmount/закрытии
  useEffect(() => {
    return () => {
      if (holdRef.current) window.clearTimeout(holdRef.current.timer);
    };
  }, []);

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
        onPointerDown={onBgPointerDown}
        onPointerMove={onBgPointerMove}
        onPointerUp={onBgPointerUp}
        onPointerCancel={onBgPointerUp}
      >
        <div
          onMouseDown={onHeaderDown}
          onDoubleClick={() => !isMobile && setMaximized(m => !m)}
          // v0.8: safe-area-top inset, чтобы крестик и кнопки не уходили
          // за iOS-шейф-зону на устройствах вроде iPhone с Dynamic Island.
          style={{ paddingTop: "env(safe-area-inset-top)", minHeight: "calc(2.5rem + env(safe-area-inset-top))" }}
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
  // Поддерживаем оба варианта role: "platform_admin"/"content_editor" (новые) и
  // "admin"/"editor" (legacy, из старых quickAccounts в LS).
  const isStaff = role === "platform_admin" || role === "content_editor" || role === "admin" || role === "editor";
  if (!isStaff) return null;
  const editor = role === "content_editor" || role === "editor";
  return <AdminWindow open={adminOpen} isMobile={isMobile} editor={editor} signal={adminSignal} onClose={closeAdmin} />;
}
