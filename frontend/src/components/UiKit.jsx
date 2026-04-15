import React from 'react'

export function PageShell({ children }) {
  return <div className="page-grid min-h-screen">{children}</div>
}

export function PageHero({ eyebrow, title, description, accent = 'emerald', stats = [] }) {
  const accentMap = {
    emerald: 'from-emerald-500 via-teal-500 to-cyan-500',
    sky: 'from-sky-500 via-blue-500 to-indigo-500',
    violet: 'from-violet-500 via-fuchsia-500 to-pink-500',
    amber: 'from-amber-500 via-orange-500 to-rose-500',
  }

  return (
    <div className="relative overflow-hidden rounded-[2rem] border border-white/50 bg-white/75 px-6 py-10 shadow-[0_30px_90px_rgba(15,23,42,0.10)] backdrop-blur-xl md:px-10 md:py-12">
      <div className={`absolute inset-0 bg-gradient-to-br ${accentMap[accent] || accentMap.emerald} opacity-[0.10]`} />
      <div className="absolute -right-12 -top-12 h-40 w-40 rounded-full bg-white/60 blur-3xl" />
      <div className="absolute -bottom-16 left-1/3 h-52 w-52 rounded-full bg-emerald-200/40 blur-3xl" />
      <div className="relative z-10">
        {eyebrow ? (
          <p className="mb-3 inline-flex rounded-full border border-white/60 bg-white/70 px-3 py-1 text-xs font-bold uppercase tracking-[0.25em] text-slate-600">
            {eyebrow}
          </p>
        ) : null}
        <h1 className="max-w-4xl text-4xl font-extrabold tracking-tight text-slate-950 md:text-6xl">{title}</h1>
        <p className="mt-4 max-w-3xl text-base leading-8 text-slate-600 md:text-lg">{description}</p>

        {stats.length > 0 ? (
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="glass-panel rounded-2xl p-4">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">{stat.label}</p>
                <p className="mt-2 text-2xl font-extrabold text-slate-950">{stat.value}</p>
                {stat.meta ? <p className="mt-1 text-sm text-slate-500">{stat.meta}</p> : null}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  )
}

export function SectionHeading({ title, description, action }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-950 md:text-3xl">{title}</h2>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-600 md:text-base">{description}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  )
}

export function MetricCard({ icon, label, value, helper, tone = 'emerald' }) {
  const toneMap = {
    emerald: 'from-emerald-500/10 to-emerald-500/5 text-emerald-700',
    sky: 'from-sky-500/10 to-sky-500/5 text-sky-700',
    violet: 'from-violet-500/10 to-violet-500/5 text-violet-700',
    amber: 'from-amber-500/10 to-amber-500/5 text-amber-700',
    rose: 'from-rose-500/10 to-rose-500/5 text-rose-700',
  }

  return (
    <div className="glass-panel rounded-3xl p-5 transition duration-300 hover:-translate-y-1 hover:shadow-[0_30px_70px_rgba(15,23,42,0.12)]">
      <div className={`inline-flex rounded-2xl bg-gradient-to-br px-3 py-2 ${toneMap[tone] || toneMap.emerald}`}>
        <span className="text-xl">{icon}</span>
      </div>
      <p className="mt-4 text-sm font-semibold text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-extrabold tracking-tight text-slate-950">{value}</p>
      {helper ? <p className="mt-2 text-sm leading-6 text-slate-500">{helper}</p> : null}
    </div>
  )
}

export function Surface({ children, className = '' }) {
  return <div className={`glass-panel rounded-[1.75rem] p-6 md:p-8 ${className}`}>{children}</div>
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="glass-panel rounded-[1.75rem] p-8 text-center">
      <p className="text-xl font-bold text-slate-950">{title}</p>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-7 text-slate-600">{description}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  )
}
