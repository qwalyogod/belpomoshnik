import React, { useEffect, useRef, useState } from "react";
import {
  Bold, Italic, Underline, Link2, Eye, EyeOff, Image as ImageIcon, Video,
  Plus, X, Check, ChevronLeft, Newspaper, FileText, AlertCircle, Calendar,
  Sparkles, MessageCircle, Languages,
} from "lucide-react";
import { useStore } from "../data/store";
import { apiClient } from "../services/api";
import { ShellContext } from "../App";

export type ContentKind = "news" | "scenario" | "problem";

export interface ContentDraft {
  kind: ContentKind;
  title: string;
  summary: string;
  bodyHtml: string;
  tags: string[];
  cover: string;
  video: string;
  gallery: string[];
  category: string;
  specialization: string;
  audience: string;
  author: string;
  date: string;
  guestVisible: boolean;
  source: string;
  sourceUrl: string;
  guestText: string;
  memberText: string;
  anonymous: boolean;
}

const KIND_META: Record<ContentKind, { icon: React.ReactNode; title: string; sub: string; titlePh: string; one: string; category: string }> = {
  news: {
    icon: <Newspaper size={15} />,
    title: "Новости и полезные материалы",
    sub: "Публикации редакции: адаптация, трудоустройство, правовые источники и работа с организациями.",
    titlePh: "Заголовок публикации",
    one: "публикацию",
    category: "Новости портала",
  },
  scenario: {
    icon: <FileText size={15} />,
    title: "Жизненные сценарии",
    sub: "Пошаговые маршруты с задачами, документами и адресами учреждений.",
    titlePh: "Название сценария",
    one: "жизненный сценарий",
    category: "Семья",
  },
  problem: {
    icon: <AlertCircle size={15} />,
    title: "Проблемы граждан",
    sub: "Типовые проблемы и способы их решения, сгруппированные по категориям.",
    titlePh: "Название проблемы",
    one: "проблему",
    category: "Социальная защита",
  },
};

const KIND_SWITCH: { id: ContentKind; label: string }[] = [
  { id: "news", label: "Новости" },
  { id: "scenario", label: "Жизненные сценарии" },
  { id: "problem", label: "Проблемы" },
];

function emptyDraft(kind: ContentKind, author: string): ContentDraft {
  return {
    kind, title: "", summary: "", bodyHtml: "", tags: [], cover: "", video: "", gallery: [],
    category: KIND_META[kind].category, specialization: "", audience: "all", author,
    date: new Date().toISOString().slice(0, 10), guestVisible: true, source: "", sourceUrl: "",
    guestText: "", memberText: "", anonymous: false,
  };
}

/* ---- small local controls (precise sizing, project styling) ---- */
function FieldLabel({ children }: { children: React.ReactNode }) {
  return <div className="mb-1.5 text-[11px] uppercase tracking-[0.12em] text-black/45 dark:text-white/45">{children}</div>;
}
const inputCls =
  "w-full rounded-xl border border-black/10 bg-white px-3.5 py-2.5 text-[14px] tracking-tight text-black outline-none transition-colors placeholder:text-black/35 focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white dark:placeholder:text-white/30";

