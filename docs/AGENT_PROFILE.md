# Agent profile: Agent Hub (project `fleet`)

Every Agent Hub agent follows the [Agent Development Standard](https://github.com/IsraelBO17/agent-standard/blob/main/docs/STANDARD.md) and starts from the [`agent-standard`](https://github.com/IsraelBO17/agent-standard) template ("Use this template"). This profile adds Agent Hub's contract and conventions (standard §18). It never weakens the standard.

| Topic | Agent Hub rule |
|---|---|
| Runtime | The standard's default stack (standard §3): Strands Agents on Amazon Bedrock AgentCore Runtime, us-east-1. LangGraph (Travel Planner) is a documented exception, connected through the HTTP runtime type and an adapter |
| Repository | `fleet-agent-<slug>` for one agent, `fleet-system-<slug>` for a multi-agent system deployed as one unit (ARCHITECTURE D24, standard §6) |
| Request | `AgentInvocation` in `agent_hub/api/openapi.yaml`: `messages` (history), `input`, `attachments` (15-minute signed URLs), `context`, and `decision` when resuming after an approval (D18, D19, D20) |
| Response | A stream of events ending in done or error. The exact event format is fixed in agent_hub issue #3 from the recorded AgentCore output (D10); evaluate AG-UI there |
| Approvals | `requiresApproval: true` in the descriptor for every `write-irreversible`/`external` tool, enforced with a Strands interrupt; the run ends and resumes on the decision (D19). Where the paused state lives is decided by the P8 spike. Paused state: Strands `S3SessionManager` keyed by the hub's session id is the leading option for the P8 spike |
| Multi-agent systems | Appear in the hub as **one agent** with one descriptor and one runtime. Specialists' work streams as tool steps (agents-as-tools, the default) or as `plan` steps. Every role with approval-class tools has the approval hook; approvals still reach the user through the hub's approval card (standard §9) |
| Retrieval | Knowledge bases and their data buckets are named and tagged like every fleet resource. Citations use the hub's `citations` block (P1); until then, sources are cited inline in text. Access groups come from the hub's `context` (standard §10.5), never from the model |
| Descriptor | `agent.yaml`: slug, name, description, tagline, greeting, icon (lucide), colour, stage, runtime ARN, version, disclaimer, capabilities, tools (with `requiresApproval`), starters. Registered with the hub's `hub agents add agent.yaml` in an `agent-onboarding` pull request that touches only `agents/` |
| AWS names | `fleet-<env>-<component>-<type>-<region>` (D26) |
| AWS tags | `Owner`, `Project=fleet`, `Environment`, `aws-apn-id`, `ManagedBy` on every resource; values kept out of public repos (D26) |
| Model access | An application inference profile tagged `Project=fleet` (D27); the hub's API is allowed to invoke only runtimes listed by exact ARN |
| Stages | Beta and Stable map to the descriptor's `stage`; the hub shows a Beta tag |
| Data | Synthetic only for the bank (Ledger) and health agents |

## Starting a fleet agent

1. **Use this template** on `IsraelBO17/agent-standard` → new repository `fleet-agent-<slug>` (or `fleet-system-<slug>` for a multi-agent system).
2. Write `SPEC.md` (standard §5, Appendix A).
3. Replace `src/<name>/contract.py` with the `AgentInvocation` shape from [`api/openapi.yaml`](../api/openapi.yaml) (`messages`, `input`, `attachments`, `context`, `decision`).
4. Fill `agent.yaml` with the descriptor fields above; list approval tools in both `agent.yaml` (`requiresApproval`) and `AGENT_APPROVAL_TOOLS`.
5. Infrastructure in `infra/` with fleet's names and tags (D26, D27); `AGENT_MODEL_ID` = the agent's tagged inference profile ARN.
6. When the eval gate passes and it's deployed to dev: an `agent-onboarding` pull request here adding `agents/<slug>.yaml`.
