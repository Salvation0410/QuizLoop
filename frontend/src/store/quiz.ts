import Taro from '@tarojs/taro'
import { create } from 'zustand'
import type { Attempt, Quiz, Report } from '@/types/api'

interface QuizState {
  quiz?: Quiz; attempt?: Attempt; report?: Report
  setQuiz: (quiz: Quiz) => void; setAttempt: (attempt: Attempt) => void; setReport: (report: Report) => void
}

export const useQuizStore = create<QuizState>((set) => ({
  quiz: Taro.getStorageSync('quizeloop_active_quiz') || undefined,
  attempt: Taro.getStorageSync('quizeloop_attempt') || undefined,
  report: Taro.getStorageSync('quizeloop_report') || undefined,
  setQuiz: (quiz) => {
    Taro.setStorageSync('quizeloop_active_quiz', quiz)
    Taro.removeStorageSync('quizeloop_attempt')
    Taro.removeStorageSync('quizeloop_report')
    set({ quiz, attempt: undefined, report: undefined })
  },
  setAttempt: (attempt) => { Taro.setStorageSync('quizeloop_attempt', attempt); set({ attempt }) },
  setReport: (report) => { Taro.setStorageSync('quizeloop_report', report); set({ report }) }
}))
