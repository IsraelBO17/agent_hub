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
})
