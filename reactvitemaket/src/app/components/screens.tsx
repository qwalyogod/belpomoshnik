import { motion } from "motion/react";
import {
  Search, FileText, Home, Bell, User, ArrowRight, ChevronRight, Check, Lock, Shield,
  AlertCircle, CalendarClock, MapPin, Briefcase, Heart, Baby, Wallet, Hammer, Plus,
  ScanLine, Eye, EyeOff, Sparkles, ArrowUpRight, Building2, Clock, Bookmark,
} from "lucide-react";
import { Card, Pill, PrimaryButton, GhostButton, StatusBar, Logo } from "./belp-ui";

/* ---------------- SPLASH ---------------- */
export function SplashScreen() {
  return (
    <div className="relative flex h-full flex-col items-center justify-center overflow-hidden"
      style={{ background: "radial-gradient(120% 80% at 50% 0%, #2277FF 0%, #0056FF 45%, #001A66 100%)" }}>
      <div className="pointer-events-none absolute -top-24 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-white/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-20 right-0 h-72 w-72 rounded-full bg-[#9BB8FF]/30 blur-3xl" />
      <StatusBar />
      <div className="relative flex flex-1 flex-col items-center justify-center gap-6 text-white">
        <motion.div
          initial={{ scale: 0.6, opacity: 0, rotate: -10 }}
          animate={{ scale: 1, opacity: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 160, damping: 16 }}
          className="grid h-24 w-24 place-items-center rounded-[28px] bg-white shadow-[0_20px_60px_-10px_rgba(0,0,0,0.4)]"
        >
          <span className="bg-gradient-to-br from-[#0056FF] to-[#2277FF] bg-clip-text text-[44px] tracking-tight text-transparent">Б</span>
        </motion.div>
        <div className="text-center">
          <div className="tracking-tight text-[28px]">Белпомощник</div>
          <div className="mt-1.5 tracking-tight text-white/70">Личный гражданский ассистент</div>
        </div>
      </div>
      <div className="relative pb-10 text-[12px] tracking-tight text-white/50">Версия 1.0 · Беларусь</div>
    </div>
  );
}

