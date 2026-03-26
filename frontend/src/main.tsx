import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import AnalysisPage from './pages/AnalysisPage'
import ProjectsPage from './pages/ProjectsPage'
import ComparePage from './pages/ComparePage'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/compare/:projectId" element={<ComparePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
