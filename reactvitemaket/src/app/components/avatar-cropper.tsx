// ============================================================================
// AvatarCropper — Telegram-стиль редактор аватара (кроп / зум / перетаскивание).
//
// Поток: пользователь выбрал файл → открывается этот модал → двигает и
// масштабирует фото внутри круглой области → «Применить» → наружу отдаётся
// уже обрезанный квадратный Blob (webp/jpeg), который грузится на бэк.
//
// Без внешних зависимостей: drag (pointer), zoom (слайдер + колесо + pinch),
// круглая маска, экспорт через <canvas>. Адаптив desktop / tablet / mobile
// обеспечивается измерением вьюпорта (ResizeObserver) — вся геометрия в px.
// ============================================================================
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion } from "motion/react";
import { X, ZoomIn, ZoomOut, Loader2, AlertCircle } from "lucide-react";

// --- Валидация входного файла (п.10–11 ТЗ задачи) ---------------------------
export const AVATAR_ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;
const AVATAR_ALLOWED_EXT = ["jpg", "jpeg", "png", "webp"];
export const AVATAR_MAX_INPUT_BYTES = 8 * 1024 * 1024; // 8 МБ на исходник

/** Проверяет тип и размер выбранного файла. Возвращает текст ошибки или null. */
export function validateAvatarFile(file: File): string | null {
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  const typeOk = (AVATAR_ALLOWED_TYPES as readonly string[]).includes(file.type) || AVATAR_ALLOWED_EXT.includes(ext);
  if (!typeOk) return "Поддерживаются только JPG, PNG и WEBP.";
  if (file.size > AVATAR_MAX_INPUT_BYTES) return `Файл больше ${AVATAR_MAX_INPUT_BYTES / (1024 * 1024)} МБ.`;
  if (file.size === 0) return "Файл пустой или повреждён.";
  return null;
}

// --- Константы геометрии ----------------------------------------------------
const OUTPUT_SIZE = 512; // сторона итогового квадрата (px)
const MAX_ZOOM = 4; // во сколько раз можно приблизить относительно «вписать»

type View = { scale: number; x: number; y: number };
type Nat = { w: number; h: number };

function distance(a: { x: number; y: number }, b: { x: number; y: number }) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

/** Жёстко удерживает картинку покрывающей круг: scale в [min,max], смещение в пределах. */
function clampView(view: View, V: number, nat: Nat): View {
  const minS = V / Math.min(nat.w, nat.h);
  const maxS = minS * MAX_ZOOM;
  const scale = Math.min(maxS, Math.max(minS, view.scale || minS));
  const maxX = Math.max(0, (nat.w * scale - V) / 2);
  const maxY = Math.max(0, (nat.h * scale - V) / 2);
  return {
    scale,
    x: Math.min(maxX, Math.max(-maxX, view.x)),
    y: Math.min(maxY, Math.max(-maxY, view.y)),
  };
}

function canvasToBlob(canvas: HTMLCanvasElement, type: string, quality: number): Promise<Blob | null> {
  return new Promise((resolve) => canvas.toBlob(resolve, type, quality));
}

export interface AvatarCropperProps {
  file: File;
  onCancel: () => void;
  /** Получает обрезанный Blob. Может бросить ошибку — покажем её в модале. */
  onApply: (blob: Blob) => Promise<void>;
}

