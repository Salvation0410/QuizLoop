import { View } from '@tarojs/components'
import { useDidShow } from '@tarojs/taro'
import { useState } from 'react'
import { AppHeader, BottomNav, PageTabs } from '@/components/Navigation'
import { learningApi } from '@/api/learning'
import type { Stats } from '@/types/api'
import './index.scss'

const zero: Stats = { completed_questions: 0, average_accuracy: 0, total_xp: 0, total_coins: 0, streak_days: 0, completed_quizzes: 0 }
export default function ProfilePage () {
  const [stats, setStats] = useState(zero); useDidShow(() => { learningApi.stats().then(setStats).catch(() => {}) })
  return <View className='screen'><AppHeader title='我的学习空间' hint='今天也有进步' coins={stats.total_coins} /><PageTabs active='profile' /><View className='profile-card'><View className='profile-avatar'>☻</View><View><View className='name'>小皮同学</View><View className='subtitle'>完成 {stats.completed_quizzes} 个关卡 · Lv.{Math.floor(stats.total_xp / 300) + 1} 知识探险家</View></View></View><View className='panel'><View className='panel-title'>我的学习数据</View><View className='profile-stats'><View><View>{stats.completed_questions}</View>完成题目</View><View><View>{stats.average_accuracy}%</View>平均正确率</View><View><View>{stats.total_xp}</View>累计 XP</View></View></View><View className='panel'><View className='panel-title'>连续学习</View><View className='streak'>🔥 <View><View className='bold'>{stats.streak_days} 天连续学习</View><View className='subtitle'>每完成一次闯关，学习足迹就会留下</View></View></View></View><View className='panel'><View className='panel-title'>我的勋章</View><View className='medals'><View className={stats.completed_quizzes ? '' : 'locked'}><View>★</View>首关完成</View><View className={stats.average_accuracy >= 80 ? '' : 'locked'}><View>⚡</View>高分达人</View><View className={stats.streak_days >= 3 ? '' : 'locked'}><View>✦</View>坚持学习</View></View></View><BottomNav active='profile' /></View>
}
