import { Button, View } from '@tarojs/components'
import Taro, { useLoad } from '@tarojs/taro'
import { useState } from 'react'
import { AppHeader } from '@/components/Navigation'
import { learningApi } from '@/api/learning'
import { useQuizStore } from '@/store/quiz'
import './index.scss'

export default function ReportPage () {
  const quiz = useQuizStore(s => s.quiz); const attempt = useQuizStore(s => s.attempt); const stored = useQuizStore(s => s.report); const setReport = useQuizStore(s => s.setReport)
  const [loading, setLoading] = useState(Boolean(quiz && !stored)); const [error, setError] = useState('')
  const load = async () => { if (!quiz) return; setLoading(true); setError(''); try { setReport(await learningApi.generateReport(quiz.quiz_id)) } catch (e) { setError(e instanceof Error ? e.message : '报告生成失败') } finally { setLoading(false) } }
  useLoad(() => { if (quiz && !stored) load() })
  const report = useQuizStore(s => s.report)
  if (!quiz) return <View className='screen'><AppHeader title='本次复盘' hint='关卡完成啦' /><View className='title'>知识闯关报告</View><View className='panel empty'>还没有可复盘的关卡</View><Button className='primary' onClick={() => Taro.redirectTo({ url: '/pages/index/index' })}>去首页开始闯关</Button></View>
  return <View className='screen'><AppHeader title='本次复盘' hint='关卡完成啦' coins={attempt?.coins_earned || 0} /><View className='title'>知识闯关报告</View>{loading && <View className='panel empty'>AI 正在整理你的学习收获…</View>}{error && <View className='error'>{error}<Button className='primary' onClick={load}>重新生成</Button></View>}{report && <><View className='score'><View className='score-number'>{report.accuracy}%</View><View>本次正确率</View><View className='reward'>+{attempt?.xp_earned || 0} XP · +{attempt?.coins_earned || 0} 金币</View></View><View className='panel'><View className='panel-title'>三句知识总结</View>{report.three_line_summary.map((line, i) => <View className='summary-line' key={line}><View>{i + 1}</View>{line}</View>)}</View><View className='two-cols'><View className='mini-panel good'><View className='panel-title'>掌握得不错</View>{report.mastered_points.length ? report.mastered_points.map(x => <View key={x}>✓ {x}</View>) : <View>继续积累中</View>}</View><View className='mini-panel weak'><View className='panel-title'>再巩固一下</View>{report.weak_points.length ? report.weak_points.map(x => <View key={x}>! {x}</View>) : <View>本关全部掌握</View>}</View></View><View className='panel quote'>“{report.share_quote}”</View><View className='panel'><View className='panel-title'>下一步建议</View>{report.advice.map(x => <View className='advice' key={x}>→ {x}</View>)}</View></>}<Button className='primary' onClick={() => Taro.redirectTo({ url: '/pages/library/index' })}>回到学习库</Button></View>
}
