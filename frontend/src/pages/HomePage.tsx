import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeV2 } from '../api'

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

      if (result.error) {
        setError('Analysis failed. The API could not parse the response — try again.')
        return
      }
      if (!result.story_chunks?.length) {
        setError('Analysis failed. The API returned no results — check your API credits.')
        return
      }

      localStorage.setItem('lastAnalysis', JSON.stringify(result))
      navigate('/analysis', { state: { result } })
    } catch (err: unknown) {
      clearInterval(timer)
      let msg = 'Analysis failed'
      if (err instanceof Error) {
        msg = err.message
      }
      if (typeof err === 'object' && err !== null && 'response' in err) {
        const status = (err as { response?: { status?: number } }).response?.status
        if (status && status >= 500) {
          msg = 'Analysis failed. Check your API credits.'
        }
      }
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
