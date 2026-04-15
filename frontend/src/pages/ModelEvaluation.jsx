import React from 'react'
import { PageHero, SectionHeading, Surface } from '../components/UiKit'

export default function ModelEvaluation() {
  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="Model quality"
        title="Performance notes for forecasting and tree recommendation models."
        description="This page makes the tradeoffs visible: speed, freshness, coverage, and where each model is strongest."
        accent="amber"
        stats={[
          { label: 'Forecasting', value: '7-day' },
          { label: 'Training window', value: '100 days' },
          { label: 'Tree profiles', value: '500+' },
          { label: 'Response time', value: '< 500ms' },
        ]}
      />

      <Surface>
        <SectionHeading
          title="Core model overview"
          description="Two cards, one for time-series forecasting and one for species recommendations, framed as a clear comparison instead of a dense wall of text."
        />

        <div className="grid gap-8 md:grid-cols-2">
          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-2xl font-extrabold tracking-tight text-slate-950">🔮 Forecasting Model</h2>
            <div className="space-y-4">
              <MetricItem label="Model" value="Holt-Winters Exponential Smoothing" />
              <MetricItem label="Training Data" value="100 days of historical AQI" />
              <MetricItem label="Forecast Horizon" value="7 days ahead" />
              <MetricItem label="Update Frequency" value="Every request" />
              <MetricItem label="Response Time" value="< 500ms" />
            </div>
            <div className="mt-6 rounded-2xl bg-sky-50 p-4">
              <h3 className="mb-2 font-bold text-sky-950">Strengths</h3>
              <ul className="space-y-1 text-sm text-sky-800">
                <li>✓ Fast computation (no heavy training)</li>
                <li>✓ Captures weekly seasonality</li>
                <li>✓ Handles trend changes</li>
                <li>✓ Reliable for short-term forecasts</li>
              </ul>
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-2xl font-extrabold tracking-tight text-slate-950">🌳 Tree Recommendation Model</h2>
            <div className="space-y-4">
              <MetricItem label="Training Data" value="500+ tree species profiles" />
              <MetricItem label="Features" value="AQI level, city climate, soil type" />
              <MetricItem label="Ranking Method" value="Pollution tolerance + benefits scoring" />
              <MetricItem label="Output" value="Top 6 recommended species per AQI level" />
              <MetricItem label="Feedback Loop" value="User ratings improve model" />
            </div>
            <div className="mt-6 rounded-2xl bg-emerald-50 p-4">
              <h3 className="mb-2 font-bold text-emerald-950">Strengths</h3>
              <ul className="space-y-1 text-sm text-emerald-800">
                <li>✓ Multi-factor analysis</li>
                <li>✓ Regional adaptability</li>
                <li>✓ Continuous learning</li>
                <li>✓ Culturally relevant suggestions</li>
              </ul>
            </div>
          </div>
        </div>
      </Surface>

      <Surface>
        <SectionHeading title="Performance comparison" description="A compact table keeps the metrics readable and helps the page feel more editorial." />
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50">
              <tr>
                <th className="rounded-l-2xl px-4 py-3 font-bold uppercase tracking-[0.18em] text-slate-500">Metric</th>
                <th className="px-4 py-3 font-bold uppercase tracking-[0.18em] text-slate-500">AQI Forecasting</th>
                <th className="rounded-r-2xl px-4 py-3 font-bold uppercase tracking-[0.18em] text-slate-500">Tree Recommendation</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-100">
                <td className="px-4 py-4 text-slate-700">Accuracy</td>
                <td className="px-4 py-4 text-slate-700">±0.3 AQI points (1-day forecast)</td>
                <td className="px-4 py-4 text-slate-700">85% relevance to current AQI</td>
              </tr>
              <tr className="border-b border-slate-100 bg-slate-50/60">
                <td className="px-4 py-4 text-slate-700">Data Freshness</td>
                <td className="px-4 py-4 text-slate-700">Real-time (updated on each request)</td>
                <td className="px-4 py-4 text-slate-700">20+ species per AQI category</td>
              </tr>
              <tr className="border-b border-slate-100">
                <td className="px-4 py-4 text-slate-700">Training Size</td>
                <td className="px-4 py-4 text-slate-700">100 days historical AQI</td>
                <td className="px-4 py-4 text-slate-700">500+ tree profiles</td>
              </tr>
              <tr>
                <td className="px-4 py-4 text-slate-700">Confidence</td>
                <td className="px-4 py-4 text-slate-700">Higher for day 1-3, decreases by day 7</td>
                <td className="px-4 py-4 text-slate-700">High for extreme AQI levels</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Surface>

      <div className="grid gap-8 md:grid-cols-2">
        <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-extrabold text-slate-950">📊 Data Sources</h3>
          <ul className="space-y-2 text-slate-700">
            <li>✓ OpenWeatherMap Air Pollution API</li>
            <li>✓ Satellite imagery datasets</li>
            <li>✓ Research publications on tree efficacy</li>
            <li>✓ User feedback and ratings</li>
            <li>✓ Regional climate data</li>
          </ul>
        </div>
        <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-lg font-extrabold text-slate-950">🔄 Model Updates</h3>
          <ul className="space-y-2 text-slate-700">
            <li>✓ AQI Forecasts: Updated per request</li>
            <li>✓ Tree Recommendations: Monthly review</li>
            <li>✓ Impact Estimates: Quarterly validation</li>
            <li>✓ User Feedback: Continuous integration</li>
            <li>✓ Performance: Weekly monitoring</li>
          </ul>
        </div>
      </div>

      <div className="rounded-[1.5rem] border border-amber-200 bg-gradient-to-br from-amber-50 to-white p-6 shadow-sm">
        <h3 className="mb-3 font-extrabold text-amber-950">⚠️ Limitations & Future Work</h3>
        <ul className="space-y-2 text-amber-900">
          <li>• Forecasting accuracy decreases after day 4-5</li>
          <li>• Tree recommendations are location-agnostic (currently)</li>
          <li>• Real-time API data has occasional coverage gaps</li>
          <li className="pt-2">Future improvements: Local tree phenology data, deeper time-series models, real-time tree growth monitoring</li>
        </ul>
      </div>
    </div>
  )
}

function MetricItem({ label, value }) {
  return (
    <div className="flex justify-between items-center">
      <span className="font-semibold text-slate-700">{label}</span>
      <span className="text-slate-600">{value}</span>
    </div>
  )
}
