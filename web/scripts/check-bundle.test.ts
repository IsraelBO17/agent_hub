import { describe, expect, it } from 'vitest'
import { initialFiles } from './check-bundle.ts'

describe('initialFiles', () => {
  it('counts the entry and its static imports, not lazy chunks', () => {
    expect(initialFiles({
      'index.html': { file: 'assets/index.js', isEntry: true, imports: ['_vendor.js'] },
      '_vendor.js': { file: 'assets/vendor.js', imports: ['_shared.js'] },
      '_shared.js': { file: 'assets/shared.js' },
      'src/app/routes/notes.tsx': { file: 'assets/notes.js', imports: ['_shared.js'] },
      'style.css': { file: 'assets/style.css' },
    }).sort()).toEqual(['assets/index.js', 'assets/shared.js', 'assets/vendor.js'])
  })
})
