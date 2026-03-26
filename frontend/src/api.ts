import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

export interface AnalyzeV2Request {
  transcript: string
  video_length_target: number
  weight_retention: number
}

export interface StoryChunk {
  chunk_id: number
  topic: string
  estimated_minutes: number
  recommendation: 'KEEP' | 'CUT' | 'SHORTEN'
  confidence: 'high' | 'medium' | 'low'
  reasoning: string
  similar_past: {
    project: string
    similarity: number
    retention: number
    survived: boolean
    views: number
  }[]
  editing_note: string
}

export interface ChapterOption {
  option: string
  structure: {
    chapter: number
    title: string
    chunks_included: number[]
    estimated_minutes: number
  }[]
  reasoning: string
}

export interface AnalysisResult {
  narrative_type: { type: string; reasoning: string }
  editorial_perspective: string
  story_chunks: StoryChunk[]
  chapter_options: ChapterOption[]
  target_compression: number
  estimated_final_length_minutes: number
  warnings: string[]
  opportunities: string[]
  killer_quote: string
  cold_open: { quote: string; why_it_works: string }
  thumbnail_suggestions: string[]
  _raw_chunks: { chunk_id: number; topic: string; summary: string; text: string; estimated_minutes: number; emotional_tone: string }[]
  error?: boolean
  raw?: string
}

export interface Project {
  project_id: string
  title: string
  character_count: number
}

export interface CompareResult {
  project_id: string
  title: string
  compression_ratio: number
  original_chunks: number
  edited_chunks: number
  performance: { views: number; likes: number; retention_ratio: number | null }
  chunk_analysis: {
    original_chunk_id: number
    topic: string
    summary?: string
    original_minutes: number
    survived: boolean
    edited_minutes?: number
    compression?: number
    note: string
  }[]
  patterns: {
    topics_kept: string[]
    topics_cut: string[]
    avg_compression_for_kept: number | null
    insight: string
  }
}

export async function analyzeV2(data: AnalyzeV2Request): Promise<AnalysisResult> {
  const resp = await api.post('/analyze-v2', data)
  return resp.data
}

export async function getProjects(): Promise<Project[]> {
  const resp = await api.get('/projects')
  return resp.data.projects
}

export async function getProject(id: string) {
  const resp = await api.get(`/projects/${id}`)
  return resp.data
}

export async function compareProject(id: string): Promise<CompareResult> {
  const resp = await api.post(`/compare/${id}`)
  return resp.data
}

export async function seedDatabase() {
  const resp = await api.post('/seed')
  return resp.data
}
