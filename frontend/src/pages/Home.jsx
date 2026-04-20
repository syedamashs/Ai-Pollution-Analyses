import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { apiService } from '../services/api'
import { AQICard, EmptyState, MetricCard, PageHero, SectionHeading, Surface } from '../components/UiKit'

export default function Home({ areas }) {
  const [stats, setStats] = useState({
    totalCities: 5,
    avgAqi: 2,
    totalPlantationArea: 0,
    totalTrees: 0,
  })
  const [aqi, setAqi] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHomeData()
  }, [])

  const fetchHomeData = async () => {
    try {
      setLoading(true)
      const aqiRes = await apiService.getAQI('periyar')
      if (aqiRes.data) {
        setAqi(aqiRes.data)
        setStats({
          totalCities: 5,
          avgAqi: aqiRes.data.aqi || 100,
          totalPlantationArea: 1250000,
          totalTrees: 125000,
        })
      }
    } catch (error) {
      console.error('Error fetching home data:', error)
      setAqi(null)
      setStats({
        totalCities: 5,
        avgAqi: 100,
        totalPlantationArea: 1250000,
        totalTrees: 125000,
      })
    } finally {
      setLoading(false)
    }
  }

  const getAqiLabel = (value) => {
    if (value <= 50) return 'Good'
    if (value <= 100) return 'Satisfactory'
    if (value <= 200) return 'Moderately Polluted'
    if (value <= 300) return 'Poor'
    if (value <= 400) return 'Very Poor'
    return 'Severe'
  }

  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="GreenMadurai - Ecological Dashboard"
        title="A cleaner Madurai plan, built from live air data and satellite intelligence."
        description="Monitor AQI across Madurai areas, surface hidden plantation space, and get tree guidance that matches the pollution profile of each locality."
        accent="emerald"
        stats={[
          { label: 'Areas tracked', value: stats.totalCities, meta: 'Periyar, Arapalayam, Maatuthavani, Thirumangalam, Thiruparankundram' },
          { label: 'Current AQI', value: aqi ? aqi.category : 'Loading' },
          { label: 'Plantation area', value: `${(stats.totalPlantationArea / 1000000).toFixed(1)}M m²` },
          { label: 'Trees recommended', value: `${(stats.totalTrees / 1000).toFixed(0)}K` },
        ]}
      />

      <Surface>
        <SectionHeading
          title="Fast entry points"
          description="The most useful actions are surfaced first so the app feels like a dashboard, not a brochure."
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <QuickActionCard
            icon="🔍"
            title="Check AQI & Trees"
            description="Monitor air quality across Madurai areas and get personalized tree recommendations."
            link="/aqi-trees"
            tone="emerald"
          />
          <QuickActionCard
            icon="🛰️"
            title="Area Analysis"
            description="Inspect plantation opportunities in each area from satellite imagery."
            link="/area-analysis"
            tone="violet"
          />
          <QuickActionCard
            icon="🔮"
            title="AQI Forecasting"
            description="See the next 7 days of AQI movement before planning work."
            link="/forecasting"
            tone="sky"
          />
          <QuickActionCard
            icon="📈"
            title="Model Evaluation"
            description="Inspect performance and confidence across both models."
            link="/model-evaluation"
            tone="amber"
          />
          <QuickActionCard
            icon="ℹ️"
            title="About Project"
            description="Learn the mission, stack, and the data sources behind it."
            link="/about"
            tone="rose"
          />
        </div>
      </Surface>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <Surface>
          <SectionHeading
            title="Why it feels more useful now"
            description="The app now guides the user toward actions, not just raw data."
          />
          <div className="grid gap-4 md:grid-cols-2">
            <FeatureCard title="Real-time AQI monitoring" description="Track air quality across multiple cities with live data updates." icon="🌍" />
            <FeatureCard title="Smart tree recommendations" description="AI-powered suggestions for pollution-absorbing trees suited to the area." icon="🌳" />
            <FeatureCard title="Satellite imagery analysis" description="Detect free land for plantation and compare coverage at a glance." icon="🛰️" />
            <FeatureCard title="7-day forecasting" description="Predict AQI trends with a simple statistical model that loads quickly." icon="📈" />
          </div>
        </Surface>

        <Surface className="flex flex-col justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-emerald-700">Live status</p>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-950">Current AQI for Madurai</h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              The dashboard keeps fallback data ready, so the experience stays stable even when the API is busy.
            </p>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            <MetricCard icon="💨" label="AQI state" value={aqi ? (aqi.category || getAqiLabel(aqi.aqi)) : 'Loading'} tone="emerald" />
            <MetricCard icon="🌱" label="Tree coverage" value={`${(stats.totalTrees / 1000).toFixed(0)}K`} tone="sky" />
          </div>

          <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-5">
            <p className="text-sm font-semibold text-slate-950">Quick note</p>
            <p className="mt-2 text-sm leading-7 text-slate-600">
              Open the AQI page first if you want the most visual, high-signal screen in the app.
            </p>
          </div>
        </Surface>
      </div>
    </div>
  )
}

function QuickActionCard({ icon, title, description, link, tone = 'emerald' }) {
  const toneMap = {
    emerald: 'from-emerald-500 to-teal-500',
    violet: 'from-violet-500 to-fuchsia-500',
    sky: 'from-sky-500 to-cyan-500',
    amber: 'from-amber-500 to-orange-500',
    rose: 'from-rose-500 to-pink-500',
  }

  return (
    <Link to={link}>
      <div className="group glass-panel h-full rounded-[1.5rem] p-6 transition duration-300 hover:-translate-y-1 hover:shadow-[0_30px_60px_rgba(15,23,42,0.12)]">
        <div className={`inline-flex rounded-2xl bg-gradient-to-br px-4 py-3 text-2xl text-white shadow-lg ${toneMap[tone]}`}>
          {icon}
        </div>
        <h3 className="mt-5 text-lg font-extrabold tracking-tight text-slate-950">{title}</h3>
        <p className="mt-2 text-sm leading-7 text-slate-600">{description}</p>
        <div className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-slate-950">
          Explore
          <span className="transition group-hover:translate-x-1">→</span>
        </div>
      </div>
    </Link>
  )
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="rounded-[1.5rem] border border-slate-200/70 bg-slate-50/80 p-6">
      <div className="text-3xl">{icon}</div>
      <h3 className="mt-4 text-lg font-extrabold tracking-tight text-slate-950">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-slate-600">{description}</p>
    </div>
  )
}
