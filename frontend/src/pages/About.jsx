import React from 'react'
import { PageHero, SectionHeading, Surface } from '../components/UiKit'

export default function About() {
  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="About the project"
        title="GreenMadurai turns pollution data into practical planting decisions."
        description="The project combines live AQI, model-driven tree recommendations, and satellite analysis into one dashboard for better planning."
        accent="emerald"
        stats={[
          { label: 'Areas', value: '5' },
          { label: 'Frontend', value: 'React + Tailwind' },
          { label: 'Backend', value: 'Flask + ML' },
          { label: 'Forecast window', value: '7 days' },
        ]}
      />

      <Surface className="max-w-5xl">
        <SectionHeading title="Mission" description="Keep the message concise, confident, and aligned with the rest of the interface." />
        <p className="text-base leading-8 text-slate-600">
          GreenMadurai is an AI-powered system designed to analyze air pollution patterns and recommend suitable trees for plantation across Madurai areas. The goal is to help communities act on environmental data instead of reading it passively.
        </p>

        <div className="mt-10 grid gap-6 md:grid-cols-2">
          <div className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-6">
            <h2 className="text-xl font-extrabold text-emerald-950 mb-4">Key features</h2>
            <ul className="space-y-4">
              <li className="flex items-start gap-3 text-slate-700"><span className="text-emerald-600 text-xl">✓</span><span><strong>Real-time AQI monitoring:</strong> Track air quality across 5 key areas with live data updates.</span></li>
              <li className="flex items-start gap-3 text-slate-700"><span className="text-emerald-600 text-xl">✓</span><span><strong>Smart tree recommendations:</strong> Pollution-absorbing species are ranked by AQI profile and area context.</span></li>
              <li className="flex items-start gap-3 text-slate-700"><span className="text-emerald-600 text-xl">✓</span><span><strong>Satellite analysis:</strong> Identify free land for plantation from image-derived data.</span></li>
              <li className="flex items-start gap-3 text-slate-700"><span className="text-emerald-600 text-xl">✓</span><span><strong>7-day forecasting:</strong> Predict AQI trends with a fast statistical model.</span></li>
            </ul>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-extrabold text-slate-950 mb-4">Technology stack</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-[1.25rem] bg-slate-50 p-4">
                <h3 className="font-extrabold text-slate-950 mb-2">Backend</h3>
                <ul className="text-sm text-slate-600 space-y-1">
                  <li>• Python & Flask</li>
                  <li>• Scikit-learn & Pandas</li>
                  <li>• Statsmodels for forecasting</li>
                  <li>• OpenCV for image analysis</li>
                </ul>
              </div>
              <div className="rounded-[1.25rem] bg-slate-50 p-4">
                <h3 className="font-extrabold text-slate-950 mb-2">Frontend</h3>
                <ul className="text-sm text-slate-600 space-y-1">
                  <li>• React 18.2</li>
                  <li>• Tailwind CSS</li>
                  <li>• React Router</li>
                  <li>• Axios for API calls</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-6 md:grid-cols-2">
            <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-extrabold text-slate-950 mb-4">Data sources</h2>
              <ul className="space-y-2 text-slate-700">
                <li>• OpenWeatherMap Air Pollution API for current and historical AQI data</li>
                <li>• Satellite imagery for land analysis</li>
                <li>• Tree species suitability datasets for different pollution levels</li>
                <li>• User feedback for continuous model improvement</li>
              </ul>
            </div>

            <div className="rounded-[1.5rem] border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-6 shadow-sm">
              <h2 className="text-xl font-extrabold text-emerald-950 mb-4">Get started</h2>
              <p className="text-slate-700 leading-8">
                Visit the AQI & Trees page to monitor real-time air quality and discover the best trees to plant in your area. Or explore Area Analysis to find plantation opportunities in your region.
              </p>
            </div>
          </div>
        </div>
      </Surface>
    </div>
  )
}
