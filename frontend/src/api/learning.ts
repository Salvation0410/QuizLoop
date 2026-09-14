import type { AnswerRecord, Attempt, HistoryItem, Quiz, Report, Stats } from '@/types/api'
import { request } from './client'

const key = (prefix: string) => `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

export const learningApi = {
  ensureSession: (anonymous_id: string) => request<{ session_id: string }>('/sessions/anonymous', 'POST', { anonymous_id }),
  generateQuiz: (user_input: string, question_count = 5, difficulty = 'mixed') => request<Quiz>('/quizzes/generate', 'POST', { user_input, question_count, difficulty }, key('quiz')),
  getQuiz: (quizId: string) => request<Quiz>(`/quizzes/${quizId}`),
  submitAttempt: (quizId: string, answer_records: AnswerRecord[]) => request<Attempt>(`/quizzes/${quizId}/attempts`, 'POST', { answer_records }, key(`attempt_${quizId}`)),
  generateReport: (quizId: string) => request<Report>(`/quizzes/${quizId}/report`, 'POST', undefined, key(`report_${quizId}`)),
  getReport: (reportId: string) => request<Report>(`/reports/${reportId}`),
  stats: () => request<Stats>('/history/stats'),
  history: () => request<HistoryItem[]>('/history/quizzes')
}
