import { ChevronDown } from "lucide-react";

export default function DashboardSection({
  title,
  Icon,
  color = "slate",
  summary,
  children,
  isOpen = true,
  onToggle,
}) {
  let sectionClasses = "border-slate-200 bg-white";

  if (color === "purple") {
    sectionClasses = "border-purple-200 bg-purple-50/70";
  }

  if (color === "amber") {
    sectionClasses = "border-amber-200 bg-amber-50/70";
  }

  if (color === "sky") {
    sectionClasses = "border-sky-200 bg-sky-50/70";
  }

  if (color === "rose") {
    sectionClasses = "border-rose-200 bg-rose-50/70";
  }

  if (color === "green") {
    sectionClasses = "border-emerald-200 bg-emerald-50/70";
  }

  return (
    <div
      className={`dashboard-section p-6 space-y-4 border rounded-2xl shadow-sm transition hover:shadow-md ${sectionClasses}`}
    >
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-4 text-left group rounded-xl"
      >
        <div className="flex items-center gap-3 min-w-0">
          {Icon && (
            <span className="dashboard-section-icon flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/70 border border-white/80 shadow-sm">
              <Icon className="dashboard-section-icon-svg h-5 w-5 text-slate-500 group-hover:text-slate-700 transition" />
            </span>
          )}

          <div className="min-w-0">
            <h2 className="dashboard-section-title text-xl font-bold leading-tight">{title}</h2>

            {!isOpen && summary && (
              <p className="dashboard-section-summary text-sm text-slate-500 mt-1">{summary}</p>
            )}
          </div>
        </div>

        <ChevronDown
          className={`dashboard-section-chevron h-5 w-5 shrink-0 text-slate-400 transition-transform duration-200 group-hover:text-slate-600 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && children}
    </div>
  );
}