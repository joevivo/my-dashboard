export default function FeaturedMemoryCard() {
  return (
    <div className="mb-5 rounded-2xl border border-sky-400/30 bg-gradient-to-br from-slate-900 via-slate-900 to-sky-950 p-5 shadow-lg">
      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-sky-300">
        Featured Memory
      </p>
      <h3 className="mt-3 text-2xl font-black text-white">
        Billie Holiday Never Left
      </h3>
      <p className="mt-3 text-sm leading-6 text-slate-300">
        Across 11 years of listening history, Billie Holiday appeared 99 times.
        Never dominant. Always present.
      </p>
    </div>
  );
}
