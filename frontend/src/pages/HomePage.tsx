import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeV2 } from '../api'
import type { AnalysisResult } from '../api'

const STEPS = [
  'Chunking transcript into story beats...',
  'Finding similar past projects...',
  'Analyzing performance data...',
  'Generating editorial recommendations...',
]

export default function HomePage() {
  const [transcript, setTranscript] = useState('')
  const [videoLength, setVideoLength] = useState(15)
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  async function handleAnalyze() {
    if (!transcript.trim()) return
    setLoading(true)
    setError(null)
    setStep(0)

    const timer = setInterval(() => {
      setStep((s) => Math.min(s + 1, STEPS.length - 1))
    }, 5000)

    try {
      const result = await analyzeV2({
        transcript,
        video_length_target: videoLength,
        weight_retention: 0.4,
      })
      clearInterval(timer)

      // Normalize: Claude may return chunks under different keys
      if (!result.story_chunks?.length) {
        const alt = (result as Record<string, unknown>).chunks
          ?? (result as Record<string, unknown>).analysis
          ?? (result as Record<string, unknown>).story_beats
        if (Array.isArray(alt) && alt.length > 0) {
          result.story_chunks = alt as AnalysisResult['story_chunks']
          console.warn('story_chunks missing — mapped from alternative key:', alt)
        }
      }

      // Allow partial success: if story_chunks exist, navigate even if error flag is set
      if (result.error && !result.story_chunks?.length) {
        setError('분석 실패 — Claude 응답을 분석 결과로 변환하지 못했습니다. 잠시 후 다시 시도해주세요.')
        console.error('Analysis error (no usable chunks):', result)
        return
      }
      if (!result.story_chunks?.length) {
        setError('분석 실패 — story_chunks가 비어있습니다. API 크레딧을 확인해주세요.')
        console.error('Empty story_chunks:', result)
        return
      }

      console.log('API response (navigating):', result)
      localStorage.setItem('lastAnalysis', JSON.stringify(result))
      navigate('/analysis', { state: { result } })
    } catch (err: unknown) {
      clearInterval(timer)
      let msg = '분석 실패 — 잠시 후 다시 시도해주세요.'
      const response = (err as { response?: { status?: number; data?: { detail?: string } } }).response
      const status = response?.status
      const detail = response?.data?.detail
      if (status === 502 && typeof detail === 'string') {
        msg = `분석 실패 — ${detail}`
      } else if (status === 429) {
        msg = '분석 실패 — API 요청 한도에 도달했습니다. 잠시 후 다시 시도해주세요.'
      } else if (status && status >= 500) {
        msg = '분석 실패 — 서버 오류입니다. API 크레딧과 백엔드 로그를 확인해주세요.'
      } else if (err instanceof Error && err.message) {
        msg = `분석 실패 — ${err.message}`
      }
      console.error('Analysis request failed:', err)
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold text-white mb-1">Story Structure Analysis</h1>
      <p className="text-gray-400 mb-6 text-sm">
        Paste an interview transcript to get AI-powered editorial recommendations based on EO's storytelling guide and past video performance.
      </p>

      <textarea
        className="w-full h-64 bg-gray-900 border border-gray-700 rounded-lg p-4 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-500 focus:outline-none resize-none"
        placeholder="Paste your interview transcript here..."
        value={transcript}
        onChange={(e) => setTranscript(e.target.value)}
        disabled={loading}
      />

      <div className="flex items-center gap-4 mt-4">
        <label className="text-sm text-gray-400">
          Target length: {videoLength} min
        </label>
        <input
          type="range"
          min={5}
          max={30}
          value={videoLength}
          onChange={(e) => setVideoLength(Number(e.target.value))}
          className="flex-1 accent-blue-500"
          disabled={loading}
        />
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading || !transcript.trim()}
        className="mt-4 w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-colors"
      >
        {loading ? 'Analyzing...' : 'Analyze Transcript'}
      </button>

      {loading && (
        <div className="mt-4 space-y-2">
          {STEPS.map((s, i) => (
            <div
              key={i}
              className={`text-sm flex items-center gap-2 ${
                i <= step ? 'text-blue-400' : 'text-gray-600'
              }`}
            >
              {i < step ? '✓' : i === step ? '⏳' : '○'} {s}
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-900/30 border border-red-800 rounded text-sm text-red-300">
          {error}
        </div>
      )}
    </div>
  )
}
