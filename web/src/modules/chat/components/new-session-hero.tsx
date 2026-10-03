// Design: New session (uBRCZ): the agent's greeting and description, and its starters (Starter Prompt, fkUCB),
// two to a row. A starter fills the composer; it doesn't send.
import type { Agent } from '@/models/agent'

export function NewSessionHero({ agent, onStarter }: { agent: Agent; onStarter: (prompt: string) => void }) {
  return (
    <div className="flex flex-col items-center gap-6 py-6 text-center md:py-12">
      <div className="flex flex-col items-center gap-2.5">
        <h2 className="text-20 font-semibold text-text-primary sm:text-28">{agent.defaultGreeting ?? 'What can I help you with today?'}</h2>
        <p className="max-w-130 text-14 leading-relaxed whitespace-pre-line text-text-secondary">{agent.description}</p>
      </div>
      {agent.starters.length > 0 ? (
        <ul aria-label="Starters" className="grid w-full gap-2.5 sm:grid-cols-2">
          {agent.starters.map((s) => (
            <li key={s.title}>
              <button type="button" onClick={() => { onStarter(s.prompt) }} disabled={!agent.available} className="flex size-full flex-col gap-1 rounded-12 border bg-surface px-4 py-3.5 text-left hover:bg-hover disabled:opacity-60">
                <span className="text-14 font-medium text-text-primary">{s.title}</span>
                {s.description ? <span className="text-13 text-text-tertiary">{s.description}</span> : null}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
