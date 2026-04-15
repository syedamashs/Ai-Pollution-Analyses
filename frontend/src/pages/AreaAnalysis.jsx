import React, { useState, useEffect } from 'react'
import { apiService } from '../services/api'
import { EmptyState, PageHero, SectionHeading, Surface } from '../components/UiKit'

export default function AreaAnalysis({ areas }) {
  const [selectedArea, setSelectedArea] = useState(areas[0]?.id || 'madurai')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchAnalysis()
  }, [selectedArea])

  const fetchAnalysis = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await apiService.getAreaAnalysis(selectedArea)
      if (res.data) {
        setAnalysis(res.data)
      } else {
        setError('No analysis data available')
        setAnalysis(null)
      }
    } catch (error) {
      console.error('Error fetching analysis:', error)
      setError('Failed to load analysis. Please try again.')
      setAnalysis(null)
    } finally {
      setLoading(false)
    }
  }

  const selectedAreaName = areas.find((area) => area.id === selectedArea)?.name || 'Madurai'
  const freeLandPercentage = analysis?.freeLandPercentage ?? 0
  const greenPercentage = analysis?.greenPercentage ?? 0
  const estimatedTrees = analysis?.estimatedTrees ?? 0
  const plantationArea = analysis?.plantationArea ?? 0
  const imageCount = analysis?.image_count ?? 0

  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="Satellite intelligence"
        title="Map plantation opportunity from image data, not guesswork."
        description="This page turns each city into a quick land-suitability snapshot with free-area metrics, vegetation coverage, and image-level evidence."
        accent="violet"
        stats={[
          { label: 'Area', value: selectedAreaName },
          { label: 'Images analyzed', value: imageCount },
          { label: 'Free land', value: `${freeLandPercentage}%` },
          { label: 'Plantation area', value: `${(plantationArea / 1000).toFixed(0)}K m²` },
        ]}
      />

      <Surface>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-slate-500">Filter</p>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tight text-slate-950">Select an area to inspect</h2>
          </div>
          <select
            value={selectedArea}
            onChange={(e) => setSelectedArea(e.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-900 shadow-sm outline-none transition focus:border-violet-400 focus:ring-4 focus:ring-violet-500/10 lg:w-80"
          >
            {areas.map(area => (
              <option key={area.id} value={area.id}>{area.name}</option>
            ))}
          </select>
        </div>
      </Surface>

      {loading && (
        <div className="glass-panel rounded-[1.75rem] py-16 text-center">
          <div className="mx-auto h-14 w-14 animate-spin rounded-full border-4 border-violet-200 border-t-violet-500" />
          <p className="mt-4 text-sm font-semibold text-slate-600">Loading area analysis...</p>
        </div>
      )}
      
      {error && (
        <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 px-5 py-4 text-rose-800 shadow-sm">
          <p className="font-bold">Error loading analysis</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}
      
      {!loading && !error && analysis ? (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <AnalysisCard label="Average Free Land" value={`${freeLandPercentage}%`} icon="📍" />
            <AnalysisCard label="Average Green Area" value={`${greenPercentage}%`} icon="🌱" />
            <AnalysisCard label="Avg Trees per Image" value={estimatedTrees} icon="🌳" />
            <AnalysisCard label="Plantation Area" value={`${(plantationArea / 1000).toFixed(0)}K m²`} icon="📊" />
          </div>

          <Surface>
            <SectionHeading
              title="Analysis summary"
              description="The most useful numbers are surfaced first, with enough context to understand the city at a glance."
            />
            <div className="grid gap-8 md:grid-cols-2">
              <div>
                <p className="text-sm font-bold uppercase tracking-[0.22em] text-slate-500">Images processed</p>
                <p className="mt-3 text-5xl font-extrabold tracking-tight text-violet-600">{imageCount}</p>
                <p className="mt-3 text-slate-600">satellite images analyzed for this area</p>
              </div>
              <div>
                <p className="text-sm font-bold uppercase tracking-[0.22em] text-slate-500">Insights</p>
                <ul className="mt-3 space-y-3 text-slate-700">
                  <li>✓ Average {freeLandPercentage.toFixed(1)}% free land available for plantation</li>
                  <li>✓ Estimated {estimatedTrees} trees per analyzed area</li>
                  <li>✓ {plantationArea.toLocaleString()} m² suitable for planting</li>
                  <li>✓ Current green cover at {greenPercentage.toFixed(1)}% of total area</li>
                </ul>
              </div>
            </div>
          </Surface>

          {analysis.images && analysis.images.length > 0 && (
            <Surface className="mt-8">
              <SectionHeading title="Analyzed images" description="The generated files are shown here so the page feels like it has real satellite evidence, not just text metrics." />
              <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
                {analysis.images.map((img, idx) => {
                  const imageUrl = `http://localhost:5000/static/images/${selectedArea}_${img.id}.png`
                  const segmentedUrl = `http://localhost:5000/static/images/${selectedArea}_${img.id}_segmented.png`

                  return (
                    <div key={idx} className="overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-sm">
                      <div className="relative h-44 bg-slate-100">
                        <img
                          src={imageUrl}
                          onError={(event) => {
                            event.currentTarget.onerror = null
                            event.currentTarget.src = segmentedUrl
                          }}
                          alt={`Satellite analysis ${img.id}`}
                          className="h-full w-full object-cover"
                        />
                        <div className="absolute left-4 top-4 rounded-full bg-white/85 px-3 py-1 text-xs font-bold text-slate-700 shadow-sm backdrop-blur">
                          Image {img.id}
                        </div>
                      </div>
                      <div className="p-4">
                        <p className="text-sm text-slate-600"><strong className="text-slate-950">Free Land:</strong> {img.freeLandPercentage}%</p>
                        <p className="text-sm text-slate-600"><strong className="text-slate-950">Green Area:</strong> {img.greenPercentage}%</p>
                        <p className="text-sm text-slate-600"><strong className="text-slate-950">Est. Trees:</strong> {img.estimatedTrees}</p>
                        <p className="text-sm text-slate-600"><strong className="text-slate-950">Plantation Area:</strong> {(img.plantationArea / 1000).toFixed(0)}K m²</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </Surface>
          )}

          <div className="mt-8 rounded-[1.5rem] border border-violet-200 bg-gradient-to-br from-violet-50 to-white p-6 shadow-sm">
            <h3 className="font-extrabold text-violet-950 mb-3">📋 Recommendations</h3>
            <ul className="space-y-2 text-violet-900">
              <li>• Focus plantation efforts on free land areas (highest concentration)</li>
              <li>• Use tree species recommended for the current AQI level</li>
              <li>• Monitor green cover growth quarterly</li>
              <li>• Prioritize high-impact tree species for fast pollution reduction</li>
            </ul>
          </div>
        </>
      ) : (
        <EmptyState title="No analysis data available" description="Pick another city or wait a moment for the area analysis request to finish." />
      )}
    </div>
  )
}

function AnalysisCard({ label, value, icon }) {
  return (
    <div className="glass-panel rounded-[1.5rem] p-6">
      <div className="text-3xl">{icon}</div>
      <p className="mt-3 text-sm font-semibold text-slate-500">{label}</p>
      <p className="mt-1 text-3xl font-extrabold tracking-tight text-violet-700">{value}</p>
    </div>
  )
}
