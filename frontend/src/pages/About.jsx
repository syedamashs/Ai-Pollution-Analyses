import React from 'react'
import { PageHero, SectionHeading, Surface } from '../components/UiKit'

export default function About() {
  const capabilities = [
    {
      title: 'Live AQI intelligence',
      description: 'Track current pollutant load per area and keep planning aligned with real-time conditions.',
      accent: 'border-sky-200 bg-sky-50',
    },
    {
      title: 'Contextual tree ranking',
      description: 'Recommendations adapt to AQI, local profile features, and impact model signals.',
      accent: 'border-emerald-200 bg-emerald-50',
    },
    {
      title: 'Satellite-based land insights',
      description: 'Image segmentation estimates free land, green cover, and plantation potential.',
      accent: 'border-amber-200 bg-amber-50',
    },
    {
      title: '7-day forecasting',
      description: 'Holt-Winters predicts short-range AQI movement for better scheduling and interventions.',
      accent: 'border-violet-200 bg-violet-50',
    },
  ]

  const stack = [
    {
      group: 'Frontend',
      items: ['React', 'Tailwind CSS', 'React Router', 'Axios'],
    },
    {
      group: 'Backend',
      items: ['Flask', 'NumPy', 'OpenCV', 'Scikit-learn'],
    },
    {
      group: 'Forecasting',
      items: ['Statsmodels', 'Holt-Winters', 'History backfill', 'Trend summary'],
    },
  ]

  const pipeline = [
    'Collect live and historical AQI signals by area.',
    'Apply area-level microzone adjustments and AQI calculation.',
    'Run land segmentation to estimate plantation capacity.',
    'Rank tree species and surface action-ready recommendations.',
  ]

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
          { label: 'Forecast model', value: 'Holt-Winters' },
        ]}
      />

      <Surface>
        <SectionHeading title="Mission" description="A clean overview of what the platform does and how it helps." />
        <p className="text-base leading-8 text-slate-600">
          GreenMadurai is built to help teams move from environmental monitoring to execution. Instead of showing only charts,
          the platform combines AQI, land analysis, and recommendation models into a single decision surface for area-level
          plantation planning.
        </p>
      </Surface>

      <Surface>
        <SectionHeading
          title="Core Capabilities"
          description="Each module is designed to answer one planning question clearly."
        />
        <div className="grid gap-4 md:grid-cols-2">
          {capabilities.map((item) => (
            <div key={item.title} className={`rounded-[1.35rem] border p-5 ${item.accent}`}>
              <h3 className="text-lg font-extrabold tracking-tight text-slate-950">{item.title}</h3>
              <p className="mt-2 text-sm leading-7 text-slate-700">{item.description}</p>
            </div>
          ))}
        </div>
      </Surface>

      <div className="grid gap-6 xl:grid-cols-3">
        <Surface className="xl:col-span-2">
          <SectionHeading title="System Stack" description="Separated by frontend, backend, and forecasting layers." />
          <div className="grid gap-4 md:grid-cols-3">
            {stack.map((section) => (
              <div key={section.group} className="rounded-[1.25rem] border border-slate-200 bg-white p-4">
                <h3 className="text-base font-extrabold text-slate-950">{section.group}</h3>
                <ul className="mt-3 space-y-2 text-sm text-slate-600">
                  {section.items.map((item) => (
                    <li key={item} className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Surface>

        <Surface>
          <SectionHeading title="Data Pipeline" />
          <ol className="space-y-3 text-sm text-slate-700">
            {pipeline.map((step, index) => (
              <li key={step} className="flex gap-3">
                <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-extrabold text-emerald-700">
                  {index + 1}
                </span>
                <span className="leading-6">{step}</span>
              </li>
            ))}
          </ol>
        </Surface>
      </div>

      <Surface>
        <SectionHeading title="How To Use It" description="A practical flow for first-time users." />
        <div className="grid gap-4 md:grid-cols-3">
          <StepCard step="1" title="Check AQI & Trees" text="Start from current AQI and review recommended species." />
          <StepCard step="2" title="Inspect Area Analysis" text="Review free-land and green-cover outputs from imagery." />
          <StepCard step="3" title="Plan With Forecast" text="Use 7-day forecast trend before scheduling plantation drives." />
        </div>
      </Surface>
    </div>
  )
}

function StepCard({ step, title, text }) {
  return (
    <div className="rounded-[1.25rem] border border-slate-200 bg-white p-5 shadow-sm">
      <p className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-xs font-extrabold text-white">{step}</p>
      <h3 className="mt-3 text-base font-extrabold text-slate-950">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-slate-600">{text}</p>
    </div>
  )
}
