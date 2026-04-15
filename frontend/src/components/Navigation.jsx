import React from 'react'
import { Link, NavLink as RouterNavLink } from 'react-router-dom'

export default function Navigation() {
  const [isOpen, setIsOpen] = React.useState(false)

  return (
    <nav className="sticky top-0 z-50 border-b border-white/60 bg-white/75 backdrop-blur-xl">
      <div className="mx-auto max-w-[1500px] px-4 sm:px-6 lg:px-8">
        <div className="flex h-20 items-center justify-between gap-4">
          <div className="flex items-center">
            <Link to="/" className="flex items-center">
              <span className="flex items-center gap-3 text-xl font-extrabold tracking-tight text-slate-950 md:text-2xl">
                <span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 text-white shadow-lg shadow-emerald-500/20">
                  🌳
                </span>
                <span>
                  GreenMadurai
                  <span className="block text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">Environmental Intelligence</span>
                </span>
              </span>
            </Link>
          </div>

          {/* Desktop menu */}
          <div className="hidden items-center gap-1 rounded-full border border-slate-200 bg-slate-50/80 p-1 md:flex">
            <NavLink to="/" label="Home" />
            <NavLink to="/aqi-trees" label="AQI & Trees" />
            <NavLink to="/area-analysis" label="Area Analysis" />
            <NavLink to="/forecasting" label="Forecasting" />
            <NavLink to="/model-evaluation" label="Model Evaluation" />
            <NavLink to="/about" label="About" />
          </div>

          <Link
            to="/aqi-trees"
            className="hidden rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-slate-950/20 transition hover:-translate-y-0.5 hover:bg-slate-800 md:inline-flex"
          >
            Open Dashboard
          </Link>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white p-3 text-slate-700 shadow-sm"
            >
              <svg className="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white/95 px-4 py-4 backdrop-blur-xl">
          <div className="space-y-2">
            <MobileNavLink to="/" label="Home" />
            <MobileNavLink to="/aqi-trees" label="AQI & Trees" />
            <MobileNavLink to="/area-analysis" label="Area Analysis" />
            <MobileNavLink to="/forecasting" label="Forecasting" />
            <MobileNavLink to="/model-evaluation" label="Model Evaluation" />
            <MobileNavLink to="/about" label="About" />
          </div>
        </div>
      )}
    </nav>
  )
}

function NavLink({ to, label }) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        [
          'rounded-full px-4 py-2 text-sm font-semibold transition duration-200',
          isActive
            ? 'bg-white text-slate-950 shadow-sm ring-1 ring-slate-200'
            : 'text-slate-600 hover:bg-white hover:text-slate-950',
        ].join(' ')
      }
    >
      {label}
    </RouterNavLink>
  )
}

function MobileNavLink({ to, label }) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        [
          'block rounded-2xl px-4 py-3 text-base font-semibold transition',
          isActive
            ? 'bg-slate-950 text-white'
            : 'bg-slate-50 text-slate-700 hover:bg-slate-100 hover:text-slate-950',
        ].join(' ')
      }
    >
      {label}
    </RouterNavLink>
  )
}
