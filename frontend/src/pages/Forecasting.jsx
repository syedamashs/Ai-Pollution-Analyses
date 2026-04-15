import React, { useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { EmptyState, PageHero, SectionHeading, Surface } from '../components/UiKit'

export default function Forecasting({ areas }) {
  const [selectedArea, setSelectedArea] = useState(areas[0]?.id || 'madurai')
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchForecast()
  }, [selectedArea])

  const fetchForecast = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await apiService.getForecast(selectedArea)
      if (res.data && res.data.forecast) {
        setForecast(res.data.forecast)
      } else {
        setError('Invalid forecast data received')
      }
    } catch (err) {
      setError('Failed to load forecast. Check your connection.')
      console.error(err)
      setForecast(null)
    } finally {
      setLoading(false)
    }
  }

  const getAqiColor = (value) => {
    if (value <= 1.5) return '#10b981'
    if (value <= 2.5) return '#eab308'
    if (value <= 3.5) return '#f97316'
    if (value <= 4.5) return '#ef4444'
    return '#8b5cf6'
  }

  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="Forecasting"
        title="Seven-day AQI movement, presented like an operations view."
        description="The forecast screen focuses on trend, confidence, and the exact values you need to plan next steps without waiting on heavy compute."
        accent="emerald"
        stats={[
          { label: 'City', value: areas.find((area) => area.id === selectedArea)?.name || 'Madurai' },
          { label: 'Forecast avg', value: forecast ? forecast.statistics.forecast_avg.toFixed(1) : 'Loading' },
          { label: 'Forecast min', value: forecast ? forecast.statistics.forecast_min.toFixed(1) : '—' },
          { label: 'Forecast max', value: forecast ? forecast.statistics.forecast_max.toFixed(1) : '—' },
        ]}
      />

      <Surface>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-500">Filter</p>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-slate-950">Select a city</h2>
          </div>
          <select
            value={selectedArea}
            onChange={(e) => setSelectedArea(e.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-900 shadow-sm outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-500/10 lg:w-72"
          >
            {areas.map(area => (
              <option key={area.id} value={area.id}>{area.name}</option>
            ))}
          </select>
        </div>
      </Surface>

        {loading && (
          <div className="glass-panel rounded-[1.75rem] py-16 text-center">
            <div className="mx-auto h-14 w-14 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-500" />
            <p className="mt-4 text-sm font-semibold text-slate-600">Loading forecast...</p>
          </div>
        )}

        {error && (
          <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-rose-800 shadow-sm">
            {error}
          </div>
        )}

        {forecast && (
          <>
            {/* Statistics */}
            <div className="grid gap-4 md:grid-cols-4">
              <StatBox label="Current AQI" value={forecast.statistics.current_aqi.toFixed(1)} tone="emerald" />
              <StatBox label="7-Day Average" value={forecast.statistics.forecast_avg.toFixed(1)} tone="sky" />
              <StatBox label="Min Forecast" value={forecast.statistics.forecast_min.toFixed(1)} tone="amber" />
              <StatBox label="Max Forecast" value={forecast.statistics.forecast_max.toFixed(1)} tone="rose" />
            </div>

            {/* Chart */}
            <Surface className="mt-8">
              <SectionHeading title="7-day AQI forecast" description="The chart uses a muted frame and one accent line, which keeps the forecast easy to read." />
              <ForecastChart forecast={forecast} />
            </Surface>

            {/* Model Info */}
            <Surface className="mt-8">
              <SectionHeading title="Model information" description="This block explains the forecast engine without overwhelming the page." />
              <div className="rounded-[1.5rem] border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5">
                <h4 className="font-extrabold text-emerald-950 mb-2">🧠 Holt-Winters Exponential Smoothing</h4>
                <p className="text-sm leading-7 text-emerald-900/80">This model is fast, stable, and works well for AQI histories with repeating weekly movement. It uses the last 100 days of AQI directly without heavy training.</p>
              </div>
            </Surface>

            {/* Forecast Table */}
            <Surface className="overflow-hidden">
              <div className="border-b border-slate-200 pb-4">
                <h3 className="text-lg font-extrabold tracking-tight text-slate-950">Detailed 7-day predictions</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-4 text-left font-bold uppercase tracking-[0.18em] text-slate-500">Date</th>
                      <th className="px-6 py-4 text-center font-bold uppercase tracking-[0.18em] text-slate-500">Forecast</th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecast.forecast_dates.map((date, idx) => (
                      <tr key={date} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/80'}>
                        <td className="px-6 py-4 font-semibold text-slate-900">{date}</td>
                        <td className="px-6 py-4 text-center font-extrabold text-emerald-600">
                          {forecast.model.values[idx].toFixed(1)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Surface>
          </>
        )}
    </div>
  )
}

function StatBox({ label, value, color = 'text-gray-900', tone = 'emerald' }) {
  const toneMap = {
    emerald: 'text-emerald-700',
    sky: 'text-sky-700',
    amber: 'text-amber-700',
    rose: 'text-rose-700',
  }

  return (
    <div className="glass-panel rounded-[1.5rem] p-4">
      <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-extrabold tracking-tight ${toneMap[tone] || color}`}>{value}</p>
    </div>
  )
}

function ForecastChart({ forecast }) {
  const values = forecast.model.values
  const minVal = Math.min(...values, 1)
  const maxVal = Math.max(...values, 5)
  const range = maxVal - minVal || 1

  const canvasWidth = 800
  const canvasHeight = 300
  const padding = { top: 30, right: 30, bottom: 50, left: 60 }
  const innerW = canvasWidth - padding.left - padding.right
  const innerH = canvasHeight - padding.top - padding.bottom

  const x = (i) => padding.left + (i / (values.length - 1 || 1)) * innerW
  const y = (v) => padding.top + innerH - ((v - minVal) / range) * innerH

  const points = values.map((v, i) => `${x(i)},${y(v)}`).join(' ')

  return (
    <svg width="100%" height={canvasHeight} viewBox={`0 0 ${canvasWidth} ${canvasHeight}`} className="w-full">
      {/* Background */}
      <rect width={canvasWidth} height={canvasHeight} rx="24" fill="#f8fafc" />

      {/* Grid lines */}
      {[0, 1, 2, 3, 4, 5].map((i) => {
        const val = minVal + (range / 5) * i
        const yVal = y(val)
        return (
          <g key={i}>
            <line x1={padding.left} y1={yVal} x2={padding.left + innerW} y2={yVal} stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4" />
            <text x={padding.left - 10} y={yVal + 4} fontSize="12" textAnchor="end" fill="#64748b">{Math.round(val)}</text>
          </g>
        )
      })}

      {/* Axes */}
      <line x1={padding.left} y1={padding.top + innerH} x2={padding.left + innerW} y2={padding.top + innerH} stroke="#cbd5e1" strokeWidth="2" />
      <line x1={padding.left} y1={padding.top} x2={padding.left} y2={padding.top + innerH} stroke="#cbd5e1" strokeWidth="2" />

      {/* Line */}
      <polyline points={points} fill="none" stroke="#0f766e" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />

      {/* Points */}
      {values.map((v, i) => (
        <circle key={i} cx={x(i)} cy={y(v)} r="5" fill="#ffffff" stroke="#0f766e" strokeWidth="3" />
      ))}

      {/* X-axis labels */}
      {forecast.forecast_dates.map((date, i) => (
        <text key={date} x={x(i)} y={padding.top + innerH + 20} fontSize="12" textAnchor="middle" fill="#64748b">
          {date.substring(5)}
        </text>
      ))}

      {/* Y-axis label */}
      <text x="20" y={padding.top + innerH / 2} fontSize="14" textAnchor="middle" fill="#64748b" fontWeight="bold" transform={`rotate(-90 20 ${padding.top + innerH / 2})`}>
        AQI Level
      </text>
    </svg>
  )
}
