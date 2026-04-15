import React, { useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { AQICard, EmptyState, MetricCard, PageHero, SectionHeading, Surface } from '../components/UiKit'

export default function AqiTrees({ areas }) {
  const [selectedArea, setSelectedArea] = useState(areas[0]?.id || 'madurai')
  const [aqi, setAqi] = useState(null)
  const [trend, setTrend] = useState([])
  const [trees, setTrees] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchAreaData()
  }, [selectedArea])

  const fetchAreaData = async () => {
    try {
      setLoading(true)
      const [aqiRes, trendRes, treesRes] = await Promise.all([
        apiService.getAQI(selectedArea),
        apiService.getAQITrend(selectedArea),
        apiService.getTreeRecommendations(selectedArea),
      ])
      
      if (aqiRes.data) setAqi(aqiRes.data)
      if (Array.isArray(trendRes.data)) setTrend(trendRes.data)
      if (treesRes.data && treesRes.data.recommendations) {
        setTrees(Array.isArray(treesRes.data.recommendations) ? treesRes.data.recommendations : [])
      } else {
        setTrees([])
      }
    } catch (error) {
      console.error('Error fetching area data:', error)
      setAqi(null)
      setTrend([])
      setTrees([])
    } finally {
      setLoading(false)
    }
  }

  const getAqiColor = (value) => {
    if (value <= 1) return { bg: '#dcfce7', text: '#15803d', label: 'Good' }
    if (value <= 2) return { bg: '#fef3c7', text: '#b45309', label: 'Fair' }
    if (value <= 3) return { bg: '#fed7aa', text: '#92400e', label: 'Moderate' }
    if (value <= 4) return { bg: '#fecaca', text: '#7f1d1d', label: 'Poor' }
    return { bg: '#f4c4f3', text: '#7c2d12', label: 'Very Poor' }
  }

  const currentColor = aqi ? getAqiColor(aqi.aqi) : null

  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="AQI intelligence"
        title="See air quality and tree guidance in one scan."
        description="This page balances the signal: live AQI state, a 7-day trend, and tree recommendations that react to the pollution profile."
        accent="sky"
        stats={[
          { label: 'Selected area', value: areas.find((area) => area.id === selectedArea)?.name || 'Madurai' },
          { label: 'AQI level', value: aqi ? getAqiColor(aqi.aqi).label : 'Loading' },
          { label: 'Trend points', value: trend.length || 0 },
          { label: 'Trees shown', value: trees.length || 0 },
        ]}
      />

      <Surface>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-500">Filter</p>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-slate-950">Choose an area</h2>
          </div>
          <select
            value={selectedArea}
            onChange={(e) => setSelectedArea(e.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-900 shadow-sm outline-none transition focus:border-sky-400 focus:ring-4 focus:ring-sky-500/10 lg:w-80"
          >
            {areas.map((area) => (
              <option key={area.id} value={area.id}>{area.name}</option>
            ))}
          </select>
        </div>
      </Surface>

      {loading && (
          <div className="glass-panel rounded-[1.75rem] py-16 text-center">
            <div className="mx-auto h-14 w-14 animate-spin rounded-full border-4 border-sky-200 border-t-sky-500" />
            <p className="mt-4 text-sm font-semibold text-slate-600">Loading air data and recommendation stack...</p>
          </div>
        )}
        
      {!loading && (
        <>
            {/* Current AQI Display */}
            {aqi && (
              <AQICard
                aqi={aqi.aqi}
                category={aqi.category}
                pm25={aqi.pm25}
                pm10={aqi.pm10}
                no2={aqi.no2}
                so2={aqi.so2}
                co={aqi.co}
                o3={aqi.o3}
              />
            )}

            {/* Tree Recommendations */}
            <Surface>
              <SectionHeading
                title={`Recommended trees for ${areas.find((a) => a.id === selectedArea)?.name}`}
                description="The cards below are tuned to the current AQI level and are meant to feel like a shortlist, not a long catalog."
              />
              {trees && trees.length > 0 ? (
                <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                  {trees.map((tree, idx) => (
                    <TreeCard key={idx} tree={tree} />
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No tree recommendations available"
                  description="Check your connection or try another area. The backend now returns a safe fallback if the model is unavailable."
                />
              )}
            </Surface>

            {/* AQI Scale Reference */}
            <Surface>
              <SectionHeading title="Understanding AQI levels" description="A reference strip to keep the color coding readable and intentional." />
              <div className="grid gap-4 md:grid-cols-5">
                {[
                  { value: 1, label: 'Good', bg: '#dcfce7', color: '#15803d', range: '0-50 µg/m³' },
                  { value: 2, label: 'Fair', bg: '#fef3c7', color: '#b45309', range: '50-100 µg/m³' },
                  { value: 3, label: 'Moderate', bg: '#fed7aa', color: '#92400e', range: '100-150 µg/m³' },
                  { value: 4, label: 'Poor', bg: '#fecaca', color: '#7f1d1d', range: '150-200 µg/m³' },
                  { value: 5, label: 'Very Poor', bg: '#f4c4f3', color: '#7c2d12', range: '200+ µg/m³' },
                ].map(level => (
                  <div key={level.value} style={{ backgroundColor: level.bg }} className="rounded-2xl p-4 text-center">
                    <p className="font-extrabold" style={{ color: level.color }}>{level.label}</p>
                    <p className="mt-2 text-xs font-semibold" style={{ color: level.color }}>{level.range}</p>
                  </div>
                ))}
              </div>
            </Surface>
        </>
      )}
    </div>
  )
}

function TreeCard({ tree }) {
  return (
    <div className="group rounded-[1.5rem] border border-slate-200 bg-white/85 p-6 shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-[0_24px_60px_rgba(15,23,42,0.12)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-lg font-extrabold tracking-tight text-slate-950">{tree.name}</h4>
          <p className="mt-1 text-sm italic text-slate-500">{tree.scientificName}</p>
        </div>
        <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-700">
          {tree.pollutionAbsorption}
        </span>
      </div>
      <p className="mt-4 text-sm leading-7 text-slate-600"><span className="font-bold text-slate-950">Reason:</span> {tree.reason}</p>
      <p className="mt-3 text-sm leading-7 text-slate-600"><span className="font-bold text-slate-950">Benefits:</span> {tree.benefits}</p>
    </div>
  )
}