/* ---------------- ONBOARDING ---------------- */
export function OnboardingScreen() {
  return (
    <div className="flex h-full flex-col bg-[#F6F7FB] dark:bg-[#07080C]">
      <StatusBar />
      <div className="flex flex-1 flex-col px-7 pt-6">
        <div className="ml-auto text-[13px] tracking-tight text-black/50 dark:text-white/50">Пропустить</div>
        <div className="mt-10 flex h-[300px] items-center justify-center">
          <div className="relative">
            <motion.div
              animate={{ y: [0, -6, 0] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="relative h-[240px] w-[240px] rounded-[40px] p-5 text-white shadow-[0_30px_80px_-20px_rgba(0,86,255,0.5)]"
              style={{ background: "linear-gradient(135deg,#0056FF,#2277FF 60%,#9BB8FF)" }}
            >
              <div className="text-[12px] tracking-tight text-white/80">Шаг 2 из 5</div>
              <div className="mt-2 tracking-tight text-[18px] leading-tight">Подать заявление в МФЦ</div>
              <div className="mt-5 space-y-2">
                {["Паспорт","Заявление","Справка о составе семьи"].map((d) => (
                  <div key={d} className="flex items-center gap-2 rounded-xl bg-white/15 px-3 py-2 text-[12px] tracking-tight backdrop-blur">
                    <FileText size={14} /> {d}
                  </div>
                ))}
              </div>
              <div className="absolute -right-3 -bottom-3 grid h-12 w-12 place-items-center rounded-2xl bg-white text-[#0056FF] shadow-lg">
                <Check size={22} strokeWidth={2.4} />
              </div>
            </motion.div>
          </div>
        </div>
        <div className="mt-auto pb-8">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 26, lineHeight: 1.15 }}>
            Разберём сложную<br />ситуацию по шагам
          </div>
          <p className="mt-3 max-w-[300px] tracking-tight text-black/60 dark:text-white/60">
            Чёткий план действий, документы и сроки — собраны в одном спокойном месте.
          </p>
          <div className="mt-6 flex items-center justify-between">
            <div className="flex gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-black/15 dark:bg-white/15" />
              <span className="h-1.5 w-6 rounded-full bg-[#0056FF]" />
              <span className="h-1.5 w-1.5 rounded-full bg-black/15 dark:bg-white/15" />
            </div>
            <PrimaryButton icon={<ArrowRight size={18} />}>Дальше</PrimaryButton>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------- HOME DASHBOARD ---------------- */
export function HomeScreen() {
  const cats = [
    { i: <FileText size={20} />, n: "Документы" },
    { i: <Home size={20} />, n: "ЖКХ" },
    { i: <Wallet size={20} />, n: "Налоги" },
    { i: <Heart size={20} />, n: "Семья" },
    { i: <Briefcase size={20} />, n: "Работа" },
    { i: <Hammer size={20} />, n: "Здоровье" },
  ];
  return (
    <div className="relative flex h-full flex-col bg-[#F6F7FB] dark:bg-[#07080C]">
      <StatusBar />
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto px-5 pb-32 pt-3 [&::-webkit-scrollbar]:hidden">
          <div className="flex items-center justify-between px-1">
            <Logo size={26} />
            <div className="relative grid h-10 w-10 place-items-center rounded-full bg-white shadow-sm dark:bg-white/[0.06]">
              <Bell size={17} className="text-black dark:text-white" />
              <span className="absolute -right-0.5 -top-0.5 grid h-4 w-4 place-items-center rounded-full bg-[#0056FF] text-[10px] text-white">3</span>
            </div>
          </div>

          <div className="mt-5 px-1">
            <div className="tracking-tight text-black/50 dark:text-white/50">Добрый день, Алексей</div>
            <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 26, lineHeight: 1.15 }}>
              Какая у вас<br />ситуация?
            </div>
          </div>

          <div className="mt-5">
            <div className="flex items-center gap-3 rounded-2xl border border-black/[0.06] bg-white px-4 py-3.5 shadow-[0_8px_24px_-16px_rgba(15,23,42,0.2)] dark:border-white/[0.06] dark:bg-[#0F1117]">
              <Search size={18} className="text-black/40 dark:text-white/40" />
              <input
                placeholder="Например: потерял паспорт"
                className="w-full bg-transparent tracking-tight outline-none placeholder:text-black/35 dark:text-white dark:placeholder:text-white/35"
              />
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <Sparkles size={14} />
              </span>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-3 gap-2.5">
            {cats.map((c) => (
              <button key={c.n} className="flex flex-col items-start gap-2 rounded-2xl border border-black/[0.06] bg-white px-3 py-3 text-left transition-all active:scale-[0.98] dark:border-white/[0.06] dark:bg-[#0F1117]">
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">{c.i}</span>
                <span className="tracking-tight text-black dark:text-white">{c.n}</span>
              </button>
            ))}
          </div>

          {/* Active situation */}
          <div className="mt-6 flex items-center justify-between px-1">
            <div className="tracking-tight text-black dark:text-white">Мои ситуации</div>
            <span className="text-[13px] tracking-tight text-[#0056FF]">Все</span>
          </div>
          <div className="mt-3 overflow-hidden rounded-3xl p-5 text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
            style={{ background: "linear-gradient(135deg,#001A66 0%,#0056FF 60%,#2277FF 100%)" }}>
            <div className="flex items-center justify-between">
              <Pill tone="ghost">
                <span className="text-white/90">В процессе</span>
              </Pill>
              <span className="text-[12px] tracking-tight text-white/70">Шаг 3 из 5</span>
            </div>
            <div className="mt-3 tracking-tight" style={{ fontSize: 19, lineHeight: 1.2 }}>
              Восстановление паспорта
            </div>
            <div className="mt-1 text-[13px] tracking-tight text-white/75">Следующее: подать заявление в РОВД</div>
            <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-white/20">
              <motion.div initial={{ width: 0 }} animate={{ width: "60%" }} transition={{ duration: 1.2, ease: "easeOut" }} className="h-full rounded-full bg-white" />
            </div>
            <div className="mt-4 flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-[12px] tracking-tight text-white/80">
                <CalendarClock size={13} /> Срок: 14 дней
              </div>
              <span className="inline-flex items-center gap-1 text-[13px] tracking-tight">Продолжить <ArrowRight size={14} /></span>
            </div>
          </div>

          {/* Deadlines + Doc */}
          <div className="mt-3 grid grid-cols-2 gap-3">
            <Card className="p-4">
              <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                <AlertCircle size={15} />
                <span className="text-[12px] tracking-tight">Срок истекает</span>
              </div>
              <div className="mt-1.5 tracking-tight text-black dark:text-white">через 14 дней</div>
              <div className="mt-0.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">Оплата налога на недвижимость</div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                <Shield size={15} />
                <span className="text-[12px] tracking-tight">Документ</span>
              </div>
              <div className="mt-1.5 tracking-tight text-black dark:text-white">Паспорт</div>
              <div className="mt-0.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">Действителен до 2031</div>
            </Card>
          </div>

          {/* Legal updates */}
          <div className="mt-6 flex items-center justify-between px-1">
            <div className="tracking-tight text-black dark:text-white">Важное для вас</div>
            <span className="text-[13px] tracking-tight text-[#0056FF]">Все</span>
          </div>
          <Card className="mt-3 p-4">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <FileText size={16} />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Pill tone="lavender">Налоги</Pill>
                  <span className="text-[11px] tracking-tight text-black/45 dark:text-white/45">с 1 июля 2026</span>
                </div>
                <div className="mt-2 tracking-tight text-black dark:text-white">Новый порядок имущественного вычета для семей с детьми</div>
                <div className="mt-1 text-[12px] tracking-tight text-black/55 dark:text-white/55">Касается вас как собственника жилья</div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Floating bottom nav */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 px-5 pb-5">
        <div className="pointer-events-auto flex items-center justify-around rounded-[28px] border border-black/[0.06] bg-white/95 px-2 py-2.5 shadow-[0_20px_60px_-20px_rgba(15,23,42,0.35)] backdrop-blur-xl dark:border-white/[0.08] dark:bg-[#0F1117]/95">
          {[
            { i: <Home size={20} />, n: "Главная", active: true },
            { i: <FileText size={20} />, n: "Ситуации" },
            { i: <Shield size={20} />, n: "Документы" },
            { i: <User size={20} />, n: "Профиль" },
          ].map((t) => (
            <button key={t.n} className="relative flex flex-col items-center gap-0.5 px-3 py-1.5">
              {t.active && (
                <motion.span layoutId="nav-pill" className="absolute inset-0 rounded-2xl bg-[#E3E7FC] dark:bg-[#0E1A3A]" />
              )}
              <span className={`relative ${t.active ? "text-[#0056FF] dark:text-[#7FA8FF]" : "text-black/55 dark:text-white/55"}`}>{t.i}</span>
              <span className={`relative text-[10px] tracking-tight ${t.active ? "text-[#0056FF] dark:text-[#7FA8FF]" : "text-black/55 dark:text-white/55"}`}>{t.n}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------------- SITUATION TIMELINE ---------------- */
export function SituationScreen() {
  const steps = [
    { n: "Получить справку об утере", state: "done", when: "Готово", where: "РОВД Первомайского района" },
    { n: "Сделать фото 4×5 на паспорт", state: "done", when: "Готово", where: "Фотосалон или дома" },
    { n: "Подать заявление в РОВД", state: "now", when: "Сегодня", where: "РОВД по месту жительства" },
    { n: "Оплатить госпошлину", state: "lock", when: "После шага 3", where: "Беларусбанк, ЕРИП" },
    { n: "Получить новый паспорт", state: "lock", when: "Через 14 дней", where: "РОВД Первомайского района" },
  ];
  return (
    <div className="flex h-full flex-col bg-[#F6F7FB] dark:bg-[#07080C]">
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 pb-10 pt-3 [&::-webkit-scrollbar]:hidden">
        <div className="flex items-center justify-between">
          <button className="grid h-9 w-9 place-items-center rounded-full bg-white text-black shadow-sm dark:bg-white/[0.06] dark:text-white">
            <ChevronRight size={16} className="rotate-180" />
          </button>
          <Pill tone="lavender">3 из 5 шагов</Pill>
          <button className="grid h-9 w-9 place-items-center rounded-full bg-white text-black shadow-sm dark:bg-white/[0.06] dark:text-white">
            <Bookmark size={15} />
          </button>
        </div>

        <div className="mt-5">
          <div className="text-[12px] tracking-tight text-[#0056FF]">Документы · в процессе</div>
          <div className="mt-1 tracking-tight text-black dark:text-white" style={{ fontSize: 26, lineHeight: 1.15 }}>
            Восстановление<br />паспорта
          </div>
          <p className="mt-2 max-w-[300px] text-[14px] tracking-tight text-black/60 dark:text-white/60">
            Пошаговый план для жителей г. Минск. Учитывает все требования МВД.
          </p>
        </div>

        <Card className="mt-5 p-4">
          <div className="flex items-center justify-between text-[12px] tracking-tight text-black/60 dark:text-white/60">
            <span>Прогресс</span><span>60%</span>
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.06]">
            <motion.div initial={{ width: 0 }} animate={{ width: "60%" }} transition={{ duration: 1, ease: "easeOut" }} className="h-full rounded-full"
              style={{ background: "linear-gradient(90deg,#0056FF,#2277FF)" }} />
          </div>
        </Card>

        <div className="mt-6 px-1 tracking-tight text-black dark:text-white">Пошаговый план</div>

        <div className="relative mt-3">
          <div className="absolute left-[15px] top-2 bottom-2 w-px bg-black/10 dark:bg-white/10" />
          <div className="space-y-3">
            {steps.map((s, i) => (
              <div key={i} className="relative pl-10">
                <div className="absolute left-0 top-3 grid h-8 w-8 place-items-center rounded-full"
                  style={{
                    background:
                      s.state === "done" ? "linear-gradient(135deg,#0056FF,#2277FF)" :
                      s.state === "now" ? "white" : "transparent",
                    boxShadow: s.state === "now" ? "0 0 0 2px #0056FF, 0 0 0 6px #E3E7FC" : "none",
                  }}
                >
                  {s.state === "done" && <Check size={16} className="text-white" strokeWidth={2.6} />}
                  {s.state === "now" && <span className="h-2 w-2 rounded-full bg-[#0056FF]" />}
                  {s.state === "lock" && <Lock size={14} className="text-black/35 dark:text-white/30" />}
                </div>
                <Card className={`p-4 ${s.state === "lock" ? "opacity-60" : ""}`}>
                  <div className="flex items-center gap-2">
                    {s.state === "now" && <Pill tone="royal">Сейчас</Pill>}
                    {s.state === "done" && <Pill tone="ok">Выполнено</Pill>}
                    <span className="text-[11px] tracking-tight text-black/45 dark:text-white/45">{s.when}</span>
                  </div>
                  <div className="mt-1.5 tracking-tight text-black dark:text-white">{s.n}</div>
                  <div className="mt-1 flex items-center gap-1.5 text-[12px] tracking-tight text-black/55 dark:text-white/55">
                    <MapPin size={12} /> {s.where}
                  </div>
                  {s.state === "now" && (
                    <div className="mt-3 flex items-center gap-2">
                      <PrimaryButton className="h-10 px-4">Я сделал(а)</PrimaryButton>
                      <GhostButton className="h-10 px-4">Открыть план</GhostButton>
                    </div>
                  )}
                </Card>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------------- DOCUMENTS VAULT ---------------- */
export function DocumentsScreen() {
  return (
    <div className="flex h-full flex-col bg-[#F6F7FB] dark:bg-[#07080C]">
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 pb-10 pt-3 [&::-webkit-scrollbar]:hidden">
        <div className="flex items-center justify-between">
          <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>Мои документы</div>
          <button className="grid h-9 w-9 place-items-center rounded-full bg-[#0056FF] text-white shadow-sm">
            <Plus size={16} />
          </button>
        </div>

        <div className="mt-2 flex items-center gap-2 text-[12px] tracking-tight text-black/55 dark:text-white/55">
          <Shield size={13} className="text-emerald-600 dark:text-emerald-400" />
          Хранится локально, зашифровано
        </div>

        {/* Passport card */}
        <div className="mt-5 overflow-hidden rounded-3xl p-5 text-white shadow-[0_30px_60px_-30px_rgba(0,86,255,0.6)]"
          style={{ background: "linear-gradient(135deg,#000000 0%,#001A66 50%,#0056FF 100%)" }}>
          <div className="flex items-center justify-between">
            <span className="text-[12px] tracking-tight text-white/70">Паспорт гражданина РБ</span>
            <button className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-[11px] tracking-tight backdrop-blur">
              <EyeOff size={12} /> Скрыть
            </button>
          </div>
          <div className="mt-6 tracking-tight">Иванов Алексей</div>
          <div className="mt-1 font-mono text-[13px] tracking-[0.2em] text-white/70">MP •••• •••• 4821</div>
          <div className="mt-5 grid grid-cols-3 gap-2 text-[11px] tracking-tight text-white/60">
            <div><div>Выдан</div><div className="mt-0.5 text-white">2021</div></div>
            <div><div>Действует</div><div className="mt-0.5 text-white">до 2031</div></div>
            <div><div>Орган</div><div className="mt-0.5 text-white">РОВД Мин.</div></div>
          </div>
        </div>

        {/* Other docs */}
        <div className="mt-3 space-y-2.5">
          {[
            { n: "Медкнижка", s: "Действует до 12 авг 2027", ok: true },
            { n: "Водительское удостоверение", s: "Истекает через 6 месяцев", warn: true },
            { n: "Свидетельство о рождении ребёнка", s: "Бессрочно", ok: true },
            { n: "ИНН / Налоговая карта", s: "Бессрочно", ok: true },
          ].map((d) => (
            <Card key={d.n} className="flex items-center gap-3 p-4">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]">
                <FileText size={18} />
              </span>
              <div className="flex-1">
                <div className="tracking-tight text-black dark:text-white">{d.n}</div>
                <div className={`text-[12px] tracking-tight ${d.warn ? "text-amber-600 dark:text-amber-400" : "text-black/55 dark:text-white/55"}`}>{d.s}</div>
              </div>
              <ChevronRight size={16} className="text-black/30 dark:text-white/30" />
            </Card>
          ))}
        </div>

        <button className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-black/15 bg-transparent py-4 text-[14px] tracking-tight text-black/55 dark:border-white/15 dark:text-white/55">
          <ScanLine size={16} /> Сканировать новый документ
        </button>
      </div>
    </div>
  );
}

/* ---------------- LEGAL FEED ---------------- */
export function LegalScreen() {
  const items = [
    { t: "Налоги", title: "Новый порядок имущественного вычета", d: "с 1 июля 2026", priority: true, you: true },
    { t: "ЖКХ", title: "Изменение тарифов на отопление в г. Минск", d: "с 1 октября 2026", priority: false, you: true },
    { t: "Документы", title: "Электронный паспорт: запуск второй очереди", d: "с 15 сентября 2026", priority: true, you: false },
    { t: "Семья", title: "Расширение списка получателей детских пособий", d: "с 1 января 2027", priority: false, you: false },
  ];
  return (
    <div className="flex h-full flex-col bg-[#F6F7FB] dark:bg-[#07080C]">
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 pb-10 pt-3 [&::-webkit-scrollbar]:hidden">
        <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>Важное для вас</div>
        <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">Подобрано по вашему профилю и городу</div>

        <div className="mt-4 flex gap-2 overflow-x-auto pb-1 [&::-webkit-scrollbar]:hidden">
          {["Все","Налоги","ЖКХ","Документы","Семья","Работа"].map((t, i) => (
            <span key={t} className={`shrink-0 rounded-full px-3.5 py-2 text-[12px] tracking-tight ${i===0 ? "bg-[#0056FF] text-white" : "bg-white text-black/70 dark:bg-white/[0.06] dark:text-white/70"}`}>{t}</span>
          ))}
        </div>

        <div className="mt-4 space-y-3">
          {items.map((it) => (
            <Card key={it.title} interactive className="p-4">
              <div className="flex items-center gap-2">
                <Pill tone="lavender">{it.t}</Pill>
                {it.priority && <Pill tone="warn"><AlertCircle size={11} /> Важное</Pill>}
                {it.you && <Pill tone="ok">Касается вас</Pill>}
              </div>
              <div className="mt-2.5 tracking-tight text-black dark:text-white" style={{ fontSize: 16, lineHeight: 1.25 }}>{it.title}</div>
              <div className="mt-2 flex items-center justify-between text-[12px] tracking-tight text-black/50 dark:text-white/50">
                <span className="inline-flex items-center gap-1.5"><Clock size={12} /> {it.d}</span>
                <span className="inline-flex items-center gap-1 text-[#0056FF]">Подробнее <ArrowUpRight size={12} /></span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------------- LIFE EVENTS ---------------- */
export function LifeEventsScreen() {
  const events = [
    { i: <Baby size={20} />, n: "Рождение ребёнка", c: "12 шагов" },
    { i: <Home size={20} />, n: "Переезд", c: "8 шагов" },
    { i: <FileText size={20} />, n: "Потеря паспорта", c: "5 шагов" },
    { i: <Building2 size={20} />, n: "Покупка жилья", c: "14 шагов" },
    { i: <Briefcase size={20} />, n: "Открытие ИП", c: "9 шагов" },
    { i: <Hammer size={20} />, n: "Увольнение", c: "6 шагов" },
  ];
  return (
    <div className="flex h-full flex-col bg-[#F6F7FB] dark:bg-[#07080C]">
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 pb-10 pt-3 [&::-webkit-scrollbar]:hidden">
        <div className="tracking-tight text-black dark:text-white" style={{ fontSize: 22 }}>Жизненные ситуации</div>
        <div className="mt-1 text-[13px] tracking-tight text-black/55 dark:text-white/55">Каждая ситуация — готовый пошаговый план</div>

        <div className="mt-5 grid grid-cols-2 gap-3">
          {events.map((e, i) => (
            <Card key={e.n} interactive className="p-4">
              <div className="mb-10 grid h-11 w-11 place-items-center rounded-2xl"
                style={{ background: i % 2 ? "#E3E7FC" : "linear-gradient(135deg,#0056FF,#2277FF)", color: i % 2 ? "#0056FF" : "white" }}>
                {e.i}
              </div>
              <div className="tracking-tight text-black dark:text-white">{e.n}</div>
              <div className="mt-0.5 text-[12px] tracking-tight text-black/50 dark:text-white/50">{e.c}</div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
