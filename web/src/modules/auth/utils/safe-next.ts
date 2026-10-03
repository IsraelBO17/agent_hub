/** Where to go after sign-in: a relative path inside the app, never another site (standard §9). */
export const safeNext = (next: string | null) => (next?.startsWith('/') && !next.startsWith('//') && !next.startsWith('/sign-in') ? next : '/')
