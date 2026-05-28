import React from "react";
import { cn } from "../lib/utils";

export const Card = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("bg-white rounded-[16px] shadow-sm border border-gray-100 overflow-hidden", className)} {...props}>
    {children}
  </div>
);

export const Button = ({ className, variant = "primary", size = "md", ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "outline" | "ghost" | "danger", size?: "sm" | "md" | "lg" }) => {
  const baseStyles = "inline-flex items-center justify-center rounded-[12px] font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
  const variants = {
    primary: "bg-emerald-600 text-white hover:bg-emerald-700 focus:ring-emerald-500",
    secondary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
    outline: "border-2 border-gray-200 bg-transparent hover:border-gray-300 text-gray-900 focus:ring-gray-200",
    ghost: "bg-transparent hover:bg-gray-100 text-gray-700 focus:ring-gray-200",
    danger: "bg-red-50 text-red-600 hover:bg-red-100 focus:ring-red-500"
  };
  const sizes = {
    sm: "h-9 px-4 text-sm",
    md: "h-12 px-6 text-base",
    lg: "h-14 px-8 text-lg"
  };
  
  return (
    <button className={cn(baseStyles, variants[variant], sizes[size], className)} {...props} />
  );
};

export const Input = ({ className, icon, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { icon?: React.ReactNode }) => (
  <div className="relative w-full">
    {icon && (
      <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
        {icon}
      </div>
    )}
    <input
      className={cn(
        "w-full h-14 bg-white border border-gray-200 rounded-[12px] px-4 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors",
        icon && "pl-12",
        className
      )}
      {...props}
    />
  </div>
);

export const Badge = ({ className, variant = "default", children }: { className?: string, variant?: "default" | "success" | "warning" | "error" | "blue", children: React.ReactNode }) => {
  const variants = {
    default: "bg-gray-100 text-gray-700",
    success: "bg-emerald-50 text-emerald-700",
    warning: "bg-yellow-50 text-yellow-700",
    error: "bg-red-50 text-red-700",
    blue: "bg-blue-50 text-blue-700"
  };
  return (
    <span className={cn("inline-flex items-center px-3 py-1 rounded-full text-xs font-medium", variants[variant], className)}>
      {children}
    </span>
  );
};

export const Progress = ({ value, className }: { value: number, className?: string }) => (
  <div className={cn("w-full bg-gray-100 rounded-full h-2", className)}>
    <div 
      className="bg-emerald-500 h-2 rounded-full transition-all duration-300" 
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);

export { Checkbox } from "./ui/checkbox";
export { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "./ui/accordion";
