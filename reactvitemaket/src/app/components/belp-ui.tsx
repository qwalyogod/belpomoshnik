import { ReactNode } from "react";
import { motion } from "motion/react";

export const COLORS = {
  royal: "#0056FF",
  azure: "#2277FF",
  lavender: "#E3E7FC",
};

export function Pill({ children, tone = "lavender" }: { children: ReactNode; tone?: "lavender" | "royal" | "azure" | "ghost" | "warn" | "ok" }) {
  const map: Record<string, string> = {
    lavender: "bg-[#E3E7FC] text-[#0056FF] dark:bg-[#0E1A3A] dark:text-[#7FA8FF]",
    royal: "bg-[#0056FF] text-white",
    azure: "bg-[#2277FF] text-white",
    ghost: "bg-black/[0.04] text-black/70 dark:bg-white/10 dark:text-white/70",
    warn: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
    ok: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] tracking-tight ${map[tone]}`}>
      {children}
    </span>
  );
}

export function PrimaryButton({ children, className = "", icon, onClick }: { children: ReactNode; className?: string; icon?: ReactNode; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`group relative inline-flex h-12 items-center justify-center gap-2 overflow-hidden rounded-2xl bg-[#0056FF] px-5 text-white shadow-[0_10px_30px_-12px_rgba(0,86,255,0.55)] transition-all active:translate-y-[1px] hover:bg-[#0049DB] ${className}`}
    >
      <span className="absolute inset-0 bg-gradient-to-r from-[#0056FF] via-[#2277FF] to-[#0056FF] opacity-0 transition-opacity group-hover:opacity-100" />
      <span className="relative inline-flex items-center gap-2 tracking-tight">
        {children}
        {icon}
      </span>
    </button>
  );
}

export function GhostButton({ children, className = "", onClick }: { children: ReactNode; className?: string; onClick?: () => void }) {
  return (
    <button onClick={onClick} className={`inline-flex h-12 items-center justify-center rounded-2xl border border-black/10 bg-white/60 px-5 tracking-tight text-black backdrop-blur transition-colors hover:bg-white dark:border-white/10 dark:bg-white/[0.04] dark:text-white dark:hover:bg-white/[0.08] ${className}`}>
      {children}
    </button>
  );
}

export function Card({ children, className = "", interactive = false }: { children: ReactNode; className?: string; interactive?: boolean }) {
  return (
    <div
      className={`relative rounded-3xl border border-black/[0.06] bg-white p-5 shadow-[0_1px_0_rgba(0,0,0,0.02),0_24px_48px_-32px_rgba(15,23,42,0.18)] dark:border-white/[0.06] dark:bg-[#0F1117] dark:shadow-[0_1px_0_rgba(255,255,255,0.02),0_24px_48px_-24px_rgba(0,0,0,0.6)] ${interactive ? "transition-all hover:-translate-y-[2px] hover:shadow-[0_1px_0_rgba(0,0,0,0.02),0_32px_60px_-28px_rgba(15,23,42,0.28)]" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return <div className="mb-4 tracking-tight text-black/50 dark:text-white/50">{children}</div>;
}

export function PhoneFrame({ children, label }: { children: ReactNode; label?: string }) {
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative h-[760px] w-[370px] rounded-[48px] bg-black p-[10px] shadow-[0_50px_120px_-30px_rgba(0,0,0,0.35),0_0_0_1px_rgba(0,0,0,0.05)] dark:shadow-[0_50px_120px_-30px_rgba(0,0,0,0.7)]">
        <div className="relative h-full w-full overflow-hidden rounded-[40px] bg-[#F6F7FB] dark:bg-[#07080C]">
          <div className="absolute left-1/2 top-2 z-30 h-6 w-28 -translate-x-1/2 rounded-full bg-black" />
          {children}
        </div>
      </div>
      {label && <div className="text-[12px] tracking-tight text-black/50 dark:text-white/40">{label}</div>}
    </div>
  );
}

export function StatusBar() {
  return (
    <div className="relative z-20 flex items-center justify-between px-7 pt-4 text-[12px] tracking-tight text-black dark:text-white">
      <span>9:41</span>
      <span className="flex items-center gap-1.5 opacity-80">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
        <span className="inline-block h-1.5 w-2 rounded-sm bg-current" />
      </span>
    </div>
  );
}

export function Logo({ size = 28, white = false }: { size?: number; white?: boolean }) {
  return (
    <div className="inline-flex items-center gap-2.5">
      <motion.div
        initial={{ rotate: -8, scale: 0.9 }}
        animate={{ rotate: 0, scale: 1 }}
        transition={{ type: "spring", stiffness: 220, damping: 18 }}
        className="relative grid place-items-center rounded-[10px]"
        style={{ width: size, height: size, background: "linear-gradient(135deg,#0056FF 0%,#2277FF 60%,#9BB8FF 100%)" }}
      >
        <span className="tracking-tight text-white" style={{ fontSize: size * 0.5 }}>Б</span>
        <span className="absolute inset-0 rounded-[10px] ring-1 ring-inset ring-white/30" />
      </motion.div>
      <span className={`tracking-tight ${white ? "text-white" : "text-black dark:text-white"}`} style={{ fontSize: size * 0.55 }}>
        Белпомощник
      </span>
    </div>
  );
}
