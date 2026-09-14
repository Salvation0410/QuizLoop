import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import QuizPage from './quiz'
import ReportPage from './report'

vi.mock('@tarojs/components', async () => {
  const React = await import('react')
  const Element = ({ children, ...props }: { children?: ReactNode }) => React.createElement('div', props, children)
  return { Button: Element, Text: Element, View: Element }
})

vi.mock('@tarojs/taro', () => ({
  default: { redirectTo: vi.fn() },
  useLoad: (callback: () => void) => callback()
}))

vi.mock('@/store/quiz', () => ({
  useQuizStore: (selector: (state: Record<string, unknown>) => unknown) => selector({
    quiz: undefined,
    attempt: undefined,
    report: undefined,
    setAttempt: vi.fn(),
    setReport: vi.fn()
  })
}))

describe('页面空态', () => {
  it('闯关空态仍保留主页面顶部标签和底部导航', () => {
    render(<QuizPage />)
    expect(screen.getAllByText('闯关')).toHaveLength(2)
    expect(screen.getAllByText('学习库')).toHaveLength(2)
    expect(screen.getByText('暂无进行中的关卡')).toBeInTheDocument()
  })

  it('没有关卡时报告页显示稳定空态', () => {
    render(<ReportPage />)
    expect(screen.getByText('还没有可复盘的关卡')).toBeInTheDocument()
    expect(screen.queryByText('AI 正在整理你的学习收获…')).not.toBeInTheDocument()
  })
})
