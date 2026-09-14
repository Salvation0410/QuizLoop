import { describe, expect, it } from 'vitest'
import { NAV_ITEMS } from '../nav-config'

describe('主页面导航', () => {
  it('固定提供四个小程序标签及正确路由', () => {
    expect(NAV_ITEMS.map(item => item.label)).toEqual(['首页', '闯关', '学习库', '我的'])
    expect(NAV_ITEMS.map(item => item.url)).toEqual([
      '/pages/index/index',
      '/pages/quiz/index',
      '/pages/library/index',
      '/pages/profile/index'
    ])
  })

  it('每个页面标识只出现一次', () => {
    expect(new Set(NAV_ITEMS.map(item => item.id)).size).toBe(4)
  })
})
