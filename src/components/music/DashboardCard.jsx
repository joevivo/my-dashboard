import { ChevronDown } from "lucide-react";

export default function DashboardCard({
  title,
  children,
  className = "",
  isOpen = true,
  onToggle,
}) {
  const isCollapsible = typeof onToggle === "function";

  return (
    <section
      className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950/40 ${className}`}
    >
      {isCollapsible ? (
        <button
          type="button"
          onClick={onToggle}
          className="flex w-full items-center justify-between gap-4 text-left"
        >
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
            {title}
          </p>
          <ChevronDown
            size={18}
            className={`shrink-0 text-slate-400 transition-transform ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </button>
      ) : (
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
          {title}
        </p>
      )}

      {isOpen ? (
        <div className="mt-4">
          {children}
        </div>
      ) : null}
    </section>
  );
}