export function AvatarCropper({ file, onCancel, onApply }: AvatarCropperProps) {
  const objectUrl = useMemo(() => URL.createObjectURL(file), [file]);
  const viewportRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  const [nat, setNat] = useState<Nat | null>(null);
  const [V, setV] = useState(0);
  const [view, setView] = useState<View>({ scale: 0, x: 0, y: 0 });
  const [loadError, setLoadError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Зеркала в ref — чтобы pointer/wheel-обработчики не ловили устаревшее состояние.
  const viewRef = useRef(view); useEffect(() => { viewRef.current = view; }, [view]);
  const VRef = useRef(V); useEffect(() => { VRef.current = V; }, [V]);
  const natRef = useRef(nat); useEffect(() => { natRef.current = nat; }, [nat]);

  // Освобождаем objectURL при размонтировании.
  useEffect(() => () => URL.revokeObjectURL(objectUrl), [objectUrl]);

  // Esc — отмена.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape" && !busy) onCancel(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel, busy]);

  // Размер вьюпорта (квадрат). ResizeObserver = адаптив под 3 устройства/поворот.
  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const w = Math.round(entries[0].contentRect.width);
      if (w > 0) setV(w);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Инициализация / переклампинг при изменении вьюпорта или картинки.
  useEffect(() => {
    if (!nat || V <= 0) return;
    setView((v) => (v.scale === 0 ? clampView({ scale: V / Math.min(nat.w, nat.h), x: 0, y: 0 }, V, nat) : clampView(v, V, nat)));
  }, [nat, V]);

  const onImgLoad = () => {
    const el = imgRef.current;
    if (!el) return;
    if (!el.naturalWidth || !el.naturalHeight) { setLoadError(true); return; }
    setNat({ w: el.naturalWidth, h: el.naturalHeight });
  };

  // --- Пан и зум ------------------------------------------------------------
  const applyPan = useCallback((dx: number, dy: number) => {
    const v = VRef.current, n = natRef.current;
    if (!n || v <= 0) return;
    setView((cur) => clampView({ ...cur, x: cur.x + dx, y: cur.y + dy }, v, n));
  }, []);

  const applyZoom = useCallback((nextScale: number) => {
    const v = VRef.current, n = natRef.current;
    if (!n || v <= 0) return;
    setView((cur) => {
      const ratio = cur.scale ? nextScale / cur.scale : 1;
      return clampView({ scale: nextScale, x: cur.x * ratio, y: cur.y * ratio }, v, n);
    });
  }, []);

  // Pointer-события: 1 палец = drag, 2 пальца = pinch-zoom.
  const ptrs = useRef(new Map<number, { x: number; y: number }>());
  const pinch = useRef<{ dist: number; scale: number } | null>(null);
  const last = useRef<{ x: number; y: number } | null>(null);

  const onPointerDown = (e: React.PointerEvent) => {
    if (busy || loadError) return;
    (e.currentTarget as Element).setPointerCapture(e.pointerId);
    ptrs.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (ptrs.current.size === 2) {
      const [a, b] = [...ptrs.current.values()];
      pinch.current = { dist: distance(a, b), scale: viewRef.current.scale };
      last.current = null;
    } else {
      last.current = { x: e.clientX, y: e.clientY };
    }
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!ptrs.current.has(e.pointerId)) return;
    ptrs.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (ptrs.current.size >= 2 && pinch.current) {
      const [a, b] = [...ptrs.current.values()];
      const d = distance(a, b);
      if (pinch.current.dist > 0) applyZoom(pinch.current.scale * (d / pinch.current.dist));
    } else if (last.current) {
      applyPan(e.clientX - last.current.x, e.clientY - last.current.y);
      last.current = { x: e.clientX, y: e.clientY };
    }
  };

  const endPointer = (e: React.PointerEvent) => {
    try { (e.currentTarget as Element).releasePointerCapture(e.pointerId); } catch { /* noop */ }
    ptrs.current.delete(e.pointerId);
    if (ptrs.current.size < 2) pinch.current = null;
    const rest = [...ptrs.current.values()];
    last.current = rest.length === 1 ? { x: rest[0].x, y: rest[0].y } : null;
  };

  // Колесо мыши — зум (десктоп). Нативный listener c passive:false, чтобы
  // отменить прокрутку страницы под модалом.
  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.08 : 1 / 1.08;
      applyZoom(viewRef.current.scale * factor);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [applyZoom]);

  // --- Экспорт обрезанного изображения --------------------------------------
  const handleApply = async () => {
    const img = imgRef.current;
    if (!img || !nat || V <= 0) return;
    setError(null);
    setBusy(true);
    try {
      const { scale, x, y } = viewRef.current;
      const left = (V - nat.w * scale) / 2 + x;
      const top = (V - nat.h * scale) / 2 + y;
      // Видимое окно V×V в координатах исходника:
      const sSize = V / scale;
      const sx = Math.max(0, Math.min(nat.w - sSize, -left / scale));
      const sy = Math.max(0, Math.min(nat.h - sSize, -top / scale));

      const canvas = document.createElement("canvas");
      canvas.width = OUTPUT_SIZE;
      canvas.height = OUTPUT_SIZE;
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Canvas недоступен в этом браузере.");
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(img, sx, sy, sSize, sSize, 0, 0, OUTPUT_SIZE, OUTPUT_SIZE);

      let blob = await canvasToBlob(canvas, "image/webp", 0.9);
      if (!blob) blob = await canvasToBlob(canvas, "image/jpeg", 0.9);
      if (!blob) throw new Error("Не удалось обработать изображение.");

      await onApply(blob);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить аватар.");
      setBusy(false);
    }
  };

  // --- Производные значения для рендера --------------------------------------
  const minScale = nat && V > 0 ? V / Math.min(nat.w, nat.h) : 0;
  const maxScale = minScale * MAX_ZOOM;
  const sliderValue = minScale > 0 && maxScale > minScale ? (view.scale - minScale) / (maxScale - minScale) : 0;
  const dispW = nat ? nat.w * view.scale : 0;
  const dispH = nat ? nat.h * view.scale : 0;
  const left = nat ? (V - dispW) / 2 + view.x : 0;
  const top = nat ? (V - dispH) / 2 + view.y : 0;
  const ready = !!nat && V > 0 && view.scale > 0 && !loadError;

  return (
    <div
      className="fixed inset-0 z-[120] grid place-items-center bg-black/50 p-4 backdrop-blur-sm"
      onMouseDown={(e) => { if (e.target === e.currentTarget && !busy) onCancel(); }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 320, damping: 32 }}
        className="flex w-full max-w-[420px] flex-col overflow-hidden rounded-3xl bg-white shadow-2xl dark:bg-[#0F1117]"
      >
        {/* Заголовок */}
        <div className="flex items-center justify-between border-b border-black/[0.06] px-5 py-4 dark:border-white/[0.06]">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 17 }}>Фото профиля</div>
          <button
            onClick={() => !busy && onCancel()}
            aria-label="Закрыть"
            className="grid h-8 w-8 place-items-center rounded-lg text-black/40 hover:bg-black/[0.04] dark:text-white/40 dark:hover:bg-white/[0.06]"
          >
            <X size={16} />
          </button>
        </div>

        {/* Тело */}
        <div className="space-y-4 p-5">
          {loadError ? (
            <div className="flex flex-col items-center gap-2 py-10 text-center">
              <AlertCircle size={28} className="text-red-500" />
              <div className="text-[14px] text-black/70 dark:text-white/70">Не удалось открыть изображение.<br />Попробуйте другой файл.</div>
            </div>
          ) : (
            <>
              {/* Область кропа: квадрат на всю ширину карточки → адаптив сам собой. */}
              <div className="mx-auto w-full max-w-[320px]">
                <div
                  ref={viewportRef}
                  onPointerDown={onPointerDown}
                  onPointerMove={onPointerMove}
                  onPointerUp={endPointer}
                  onPointerCancel={endPointer}
                  className="relative aspect-square w-full touch-none select-none overflow-hidden rounded-2xl bg-black/90"
                  style={{ cursor: ready ? "grab" : "default" }}
                >
                  {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
                  <img
                    ref={imgRef}
                    src={objectUrl}
                    alt="Предпросмотр фото"
                    draggable={false}
                    onLoad={onImgLoad}
                    onError={() => setLoadError(true)}
                    style={ready ? { position: "absolute", left, top, width: dispW, height: dispH, maxWidth: "none" } : { opacity: 0 }}
                  />
                  {/* Круглая маска: затемнение вне круга + белое кольцо. */}
                  {ready && (
                    <>
                      <div className="pointer-events-none absolute inset-0 rounded-full shadow-[0_0_0_9999px_rgba(0,0,0,0.45)]" />
                      <div className="pointer-events-none absolute inset-0 rounded-full ring-2 ring-white/80" />
                    </>
                  )}
                  {!ready && (
                    <div className="absolute inset-0 grid place-items-center">
                      <Loader2 size={22} className="animate-spin text-white/70" />
                    </div>
                  )}
                </div>
              </div>

              {/* Зум: −  слайдер  + */}
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  aria-label="Отдалить"
                  disabled={!ready}
                  onClick={() => applyZoom(view.scale / 1.15)}
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-black/[0.04] text-black/60 transition hover:bg-black/[0.08] disabled:opacity-40 dark:bg-white/[0.06] dark:text-white/60"
                >
                  <ZoomOut size={16} />
                </button>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.001}
                  value={sliderValue}
                  disabled={!ready}
                  onChange={(e) => applyZoom(minScale + Number(e.target.value) * (maxScale - minScale))}
                  aria-label="Масштаб"
                  className="h-1.5 flex-1 cursor-pointer appearance-none rounded-full bg-black/10 accent-[#0056FF] disabled:opacity-40 dark:bg-white/15"
                />
                <button
                  type="button"
                  aria-label="Приблизить"
                  disabled={!ready}
                  onClick={() => applyZoom(view.scale * 1.15)}
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-black/[0.04] text-black/60 transition hover:bg-black/[0.08] disabled:opacity-40 dark:bg-white/[0.06] dark:text-white/60"
                >
                  <ZoomIn size={16} />
                </button>
              </div>

              <p className="text-center text-[12px] text-black/45 dark:text-white/45">
                Перетащите фото и настройте масштаб
              </p>
            </>
          )}

          {error && (
            <div className="flex items-center gap-2 rounded-xl bg-red-50 px-3 py-2 text-[13px] text-red-600 dark:bg-red-500/10 dark:text-red-300">
              <AlertCircle size={15} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Кнопки */}
        <div className="flex gap-2 border-t border-black/[0.06] p-4 dark:border-white/[0.06]">
          <button
            onClick={() => !busy && onCancel()}
            disabled={busy}
            className="h-12 flex-1 rounded-2xl bg-black/[0.04] tracking-tight text-black/70 transition hover:bg-black/[0.07] disabled:opacity-50 dark:bg-white/[0.06] dark:text-white/70 dark:hover:bg-white/[0.1]"
          >
            Отмена
          </button>
          <button
            onClick={handleApply}
            disabled={!ready || busy}
            className="inline-flex h-12 flex-1 items-center justify-center gap-2 rounded-2xl bg-[#0056FF] tracking-tight text-white shadow-[0_10px_30px_-12px_rgba(0,86,255,0.55)] transition hover:bg-[#0049DB] active:translate-y-[1px] disabled:opacity-50"
          >
            {busy ? <><Loader2 size={16} className="animate-spin" /> Сохранение…</> : "Сохранить"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

export default AvatarCropper;
