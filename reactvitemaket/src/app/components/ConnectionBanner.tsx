import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { CloudOff, WifiOff, RefreshCw } from "lucide-react";
import { useConnectionStatus, pingHealth } from "../services/connection";

/**
 * ConnectionBanner — sticky-баннер в MobileShell над нижним таб-баром.
 * Показывается ТОЛЬКО когда состояние подключения не "online".
 * Тема — Apple-grade: rounded-2xl, blur, мягкая тень, в стиле сайта.
 */
export function ConnectionBanner() {
  const status = useConnectionStatus();
  const [retrying, setRetrying] = useState(false);

  const visible = status !== "online";

  const retry = async () => {
    if (retrying) return;
    setRetrying(true);
    const ok = await pingHealth();
    if (ok) {
      // Бэкенд живой. Браузер автоматически выстрелит "online", если был offline.
      // Если был server-error — перезагрузим страницу, чтобы fetch'и пошли заново.
      window.location.reload();
    } else {
      // Бэк всё ещё недоступен. Оставляем баннер как есть, но снимаем флаг retry.
      setRetrying(false);
    }
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ y: 16, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 16, opacity: 0 }}
          transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
          className="pointer-events-none fixed inset-x-0 z-40 px-3"
          style={{ bottom: "calc(5.5rem + env(safe-area-inset-bottom))" }}
        >
          <div className="pointer-events-auto mx-auto flex max-w-[480px] items-center gap-3 rounded-2xl border border-black/[0.06] bg-white/95 px-4 py-3 shadow-[0_18px_50px_-20px_rgba(15,23,42,0.35)] backdrop-blur-md dark:border-white/[0.08] dark:bg-[#0F1117]/95">
            <div
              className="grid h-9 w-9 shrink-0 place-items-center rounded-xl"
              style={{
                background:
                  status === "offline"
                    ? "linear-gradient(135deg,#FF3B30,#FF6B6B)"
                    : "linear-gradient(135deg,#F59E0B,#FBBF24)",
              }}
            >
              {status === "offline" ? (
                <WifiOff size={16} className="text-white" />
              ) : (
                <CloudOff size={16} className="text-white" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-[13px] font-medium tracking-tight text-black dark:text-white">
                {status === "offline" ? "Нет подключения к интернету" : "Сервис временно недоступен"}
              </div>
              <div className="truncate text-[12px] tracking-tight text-black/55 dark:text-white/55">
                {status === "offline"
                  ? "Проверьте Wi-Fi или мобильные данные"
                  : "Проверьте адрес сервера и доступ сети"}
              </div>
            </div>
            <button
              onClick={retry}
              disabled={retrying}
              className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-xl bg-[#0056FF] px-3 text-[12px] font-medium tracking-tight text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px] disabled:opacity-60"
            >
              <RefreshCw size={12} className={retrying ? "animate-spin" : ""} />
              {retrying ? "Проверяем" : "Повторить"}
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
