import { Button, Textarea, View } from '@tarojs/components'
import Taro, { useDidShow } from '@tarojs/taro'
import { useState } from 'react'
import { AppHeader, BottomNav, PageTabs } from '@/components/Navigation'
import { learningApi } from '@/api/learning'
import { useQuizStore } from '@/store/quiz'
import type { HistoryItem, Stats } from '@/types/api'
import './index.scss'

export default function Index () {
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [stats, setStats] = useState<Stats>({ completed_questions: 0, average_accuracy: 0, total_xp: 0, total_coins: 0, streak_days: 0, completed_quizzes: 0 })
  const setQuiz = useQuizStore(s => s.setQuiz)
  useDidShow(() => { Promise.all([learningApi.history(), learningApi.stats()]).then(([h, s]) => { setHistory(h); setStats(s) }).catch(() => {}) })
  const start = async () => {
    if (topic.trim().length < 2) { setError('先输入至少两个字的学习主题'); return }
    setLoading(true); setError('')
    try { const quiz = await learningApi.generateQuiz(topic.trim()); setQuiz(quiz); Taro.navigateTo({ url: '/pages/quiz/index' }) } catch (e) { setError(e instanceof Error ? e.message : '生成失败，请重试') } finally { setLoading(false) }
  }
  return <View className='screen'><AppHeader coins={stats.total_coins} /><PageTabs active='home' /><View className='hero'><View className='title'>今天想闯哪一关？</View><View className='avatar'>☻</View></View><View className='input-panel'><View className='label'>输入你想学的内容</View><Textarea className='topic-input' maxlength={10000} value={topic} onInput={e => setTopic(e.detail.value)} placeholder='例如：RAG 和传统搜索有什么区别？' /><Button className='primary start' loading={loading} disabled={loading} onClick={start}>{loading ? 'AI 正在整理知识点…' : '→ 开始生成题目'}</Button>{error && <View className='error'>{error}</View>}</View><View className='section-head'><View className='panel-title'>未完成关卡</View><View>共 {history.length} 个</View></View>{history.slice(0, 3).map(item => <View className='course' key={item.quiz_id} onClick={() => learningApi.getQuiz(item.quiz_id).then(q => { setQuiz(q); Taro.navigateTo({ url: '/pages/quiz/index' }) })}><View className='course-icon'>★</View><View><View className='course-title'>{item.title}</View><View className='course-meta'>{item.question_count} 道题 · {item.status === 'completed' ? '已完成' : '继续闯关'}</View></View><View className='badge'>{item.status === 'completed' ? '100%' : 'GO'}</View></View>)}{history.length === 0 && <View className='empty'>还没有关卡，输入一个主题开始吧</View>}<BottomNav active='home' /></View>
}
