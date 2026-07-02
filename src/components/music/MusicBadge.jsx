export default function MusicBadge({ children, tone = "slate" }) {
  const tones = {
    slate: "bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-300",
    relationship: "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300",
    album: "bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300",
    playlist: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300",
    station: "bg-indigo-100 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300",
    story: "bg-sky-100 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300",
  };

  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold ${tones[tone] || tones.slate}`}>
      {children}
    </span>
  );
}
