import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProjects, getProject, type Project } from '../api'

interface ProjectDetail {
  project_id: string
  title: string
  transcript_original?: string
  transcript_edited?: string
  performance?: { views: number; likes: number; comments: number }
  retention_ratio?: number
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<ProjectDetail | null>(null)

  useEffect(() => {
    getProjects()
      .then(setProjects)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleSelect(id: string) {
    try {
      const detail = await getProject(id)
      setSelected(detail as ProjectDetail)
    } catch {
      setError('Failed to load project detail')
    }
  }

  if (loading) return <p className="text-gray-400">Loading projects...</p>
  if (error) return <p className="text-red-400">{error}</p>

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold text-white mb-4">Projects ({projects.length})</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 space-y-1 max-h-[80vh] overflow-auto">
          {projects.map((p) => (
            <button
              key={p.project_id}
              onClick={() => handleSelect(p.project_id)}
              className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                selected?.project_id === p.project_id
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200'
              }`}
            >
              <p className="truncate">{p.title}</p>
              <p className="text-xs text-gray-600">{p.character_count.toLocaleString()} chars</p>
            </button>
          ))}
        </div>

        <div className="lg:col-span-2">
          {selected ? (
            <div className="border border-gray-800 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-white">{selected.title}</h2>
                {selected.transcript_edited && (
                  <Link
                    to={`/compare/${selected.project_id}`}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded transition-colors"
                  >
                    Compare Original vs Edited
                  </Link>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-500">Project ID</p>
                  <p className="text-gray-300 font-mono text-xs">{selected.project_id}</p>
                </div>
                {selected.performance && (
                  <>
                    <div>
                      <p className="text-gray-500">Views</p>
                      <p className="text-gray-300">{selected.performance.views?.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Likes</p>
                      <p className="text-gray-300">{selected.performance.likes?.toLocaleString()}</p>
                    </div>
                  </>
                )}
                {selected.retention_ratio != null && (
                  <div>
                    <p className="text-gray-500">Retention</p>
                    <p className="text-gray-300">{(selected.retention_ratio * 100).toFixed(1)}%</p>
                  </div>
                )}
              </div>

              {selected.transcript_original && (
                <div>
                  <p className="text-gray-500 text-sm mb-1">Original Transcript (first 2000 chars)</p>
                  <pre className="bg-gray-900 border border-gray-800 rounded p-3 text-xs text-gray-400 whitespace-pre-wrap max-h-64 overflow-auto">
                    {selected.transcript_original.slice(0, 2000)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-600">
              Select a project to view details
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
