import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { compareProject, type CompareResult } from '../api'

export default function ComparePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [result, setResult] = useState<CompareResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return
    setLoading(true)
    compareProject(projectId)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [projectId])

  if (loading) {
    return (
      <div className="text-gray-400">
        <p>Analyzing original vs edited transcripts...</p>
        <p className="text-sm text-gray-600 mt-1">This may take a few minutes (chunking both transcripts with AI).</p>
      </div>
    )
  }
  if (error) return <p className="text-red-400">{error}</p>
  if (!result) return <p className="text-gray-400">No data</p>

  const kept = result.chunk_analysis.filter((c) => c.survived)
  const cut = result.chunk_analysis.filter((c) => !c.survived)

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">{result.title}</h1>
          <p className="text-sm text-gray-400 mt-1">Original vs Edited Comparison</p>
        </div>
        <Link to="/projects" className="text-sm text-gray-500 hover:text-gray-300">
          Back to Projects
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {[
          { label: 'Compression', value: `${((result.compression_ratio || 0) * 100).toFixed(0)}%` },
          { label: 'Original Chunks', value: result.original_chunks },
          { label: 'Edited Chunks', value: result.edited_chunks },
          { label: 'Views', value: result.performance.views.toLocaleString() },
          { label: 'Retention', value: result.performance.retention_ratio ? `${(result.performance.retention_ratio * 100).toFixed(0)}%` : 'N/A' },
        ].map((s) => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-center">
            <p className="text-xs text-gray-500">{s.label}</p>
            <p className="text-lg text-white font-medium">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Kept */}
        <div>
          <h2 className="text-sm font-medium text-green-400 mb-2 uppercase">
            Kept in Edit ({kept.length})
          </h2>
          <div className="space-y-2">
            {kept.map((c) => (
              <div key={c.original_chunk_id} className="border border-green-500/20 bg-green-500/5 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-300">#{c.original_chunk_id} {c.topic}</span>
                  <span className="text-xs text-gray-500">
                    {c.original_minutes}m → {c.edited_minutes ?? '?'}m
                  </span>
                </div>
                {c.summary && <p className="text-xs text-gray-400 mb-1">{c.summary}</p>}
                <p className="text-xs text-gray-500">{c.note}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Cut */}
        <div>
          <h2 className="text-sm font-medium text-red-400 mb-2 uppercase">
            Cut from Edit ({cut.length})
          </h2>
          <div className="space-y-2">
            {cut.map((c) => (
              <div key={c.original_chunk_id} className="border border-red-500/20 bg-red-500/5 rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-300">#{c.original_chunk_id} {c.topic}</span>
                  <span className="text-xs text-gray-500">{c.original_minutes}m</span>
                </div>
                {c.summary && <p className="text-xs text-gray-400 mb-1">{c.summary}</p>}
                <p className="text-xs text-gray-500">{c.note}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Patterns */}
      <div className="border border-gray-800 rounded-lg p-4 space-y-3">
        <h2 className="text-sm font-medium text-white uppercase">Patterns</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-500 text-xs mb-1">Topics Kept</p>
            <div className="flex flex-wrap gap-1">
              {result.patterns.topics_kept.map((t) => (
                <span key={t} className="px-2 py-0.5 bg-green-500/10 text-green-400 rounded text-xs">{t}</span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Topics Cut</p>
            <div className="flex flex-wrap gap-1">
              {result.patterns.topics_cut.map((t) => (
                <span key={t} className="px-2 py-0.5 bg-red-500/10 text-red-400 rounded text-xs">{t}</span>
              ))}
            </div>
          </div>
        </div>
        {result.patterns.avg_compression_for_kept && (
          <p className="text-xs text-gray-500">
            Avg compression for kept chunks: {result.patterns.avg_compression_for_kept}x
          </p>
        )}
        <p className="text-sm text-gray-300">{result.patterns.insight}</p>
      </div>
    </div>
  )
}
