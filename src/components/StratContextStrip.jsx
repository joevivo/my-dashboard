export default function StratContextStrip({ items = [] }) {
  const visibleItems = items.filter((item) => item?.value);

  if (!visibleItems.length) return null;

  return (
    <div className="dashboard-panel p-4">
      <div className="flex flex-wrap gap-3">
        {visibleItems.map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800/70"
          >
            <div className="text-[10px] font-bold uppercase tracking-wide text-slate-400">
              {item.label}
            </div>
            <div className="mt-1 font-semibold text-slate-800 dark:text-slate-100">
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
