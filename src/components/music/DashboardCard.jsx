export default function DashboardCard({ title, children, className = "" }) {
  return (
    <section
      className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950/40 ${className}`}
    >
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
        {title}
      </p>

      <div className="mt-4">
        {children}
      </div>
    </section>
  );
}
