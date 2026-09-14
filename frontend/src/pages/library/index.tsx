import { View } from '@tarojs/components'
import { useDidShow } from '@tarojs/taro'
import { useState } from 'react'
import { AppHeader, BottomNav, PageTabs } from '@/components/Navigation'
import { learningApi } from '@/api/learning'
import type { HistoryItem, Stats } from '@/types/api'
import './index.scss'

const zero: Stats = { completed_questions: 0, average_accuracy: 0, total_xp: 0, total_coins: 0, streak_days: 0, completed_quizzes: 0 }
export default function LibraryPage () {
  const [history, setHistory] = useState<HistoryItem[]>([]); const [stats, setStats] = useState(zero)
  useDidShow(() => { Promise.all([learningApi.history(), learningApi.stats()]).then(([h, s]) => { setHistory(h); setStats(s) }).catch(() => {}) })
  return <View className='screen'><AppHeader title='学习库' hint='知识都在这里' coins={stats.total_coins} /><PageTabs active='library' /><View className='title'>学习库</View><View className='subtitle'>错题重温、掌握度分析，学过的都不会丢。</View><View className='panel'><View className='panel-title'>历史关卡</View>{history.map(item => <View className='history-row' key={item.quiz_id}><View className='round'>↺</View><View><View className='row-title'>{item.title}</View><View className='row-meta'>{item.question_count} 道题 · {item.status === 'completed' ? '已完成' : '未完成'}</View></View><View className='badge'>{item.status === 'completed' ? '完成' : '继续'}</View></View>)}{history.length === 0 && <View className='empty'>还没有学习记录</View>}</View><View className='panel'><View className='panel-title'>本周掌握度</View><View className='stats'><View><TextValue value={`${stats.average_accuracy}%`} label='平均正确率' /></View><View><TextValue value={`${stats.completed_questions}`} label='累计答题' /></View><View><TextValue value={`${stats.total_xp}`} label='累计 XP' /></View><View><TextValue value={`${stats.streak_days}`} label='连续天数' /></View></View></View><View className='panel pk'><View className='panel-title'>好友 PK</View><View className='vs'>😎　VS　🤓</View><View className='badge'>暂未开放</View></View><BottomNav active='library' /></View>
}
function TextValue ({ value, label }: { value: string; label: string }) { return <View className='stat'><View>{value}</View>{label}</View> }
