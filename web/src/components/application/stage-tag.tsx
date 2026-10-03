// Design: Stage Tag (nC6tf): an outlined pill, 2 × 8, 12/500.
export function StageTag({ label }: { label: string }) {
  return <span className="inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-12 font-medium text-text-secondary">{label}</span>
}
