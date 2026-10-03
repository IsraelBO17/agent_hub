import { describe, expect, it, vi } from 'vitest'
import { batchPerFrame } from '@/utils/batch-per-frame'

describe('batchPerFrame', () => {
  it('flushes everything pushed within one frame together', async () => {
    const flush = vi.fn()
    const batch = batchPerFrame<string>(flush)
    batch.push('a')
    batch.push('b')
    expect(flush).not.toHaveBeenCalled()
    await new Promise((r) => requestAnimationFrame(r))
    expect(flush).toHaveBeenCalledExactlyOnceWith(['a', 'b'])
  })
  it('flushNow hands over at once', () => {
    const flush = vi.fn()
    const batch = batchPerFrame<number>(flush)
    batch.push(1)
    batch.flushNow()
    expect(flush).toHaveBeenCalledWith([1])
  })

  it('hands over on a timer when no frame comes (a background tab)', () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const raf = vi.spyOn(window, 'requestAnimationFrame').mockImplementation(() => 1) // frames never run
    const flush = vi.fn()
    const batch = batchPerFrame<string>(flush, 250)
    batch.push('a')
    batch.push('b')
    vi.advanceTimersByTime(249)
    expect(flush).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(flush).toHaveBeenCalledExactlyOnceWith(['a', 'b'])
    raf.mockRestore()
  })
})
