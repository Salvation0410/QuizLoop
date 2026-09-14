import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { NAV_ITEMS } from './nav-config'
import type { MainPage } from './nav-config'
import './navigation.scss'

export { NAV_ITEMS }
export type { MainPage }

const go = (url: string) => Taro.redirectTo({ url })

export function AppHeader ({ title = '你好，小皮', hint = '今天也要好好学', coins = 0 }: { title?: string; hint?: string; coins?: number }) {
  return <View className='app-header'><View className='hello'>{hint}<Text>{title}</Text></View><View className='wallet'>{coins} 金币</View></View>
}

export function PageTabs ({ active }: { active: MainPage }) {
  return <View className='page-tabs'>{NAV_ITEMS.map(item => <View key={item.id} className={`page-tab ${active === item.id ? 'active' : ''}`} onClick={() => go(item.url)}>{item.label}</View>)}</View>
}

export function BottomNav ({ active }: { active: MainPage }) {
  return <View className='bottom-nav'>{NAV_ITEMS.map(item => <View key={item.id} className={`bottom-item ${active === item.id ? 'active' : ''}`} onClick={() => go(item.url)}><Text className='nav-icon'>{item.icon}</Text>{item.label}</View>)}</View>
}
