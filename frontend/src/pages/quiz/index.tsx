import { Button, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useMemo, useState } from 'react'
import { AppHeader, BottomNav, PageTabs } from '@/components/Navigation'
import { learningApi } from '@/api/learning'
import { useQuizStore } from '@/store/quiz'
import type { AnswerRecord } from '@/types/api'
import { answersMatch } from './scoring'
import './index.scss'

export default function QuizPage () {
  const quiz = useQuizStore(s => s.quiz); const setAttempt = useQuizStore(s => s.setAttempt)
  const [index, setIndex] = useState(0); const [selected, setSelected] = useState<string[]>([])
  const [submitted, setSubmitted] = useState(false); const [records, setRecords] = useState<AnswerRecord[]>([])
  const [startedAt, setStartedAt] = useState(Date.now()); const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  const question = quiz?.questions[index]
  const correct = useMemo(() => question ? answersMatch(question.answer, selected) : false, [question, selected])
  if (!quiz || !question) return <View className='screen'><AppHeader hint='今天继续闯关' /><PageTabs active='quiz' /><View className='empty'>暂无进行中的关卡</View><BottomNav active='quiz' /></View>
  const pick = (key: string) => {
    if (submitted) return
    if (question.type === 'multiple') setSelected(value => value.includes(key) ? value.filter(item => item !== key) : [...value, key])
    else setSelected([key])
  }
  const submit = () => { if (!selected.length) { setError('先选一个答案嘛'); return }; setError(''); setSubmitted(true) }
  const next = async () => {
    const nextRecords = [...records, { question_id: question.id, selected_answers: selected, duration_ms: Date.now() - startedAt }]
    if (index < quiz.questions.length - 1) { setRecords(nextRecords); setIndex(index + 1); setSelected([]); setSubmitted(false); setStartedAt(Date.now()); return }
    setBusy(true)
    try { const attempt = await learningApi.submitAttempt(quiz.quiz_id, nextRecords); setAttempt(attempt); Taro.redirectTo({ url: '/pages/report/index' }) } catch (e) { setError(e instanceof Error ? e.message : '提交失败，请重试') } finally { setBusy(false) }
  }
  return <View className='screen'><AppHeader hint='今天继续闯关' /><PageTabs active='quiz' /><View className='title'>{quiz.title}</View><View className='subtitle'>答对就有金币，答错也会得到一段小讲解。</View><View className='panel'><View className='progress-line'><View>第 {index + 1} 题 / {quiz.questions.length}</View><View>{Math.round((index + 1) * 100 / quiz.questions.length)}%</View></View><View className='bar'><View style={{ width: `${(index + 1) * 100 / quiz.questions.length}%` }} /></View><View className='speech'>这题看起来有点东西，稳住再选！</View><View className='meta'>{question.type === 'single' ? '单选题' : question.type === 'multiple' ? '多选题' : '判断题'} · {question.knowledge_point}</View><View className='question'>{question.stem}</View>{question.options.map(option => <View key={option.key} className={`option ${selected.includes(option.key) ? 'selected' : ''}`} onClick={() => pick(option.key)}>{option.key} · {option.text}</View>)}{submitted && <View className={`feedback ${correct ? 'good' : 'bad'}`}><View className='feedback-title'>{correct ? '✓ 答对啦！' : `正确答案：${question.answer.join('、')}`}</View>{question.explanation}</View>}{error && <View className='error'>{error}</View>}<View className='actions'>{!submitted ? <Button className='primary' onClick={submit}>提交答案</Button> : <Button className='primary' loading={busy} onClick={next}>{index === quiz.questions.length - 1 ? '生成复盘报告 →' : '下一题 →'}</Button>}</View></View><BottomNav active='quiz' /></View>
}