export function ContentEditor({
  kind: kindProp, mode = "create", initial, authorName, mobile = false, propose = false, uploadFile, onClose, onSubmit,
}: {
  kind: ContentKind;
  mode?: "create" | "edit";
  initial?: Partial<ContentDraft>;
  authorName: string;
  mobile?: boolean;
  propose?: boolean;
  uploadFile?: (file: File) => Promise<string | null>;
  onClose: () => void;
  onSubmit: (draft: ContentDraft, action: "publish" | "draft" | "submit") => void;
}) {
  const [kind, setKind] = useState<ContentKind>(kindProp);
  const [tab, setTab] = useState<"content" | "media" | "publish">("content");
  const [preview, setPreview] = useState(false);
  const [d, setD] = useState<ContentDraft>(() => ({ ...emptyDraft(kindProp, authorName), ...initial, kind: kindProp }));
  const [bodyText, setBodyText] = useState("");
  const [tagInput, setTagInput] = useState("");
  const [linkOpen, setLinkOpen] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  // AI-помощник для контента.
  const { authSession, contentTags } = useStore();
  const { openAssistant } = React.useContext(ShellContext);
  const [aiOpen, setAiOpen] = useState(false);
  const [aiHint, setAiHint] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const askAi = async (mode: "generate" | "rewrite" | "expand" | "summarize" | "translate") => {
    if (!authSession?.access_token) {
      setAiError("Нужно войти как редактор или админ");
      return;
    }
    setAiBusy(true);
    setAiError(null);
    try {
      const resp = await apiClient.aiAssistContent<{ title: string; summary: string; body_html: string; source: string }>(
        authSession.access_token,
        {
          mode,
          kind,
          current_title: d.title,
          current_summary: d.summary,
          current_body_html: d.bodyHtml,
          hint: aiHint,
        },
      );
      if (mode === "summarize" && resp.summary) set("summary", resp.summary);
      if (mode === "generate" || mode === "rewrite" || mode === "expand") {
        if (resp.title) set("title", resp.title);
        if (resp.summary) set("summary", resp.summary);
        if (resp.body_html) {
          set("bodyHtml", resp.body_html);
          const el = editorRef.current;
          if (el) el.innerHTML = resp.body_html;
        }
      }
      setAiOpen(false);
      setAiHint("");
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Не удалось получить ответ от ИИ");
    } finally {
      setAiBusy(false);
    }
  };

  const editorRef = useRef<HTMLDivElement>(null);
  const savedRange = useRef<Range | null>(null);
  const coverInput = useRef<HTMLInputElement>(null);
  const videoInput = useRef<HTMLInputElement>(null);
  const galleryInput = useRef<HTMLInputElement>(null);

  const meta = KIND_META[kind];
  const set = <K extends keyof ContentDraft>(k: K, v: ContentDraft[K]) => setD((p) => ({ ...p, [k]: v }));

  // Seed the rich-text body once (edit mode / restored draft).
  useEffect(() => {
    const el = editorRef.current;
    if (el && initial?.bodyHtml) {
      el.innerHTML = initial.bodyHtml;
      setBodyText(el.innerText);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Switching kind only swaps the default category if untouched.
  useEffect(() => {
    setD((p) => ({ ...p, kind, category: KIND_SWITCH.some((k) => KIND_META[k.id].category === p.category) ? KIND_META[kind].category : p.category }));
  }, [kind]);

  const saveSel = () => {
    const s = window.getSelection();
    if (s && s.rangeCount && editorRef.current?.contains(s.anchorNode)) savedRange.current = s.getRangeAt(0).cloneRange();
  };
  const restoreSel = () => {
    const s = window.getSelection();
    if (s && savedRange.current) { s.removeAllRanges(); s.addRange(savedRange.current); }
  };
  const syncBody = () => {
    const el = editorRef.current;
    if (!el) return;
    set("bodyHtml", el.innerHTML);
    setBodyText(el.innerText);
  };
  const exec = (cmd: string, val?: string) => {
    editorRef.current?.focus();
    restoreSel();
    document.execCommand(cmd, false, val);
    syncBody();
    saveSel();
  };
  const applyLink = () => {
    const url = linkUrl.trim();
    if (url) exec("createLink", /^https?:\/\//.test(url) ? url : `https://${url}`);
    setLinkOpen(false);
    setLinkUrl("");
  };

  const activeTags = contentTags.filter(tag => tag.isActive);
  const filteredTags = activeTags
    .filter(tag => !d.tags.includes(tag.name))
    .filter(tag => {
      const q = tagInput.trim().toLowerCase();
      return !q || tag.name.toLowerCase().includes(q) || tag.description.toLowerCase().includes(q);
    })
    .slice(0, 12);
  const selectTag = (name: string) => {
    if (!d.tags.includes(name)) set("tags", [...d.tags, name]);
    setTagInput("");
  };
  const pickFiles = (ref: React.RefObject<HTMLInputElement>) => ref.current?.click();
  // Upload to the server when available (persists across reloads); otherwise a
  // local object URL keeps the editor usable offline.
  const resolveUrl = async (f: File) => (uploadFile ? (await uploadFile(f)) ?? URL.createObjectURL(f) : URL.createObjectURL(f));
  const onCover = async (e: React.ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (f) set("cover", await resolveUrl(f)); };
  const onVideo = async (e: React.ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (f) set("video", await resolveUrl(f)); };
  const onGallery = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    const urls = await Promise.all(files.map(resolveUrl));
    set("gallery", [...d.gallery, ...urls]);
  };

  const chars = bodyText.length;
  const words = bodyText.trim() ? bodyText.trim().split(/\s+/).length : 0;
  const mins = Math.max(1, Math.round(words / 200));
  const readiness = [
    { l: "Заголовок", ok: !!d.title.trim() },
    { l: "Текст", ok: bodyText.trim().length > 0 },
    { l: "Обложка", ok: !!d.cover.trim() },
  ];
  const canPublish = d.title.trim().length > 1 && bodyText.trim().length > 0;

  /* ---------- tab bodies ---------- */
  const contentTab = (
    <div className="space-y-5">
      <div className="relative">
        <input
          value={d.title}
          onChange={(e) => set("title", e.target.value)}
          placeholder={meta.titlePh}
          className="w-full border-0 border-b border-black/10 bg-transparent pb-2 pr-12 text-[26px] font-medium tracking-tight text-black outline-none placeholder:text-black/25 focus:border-[#0056FF] dark:border-white/15 dark:text-white dark:placeholder:text-white/20"
        />
        {/* P12: AI-помощник для контента (только для staff). */}
        <button
          type="button"
          onClick={() => setAiOpen((v) => !v)}
          disabled={aiBusy}
          title="ИИ-помощник для текста"
          className="absolute right-0 top-0 inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#0056FF] to-[#2277FF] text-white shadow-[0_8px_24px_-12px_rgba(0,86,255,0.6)] transition-transform hover:scale-105 active:scale-95 disabled:opacity-50"
        >
          <Sparkles size={15} />
        </button>
        {aiOpen && (
          <div className="absolute right-0 top-12 z-30 w-[300px] rounded-2xl border border-black/[0.06] bg-white p-3 shadow-2xl dark:border-white/[0.08] dark:bg-[#0F1117]">
            <div className="mb-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
              ИИ-помощник
            </div>
            <input
              value={aiHint}
              onChange={(e) => setAiHint(e.target.value)}
              placeholder="Подсказка для ИИ (необязательно)"
              className="mb-2 w-full rounded-lg border border-black/10 bg-white px-2.5 py-1.5 text-[12px] outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
            />
            <div className="grid grid-cols-2 gap-1.5">
              <button onClick={() => askAi("generate")} disabled={aiBusy} className="rounded-lg bg-[#0056FF] px-2.5 py-1.5 text-[12px] text-white hover:bg-[#0049DB] disabled:opacity-50">Создать</button>
              <button onClick={() => askAi("rewrite")} disabled={aiBusy} className="rounded-lg border border-black/10 bg-white px-2.5 py-1.5 text-[12px] text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:bg-white/[0.04] dark:text-white/70 disabled:opacity-50">Переписать</button>
              <button onClick={() => askAi("expand")} disabled={aiBusy} className="rounded-lg border border-black/10 bg-white px-2.5 py-1.5 text-[12px] text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:bg-white/[0.04] dark:text-white/70 disabled:opacity-50">Расширить</button>
              <button onClick={() => askAi("summarize")} disabled={aiBusy} className="rounded-lg border border-black/10 bg-white px-2.5 py-1.5 text-[12px] text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:bg-white/[0.04] dark:text-white/70 disabled:opacity-50">Сократить</button>
              {/* Перевод на белорусский */}
              <button
                onClick={() => askAi("translate")}
                disabled={aiBusy}
                className="col-span-2 inline-flex items-center justify-center gap-1.5 rounded-lg border border-black/10 bg-white px-2.5 py-1.5 text-[12px] text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:bg-white/[0.04] dark:text-white/70 disabled:opacity-50"
              >
                <Languages size={12} /> Перевести на белорусский
              </button>
              {/* Открыть полный ассистент (RAG-чат) */}
              <button
                onClick={() => { setAiOpen(false); openAssistant(); }}
                className="col-span-2 inline-flex items-center justify-center gap-1.5 rounded-lg border border-[#0056FF]/20 bg-[#E3E7FC] px-2.5 py-1.5 text-[12px] text-[#0056FF] hover:bg-[#0056FF]/20 dark:bg-[#0E1A3A] dark:text-[#7FA8FF]"
              >
                <MessageCircle size={12} /> Спросить ИИ-ассистента
              </button>
            </div>
            {aiBusy && (
              <div className="mt-2 text-center text-[11px] text-black/55 dark:text-white/55">Готовлю ответ…</div>
            )}
            {aiError && (
              <div className="mt-2 rounded-lg border border-red-200/60 bg-red-50 px-2 py-1.5 text-[11px] text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
                {aiError}
              </div>
            )}
            <div className="mt-2 text-[10px] leading-snug text-black/45 dark:text-white/45">
              Без GROQ_API_KEY работает локальный fallback с предупреждением «отредактируйте перед публикацией».
            </div>
          </div>
        )}
      </div>
      <textarea
        value={d.summary}
        onChange={(e) => set("summary", e.target.value)}
        rows={2}
        placeholder="Краткое описание — будет показано в карточке и в поиске"
        className={`${inputCls} resize-y`}
      />

      {/* rich-text toolbar */}
      <div className="rounded-2xl border border-black/10 dark:border-white/12">
        <div className="flex flex-wrap items-center gap-1 border-b border-black/[0.07] px-2 py-1.5 dark:border-white/[0.07]">
          {[
            { cmd: "bold", icon: <Bold size={15} />, t: "Жирный" },
            { cmd: "italic", icon: <Italic size={15} />, t: "Курсив" },
            { cmd: "underline", icon: <Underline size={15} />, t: "Подчёркнутый" },
          ].map((b) => (
            <button
              key={b.cmd}
              title={b.t}
              onMouseDown={(e) => { e.preventDefault(); exec(b.cmd); }}
              className="grid h-8 w-8 place-items-center rounded-lg text-black/65 transition-colors hover:bg-black/[0.05] dark:text-white/65 dark:hover:bg-white/[0.07]"
            >
              {b.icon}
            </button>
          ))}
          <span className="mx-1 h-5 w-px bg-black/10 dark:bg-white/15" />
          <button
            title="Гиперссылка"
            onMouseDown={(e) => { e.preventDefault(); saveSel(); setLinkOpen((v) => !v); }}
            className={`grid h-8 w-8 place-items-center rounded-lg transition-colors ${linkOpen ? "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/65 hover:bg-black/[0.05] dark:text-white/65 dark:hover:bg-white/[0.07]"}`}
          >
            <Link2 size={15} />
          </button>
          {linkOpen && (
            <div className="flex items-center gap-1.5 pl-1">
              <input
                autoFocus
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); applyLink(); } if (e.key === "Escape") setLinkOpen(false); }}
                placeholder="https://…"
                className="h-8 w-48 rounded-lg border border-black/10 bg-white px-2.5 text-[13px] outline-none focus:border-[#0056FF] dark:border-white/12 dark:bg-white/[0.04] dark:text-white"
              />
              <button onMouseDown={(e) => { e.preventDefault(); applyLink(); }} className="grid h-8 w-8 place-items-center rounded-lg bg-[#0056FF] text-white"><Check size={14} /></button>
            </div>
          )}
          <span className="ml-auto pr-1 text-[11px] tracking-tight text-black/35 dark:text-white/35">Выделите текст и нажмите формат</span>
        </div>
        <div className="relative">
          <div
            ref={editorRef}
            contentEditable
            suppressContentEditableWarning
            onInput={syncBody}
            onKeyUp={saveSel}
            onMouseUp={saveSel}
            className="min-h-[220px] w-full px-4 py-3 text-[14px] leading-relaxed tracking-tight text-black outline-none [&_a]:text-[#0056FF] [&_a]:underline dark:text-white"
          />
          {!bodyText && (
            <div className="pointer-events-none absolute left-4 top-3 text-[14px] tracking-tight text-black/30 dark:text-white/25">
              Текст публикации. Используйте абзацы для структуры — каждая пустая строка создаёт новый параграф.
            </div>
          )}
          <div className="flex justify-end gap-3 px-4 pb-2 text-[11px] tracking-tight text-black/40 dark:text-white/40">
            <span>{chars} символов</span><span>{words} слов</span><span>~{mins} мин</span>
          </div>
        </div>
      </div>

      {/* tags */}
      <div>
        <FieldLabel>Теги</FieldLabel>
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-1.5">
          {d.tags.map((t) => (
            <span key={t} className="inline-flex items-center gap-1 rounded-full bg-[#E3E7FC] px-2.5 py-1 text-[12px] tracking-tight text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
              {t}
              <button onClick={() => set("tags", d.tags.filter((x) => x !== t))} className="opacity-60 hover:opacity-100"><X size={12} /></button>
            </span>
          ))}
            {d.tags.length === 0 && (
              <span className="text-[12px] tracking-tight text-black/45 dark:text-white/45">Теги не выбраны</span>
            )}
          </div>
          <div className="rounded-2xl border border-black/10 bg-white p-2 dark:border-white/12 dark:bg-white/[0.04]">
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              placeholder="Найти тег из справочника…"
              className="h-8 w-full rounded-lg bg-transparent px-2 text-[13px] tracking-tight text-black outline-none placeholder:text-black/35 dark:text-white dark:placeholder:text-white/30"
            />
            <div className="mt-2 flex flex-wrap gap-1.5">
              {filteredTags.map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => selectTag(tag.name)}
                  className="inline-flex items-center gap-1 rounded-full border border-black/[0.08] px-2.5 py-1 text-[12px] tracking-tight text-black/65 transition-colors hover:border-[#0056FF]/40 hover:bg-[#E3E7FC] hover:text-[#0056FF] dark:border-white/10 dark:text-white/65 dark:hover:bg-[#0E1A3A] dark:hover:text-[#7FA8FF]"
                >
                  {tag.color && <span className="h-2 w-2 rounded-full" style={{ backgroundColor: tag.color }} />}
                  {tag.name}
                </button>
              ))}
              {filteredTags.length === 0 && (
                <span className="px-2 py-1 text-[12px] tracking-tight text-black/45 dark:text-white/45">
                  Подходящих тегов нет. Создайте тег в админке в разделе «Теги».
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const dropZone = (label: string, value: string, isVideo: boolean, ref: React.RefObject<HTMLInputElement>, onUrl: (v: string) => void) => (
    <div>
      <FieldLabel>{label}</FieldLabel>
      <button
        onClick={() => pickFiles(ref)}
        className="grid h-44 w-full place-items-center overflow-hidden rounded-2xl border-2 border-dashed border-black/12 bg-black/[0.015] text-center transition-colors hover:border-[#0056FF]/50 hover:bg-[#0056FF]/[0.03] dark:border-white/15 dark:bg-white/[0.02]"
      >
        {value ? (
          isVideo ? <video src={value} className="h-full w-full object-cover" /> : <img src={value} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="text-black/40 dark:text-white/35">
            <div className="mx-auto mb-2 grid h-10 w-10 place-items-center rounded-xl bg-black/[0.05] dark:bg-white/[0.06]">{isVideo ? <Video size={18} /> : <ImageIcon size={18} />}</div>
            <div className="text-[13px] tracking-tight text-black/55 dark:text-white/55">Нажмите для загрузки</div>
            <div className="text-[11px] tracking-tight">{isVideo ? "MP4, WebM, OGG" : "JPG, PNG, WebP, GIF"}</div>
          </div>
        )}
      </button>
      <input
        value={value.startsWith("blob:") ? "" : value}
        onChange={(e) => onUrl(e.target.value)}
        placeholder="Или вставьте URL: https://…"
        className={`${inputCls} mt-2`}
      />
    </div>
  );

  const mediaTab = (
    <div className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-2">
        {dropZone("Обложка", d.cover, false, coverInput, (v) => set("cover", v))}
        {dropZone("Видео", d.video, true, videoInput, (v) => set("video", v))}
      </div>
      <div className="rounded-2xl border border-black/10 p-4 dark:border-white/12">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[14px] tracking-tight text-black dark:text-white">Лента фото для слайдера</div>
            <div className="text-[12px] tracking-tight text-black/45 dark:text-white/45">{d.gallery.length} фото добавлено</div>
          </div>
          <button onClick={() => pickFiles(galleryInput)} className="inline-flex items-center gap-1.5 rounded-xl border border-black/10 px-3 py-2 text-[13px] tracking-tight text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70">
            <Plus size={14} /> Добавить фото
          </button>
        </div>
        {d.gallery.length ? (
          <div className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-5">
            {d.gallery.map((g, i) => (
              <div key={i} className="group relative aspect-square overflow-hidden rounded-xl">
                <img src={g} alt="" className="h-full w-full object-cover" />
                <button onClick={() => set("gallery", d.gallery.filter((_, j) => j !== i))} className="absolute right-1 top-1 grid h-6 w-6 place-items-center rounded-lg bg-black/55 text-white opacity-0 transition-opacity group-hover:opacity-100"><X size={13} /></button>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-3 grid h-20 place-items-center rounded-xl border border-dashed border-black/12 text-[12px] tracking-tight text-black/35 dark:border-white/12 dark:text-white/30">
            Загрузите фото кнопкой выше
          </div>
        )}
      </div>
    </div>
  );

  const publishTab = (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <div><FieldLabel>Категория</FieldLabel><input value={d.category} onChange={(e) => set("category", e.target.value)} className={inputCls} /></div>
        <div><FieldLabel>Специализация</FieldLabel><input value={d.specialization} onChange={(e) => set("specialization", e.target.value)} placeholder="или пусто" className={inputCls} /></div>
        <div>
          <FieldLabel>Аудитория</FieldLabel>
          <select value={d.audience} onChange={(e) => set("audience", e.target.value)} className={inputCls}>
            <option value="all">Все</option>
            <option value="citizens">Граждане</option>
            <option value="members">После входа</option>
            <option value="spec">По специализации</option>
          </select>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <div><FieldLabel>Автор</FieldLabel><input value={d.author} onChange={(e) => set("author", e.target.value)} className={inputCls} /></div>
        <div><FieldLabel>Дата публикации</FieldLabel>
          <div className="relative">
            <Calendar size={15} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-black/35 dark:text-white/35" />
            <input type="date" value={d.date} onChange={(e) => set("date", e.target.value)} className={inputCls} />
          </div>
        </div>
        <label className="flex cursor-pointer items-center gap-2.5 self-end rounded-xl border border-black/10 px-3.5 py-2.5 dark:border-white/12">
          <input type="checkbox" checked={d.guestVisible} onChange={(e) => set("guestVisible", e.target.checked)} className="h-4 w-4 accent-[#0056FF]" />
          <span className="text-[13px] tracking-tight text-black/70 dark:text-white/70">Видно гостям</span>
        </label>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div><FieldLabel>Источник</FieldLabel><input value={d.source} onChange={(e) => set("source", e.target.value)} placeholder="Официальный источник" className={inputCls} /></div>
        <div><FieldLabel>Ссылка на источник</FieldLabel><input value={d.sourceUrl} onChange={(e) => set("sourceUrl", e.target.value)} placeholder="https://pravo.by/" className={inputCls} /></div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div><FieldLabel>Текст для гостя</FieldLabel><textarea rows={3} value={d.guestText} onChange={(e) => set("guestText", e.target.value)} className={`${inputCls} resize-y`} /></div>
        <div><FieldLabel>Текст после входа</FieldLabel><textarea rows={3} value={d.memberText} onChange={(e) => set("memberText", e.target.value)} className={`${inputCls} resize-y`} /></div>
      </div>
    </div>
  );

  const previewBody = (
    <article className="mx-auto max-w-[680px]">
      {d.cover && <img src={d.cover} alt="" className="mb-5 aspect-[16/9] w-full rounded-2xl object-cover" />}
      <div className="text-[12px] uppercase tracking-[0.12em] text-[#0056FF]">{d.category || meta.category}</div>
      <h1 className="mt-2 text-[28px] font-medium leading-tight tracking-tight text-black dark:text-white">{d.title || meta.titlePh}</h1>
      <div className="mt-2 text-[13px] tracking-tight text-black/45 dark:text-white/45">Автор: {d.author || authorName} · {d.date}</div>
      {d.summary && <p className="mt-4 text-[15px] leading-relaxed tracking-tight text-black/70 dark:text-white/70">{d.summary}</p>}
      <div className="prose mt-4 text-[15px] leading-relaxed tracking-tight text-black/85 [&_a]:text-[#0056FF] [&_a]:underline dark:text-white/85" dangerouslySetInnerHTML={{ __html: d.bodyHtml || "<p style='opacity:.4'>Тело материала появится здесь…</p>" }} />
      {d.tags.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-1.5">
          {d.tags.map((t) => <span key={t} className="rounded-full bg-black/[0.05] px-2.5 py-1 text-[12px] tracking-tight text-black/55 dark:bg-white/[0.06] dark:text-white/55">#{t}</span>)}
        </div>
      )}
    </article>
  );

  return (
    <div className="flex h-full flex-col bg-[#F6F7FB] dark:bg-[#07080C]">
      {/* hidden file inputs */}
      <input ref={coverInput} type="file" accept="image/*" hidden onChange={onCover} />
      <input ref={videoInput} type="file" accept="video/*" hidden onChange={onVideo} />
      <input ref={galleryInput} type="file" accept="image/*" multiple hidden onChange={onGallery} />

      {/* top: title + kind switch */}
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-black/[0.06] bg-white/70 px-5 py-3.5 backdrop-blur dark:border-white/[0.06] dark:bg-[#0B0D13]/70 sm:px-7">
        <div className="flex items-start gap-2.5">
          <button onClick={onClose} className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg text-black/55 hover:bg-black/[0.05] dark:text-white/55 dark:hover:bg-white/[0.07]" title="Назад"><ChevronLeft size={18} /></button>
          <div>
            <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 19 }}>{propose ? `Предложить ${meta.one}` : meta.title}</div>
            <div className="mt-0.5 max-w-[60ch] text-[12px] leading-snug tracking-tight text-black/50 dark:text-white/50">{propose ? "Ваш материал уйдёт на модерацию редактору. Можно сохранить черновик и дописать позже." : meta.sub}</div>
          </div>
        </div>
        {mode === "create" && (
          <div className="flex items-center gap-1 rounded-xl bg-[#F6F7FB] p-1 dark:bg-white/[0.04]">
            {KIND_SWITCH.map((k) => (
              <button key={k.id} onClick={() => setKind(k.id)} className={`rounded-lg px-3 py-1.5 text-[12px] tracking-tight transition-colors ${kind === k.id ? "bg-white text-[#0056FF] shadow-sm dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "text-black/55 dark:text-white/55"}`}>{k.label}</button>
            ))}
          </div>
        )}
      </div>

      {/* editor card */}
      <div className="min-h-0 flex-1 overflow-y-auto p-4 [&::-webkit-scrollbar]:hidden sm:p-6">
        <div className="mx-auto max-w-[920px] overflow-hidden rounded-2xl border border-black/[0.06] bg-white dark:border-white/[0.06] dark:bg-[#0F1117]">
          <div className="flex items-center justify-between border-b border-black/[0.06] px-4 py-2.5 dark:border-white/[0.06]">
            <div className="flex items-center gap-1 rounded-xl bg-[#F6F7FB] p-1 dark:bg-white/[0.04]">
              {(propose ? ([["content", "Контент"], ["media", "Медиа"]] as const) : ([["content", "Контент"], ["media", "Медиа"], ["publish", "Публикация"]] as const)).map(([id, label]) => (
                <button key={id} onClick={() => setTab(id)} className={`rounded-lg px-3 py-1.5 text-[13px] tracking-tight transition-colors ${tab === id ? "bg-white text-black shadow-sm dark:bg-[#0E1A3A] dark:text-white" : "text-black/55 dark:text-white/55"}`}>{label}</button>
              ))}
            </div>
            <button onClick={() => setPreview((v) => !v)} className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-[13px] tracking-tight transition-colors ${preview ? "border-[#0056FF] bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]" : "border-black/10 text-black/65 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/65"}`}>
              {preview ? <EyeOff size={14} /> : <Eye size={14} />} {preview ? "Редактор" : "Предпросмотр"}
            </button>
          </div>
          <div className="p-4 sm:p-6">
            {preview ? previewBody : tab === "content" ? contentTab : tab === "media" ? mediaTab : publishTab}
          </div>
        </div>
      </div>

      {/* footer actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-black/[0.06] bg-white/80 px-5 py-3 backdrop-blur dark:border-white/[0.06] dark:bg-[#0B0D13]/80 sm:px-7">
        <div className="flex items-center gap-2.5">
          {propose ? (
            <>
              <button onClick={() => onSubmit({ ...d, kind }, "submit")} disabled={!canPublish} className="inline-flex h-10 items-center gap-2 rounded-xl bg-[#0056FF] px-4 text-[14px] tracking-tight text-white shadow-[0_8px_24px_-10px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px] disabled:opacity-40"><Check size={16} /> Отправить на модерацию</button>
              <button onClick={() => onSubmit({ ...d, kind }, "draft")} className="inline-flex h-10 items-center rounded-xl border border-black/10 px-4 text-[14px] tracking-tight text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70">В черновик</button>
            </>
          ) : mode === "edit" ? (
            <button onClick={() => onSubmit({ ...d, kind }, "publish")} disabled={!canPublish} className="inline-flex h-10 items-center gap-2 rounded-xl bg-[#0056FF] px-4 text-[14px] tracking-tight text-white shadow-[0_8px_24px_-10px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px] disabled:opacity-40"><Check size={16} /> Сохранить изменения</button>
          ) : (
            <>
              <button onClick={() => onSubmit({ ...d, kind }, "publish")} disabled={!canPublish} className="inline-flex h-10 items-center gap-2 rounded-xl bg-[#0056FF] px-4 text-[14px] tracking-tight text-white shadow-[0_8px_24px_-10px_rgba(0,86,255,0.6)] transition-all hover:bg-[#0049DB] active:translate-y-[1px] disabled:opacity-40"><Check size={16} /> Опубликовать</button>
              <button onClick={() => onSubmit({ ...d, kind }, "draft")} className="inline-flex h-10 items-center rounded-xl border border-black/10 px-4 text-[14px] tracking-tight text-black/70 hover:bg-black/[0.04] dark:border-white/12 dark:text-white/70">В черновик</button>
            </>
          )}
          <button onClick={onClose} className="inline-flex h-10 items-center rounded-xl px-3 text-[14px] tracking-tight text-black/50 hover:bg-black/[0.04] dark:text-white/50">Отмена</button>
        </div>
        {propose ? (
          <label className="flex cursor-pointer items-center gap-2.5 rounded-xl border border-black/10 px-3.5 py-2 dark:border-white/12">
            <input type="checkbox" checked={d.anonymous} onChange={(e) => set("anonymous", e.target.checked)} className="h-4 w-4 accent-[#0056FF]" />
            <span className="text-[13px] tracking-tight text-black/70 dark:text-white/70">Опубликовать анонимно</span>
          </label>
        ) : !mobile && (
          <div className="flex items-center gap-3 text-[12px] tracking-tight">
            {readiness.map((r) => (
              <span key={r.l} className={`inline-flex items-center gap-1.5 ${r.ok ? "text-emerald-600 dark:text-emerald-400" : "text-black/35 dark:text-white/35"}`}>
                <span className={`inline-block h-1.5 w-1.5 rounded-full ${r.ok ? "bg-emerald-500" : "bg-black/20 dark:bg-white/25"}`} />{r.l}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
