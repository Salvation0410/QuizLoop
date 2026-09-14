export type MainPage = 'home' | 'quiz' | 'library' | 'profile'

export const NAV_ITEMS: ReadonlyArray<{
  id: MainPage
  label: string
  icon: string
  url: string
}> = [
  { id: 'home', label: '首页', icon: '⌂', url: '/pages/index/index' },
  { id: 'quiz', label: '闯关', icon: '★', url: '/pages/quiz/index' },
  { id: 'library', label: '学习库', icon: '▤', url: '/pages/library/index' },
  { id: 'profile', label: '我的', icon: '◇', url: '/pages/profile/index' }
]
