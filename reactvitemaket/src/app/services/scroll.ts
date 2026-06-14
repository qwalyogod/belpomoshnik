/**
 * Сброс прокрутки контента наверх.
 *
 * В приложении две модели скролла:
 *  - mobile (MobileShell): страница скроллится нативно окном; bottom-nav
 *    защищён fade-подложкой и дополнительным нижним padding;
 *  - desktop (DesktopShell / DesktopHeaderShell): контент живёт в постоянном
 *    `flex-1 overflow-y-auto`, помеченном [data-scroll-root].
 *
 * behavior:
 *  - "auto"   — мгновенно: при переходе на новый маршрут (страница обязана
 *    открыться сверху, а не на позиции скролла предыдущей);
 *  - "smooth" — плавно: при повторном клике по уже активному пункту меню.
 */
export function scrollContentToTop(behavior: ScrollBehavior = "auto"): void {
  if (typeof window === "undefined") return;
  try {
    window.scrollTo({ top: 0, left: 0, behavior });
  } catch {
    window.scrollTo(0, 0);
  }
  document.querySelectorAll<HTMLElement>("[data-scroll-root]").forEach((el) => {
    try {
      el.scrollTo({ top: 0, behavior });
    } catch {
      el.scrollTop = 0;
    }
  });
}
