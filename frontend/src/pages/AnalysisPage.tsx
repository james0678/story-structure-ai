import { useState } from 'react'
import { useLocation, Navigate } from 'react-router-dom'
import type { AnalysisResult, StoryChunk } from '../api'

const REC_COLORS: Record<string, string> = {
  KEEP: 'border-green-500 bg-green-500/10',
  CUT: 'border-red-500 bg-red-500/10',
  SHORTEN: 'border-yellow-500 bg-yellow-500/10',
}

const REC_BADGES: Record<string, string> = {
  KEEP: 'bg-green-500/20 text-green-400',
  CUT: 'bg-red-500/20 text-red-400',
  SHORTEN: 'bg-yellow-500/20 text-yellow-400',
}

function ChunkCard({ chunk }: { chunk: StoryChunk }) {
  const [expanded, setExpanded] = useState(false)
  const rec = chunk.recommendation || 'KEEP'

  return (
    <div
      className={`border rounded-lg p-4 cursor-pointer transition-colors ${REC_COLORS[rec] || 'border-gray-700'}`}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-300">#{chunk.chunk_id}</span>
          <span className="text-sm text-gray-400">{chunk.topic}</span>
          <span className="text-xs text-gray-500">{chunk.estimated_minutes}m</span>
        </div>
        <span className={`text-xs font-medium px-2 py-0.5 rounded ${REC_BADGES[rec] || ''}`}>
          {rec} ({chunk.confidence})
        </span>
      </div>

      {expanded && (
        <div className="mt-3 space-y-3 text-sm">
          <p className="text-gray-300">{chunk.reasoning}</p>
          {chunk.editing_note && (
            <p className="text-gray-400 italic">{chunk.editing_note}</p>
          )}
          {chunk.similar_past?.length > 0 && (
            <div className="space-y-1">
              <p className="text-gray-500 text-xs font-medium uppercase">Similar Past Projects</p>
              {chunk.similar_past.map((s, i) => (
                <div key={i} className="flex items-center gap-3 text-xs text-gray-400">
                  <span className="text-gray-300">{s.project}</span>
                  <span>sim: {s.similarity}</span>
                  <span>ret: {s.retention}</span>
                  <span>{s.views?.toLocaleString()} views</span>
                  <span className={s.survived ? 'text-green-400' : 'text-red-400'}>
                    {s.survived ? 'KEPT' : 'CUT'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function AnalysisPage() {
  const location = useLocation()
  const result = (location.state?.result ?? (() => {
    try {
      const stored = localStorage.getItem('lastAnalysis')
      return stored ? JSON.parse(stored) : undefined
    } catch {
      return undefined
    }
  })()) as AnalysisResult | undefined

  if (!result) return <Navigate to="/" />

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-white mb-2">Analysis Results</h1>
        <div className="flex gap-4 text-sm text-gray-400">
          <span>Type: <span className="text-white">{result.narrative_type?.type}</span></span>
          <span>Est. final: <span className="text-white">{result.estimated_final_length_minutes}m</span></span>
          <span>Compression: <span className="text-white">{((result.target_compression || 0) * 100).toFixed(0)}%</span></span>
        </div>
        <p className="mt-2 text-gray-300">{result.editorial_perspective}</p>
        <p className="mt-1 text-sm text-gray-500">{result.narrative_type?.reasoning}</p>
      </div>

      {/* Cold Open & Killer Quote */}
      {(result.cold_open?.quote || result.killer_quote) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.cold_open?.quote && (
            <div className="border border-blue-500/30 bg-blue-500/5 rounded-lg p-4">
              <p className="text-xs text-blue-400 font-medium uppercase mb-2">Cold Open</p>
              <p className="text-gray-200 text-sm italic">"{result.cold_open.quote}"</p>
              <p className="text-gray-500 text-xs mt-2">{result.cold_open.why_it_works}</p>
            </div>
          )}
          {result.killer_quote && (
            <div className="border border-purple-500/30 bg-purple-500/5 rounded-lg p-4">
              <p className="text-xs text-purple-400 font-medium uppercase mb-2">Killer Quote</p>
              <p className="text-gray-200 text-sm italic">"{result.killer_quote}"</p>
            </div>
          )}
        </div>
      )}

      {/* Story Chunks */}
      <div>
        <h2 className="text-lg font-medium text-white mb-3">
          Story Chunks ({result.story_chunks?.length || 0})
        </h2>
        <p className="text-xs text-gray-500 mb-3">Click a chunk to expand details</p>
        <div className="space-y-2">
          {result.story_chunks?.map((c) => <ChunkCard key={c.chunk_id} chunk={c} />)}
        </div>
      </div>

      {/* Chapter Options */}
      {result.chapter_options?.length > 0 && (
        <div>
          <h2 className="text-lg font-medium text-white mb-3">Chapter Structure Options</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {result.chapter_options.map((opt) => (
              <div key={opt.option} className="border border-gray-700 rounded-lg p-4">
                <p className="text-sm font-medium text-white mb-2">Option {opt.option}</p>
                <div className="space-y-1 mb-3">
                  {opt.structure?.map((ch) => (
                    <div key={ch.chapter} className="flex items-center gap-2 text-sm">
                      <span className="text-gray-500 w-6">Ch{ch.chapter}</span>
                      <span className="text-gray-300 flex-1">{ch.title}</span>
                      <span className="text-gray-500 text-xs">{ch.estimated_minutes}m</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500">{opt.reasoning}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warnings & Opportunities */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {result.warnings?.length > 0 && (
          <div className="border border-red-500/20 bg-red-500/5 rounded-lg p-4">
            <p className="text-xs text-red-400 font-medium uppercase mb-2">Warnings</p>
            <ul className="space-y-2">
              {result.warnings.map((w, i) => (
                <li key={i} className="text-sm text-gray-300">{w}</li>
              ))}
            </ul>
          </div>
        )}
        {result.opportunities?.length > 0 && (
          <div className="border border-green-500/20 bg-green-500/5 rounded-lg p-4">
            <p className="text-xs text-green-400 font-medium uppercase mb-2">Opportunities</p>
            <ul className="space-y-2">
              {result.opportunities.map((o, i) => (
                <li key={i} className="text-sm text-gray-300">{o}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Thumbnails */}
      {result.thumbnail_suggestions?.length > 0 && (
        <div>
          <h2 className="text-lg font-medium text-white mb-3">Thumbnail Suggestions</h2>
          <div className="flex flex-wrap gap-2">
            {result.thumbnail_suggestions.map((t, i) => (
              <span key={i} className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm text-gray-300">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
