import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import { PageShell } from './components/UiKit'
import Home from './pages/Home'
import About from './pages/About'
import AqiTrees from './pages/AqiTrees'
import AreaAnalysis from './pages/AreaAnalysis'
import Forecasting from './pages/Forecasting'
import ModelEvaluation from './pages/ModelEvaluation'

function App() {
  const [areas] = useState([
    { id: 'madurai', name: 'Madurai' },
    { id: 'chennai', name: 'Chennai' },
    { id: 'coimbatore', name: 'Coimbatore' },
    { id: 'dindigul', name: 'Dindigul' },
    { id: 'trichy', name: 'Trichy' },
  ])

  return (
    <Router>
      <PageShell>
        <Navigation />
        <main className="mx-auto w-full max-w-[1500px] px-4 pb-12 pt-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Home areas={areas} />} />
            <Route path="/about" element={<About />} />
            <Route path="/aqi-trees" element={<AqiTrees areas={areas} />} />
            <Route path="/area-analysis" element={<AreaAnalysis areas={areas} />} />
            <Route path="/forecasting" element={<Forecasting areas={areas} />} />
            <Route path="/model-evaluation" element={<ModelEvaluation />} />
          </Routes>
        </main>
      </PageShell>
    </Router>
  )
}

export default App
