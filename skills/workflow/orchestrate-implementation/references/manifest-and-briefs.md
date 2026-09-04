# Implementation manifests and briefs

## Run manifest

Create one compact run manifest in runtime-managed artifacts. Record:

- repository, cwd, base ref, and mode;
- source artifact references;
- normalized constraints, non-goals, and acceptance criteria;
- task IDs, dependency edges, lanes, and claimed files/contracts;
- worker, reviewer, simplifier, oracle, and peer configuration;
- validation commands and review-round cap;
- unresolved decisions and their owners;
- per-lane base, head, last-reviewed SHA, commit, and handoff state;
- candidate-branch base, head, cherry-pick, and review state; and
- residual risks and artifact references.

Store large content in artifacts. Keep only paths and concise summaries in the manifest or mission state.

## Cold-start task brief

Give each worker one bounded brief containing:

1. goal;
2. repository, cwd, base ref, lane, and managed worktree;
3. allowed files/contracts and authority boundary;
4. relevant upstream interfaces and approved decisions;
5. acceptance criteria;
6. focused validation commands;
7. test obligation: the assigned obligation and its rationale;
8. commit and report requirements; and
9. stop/escalate conditions.

Do not paste the complete plan or accumulated task history into worker prompts.

The worker report contains:

- status and commit IDs;
- changed files;
- test-obligation evidence: the assigned obligation, rationale, commands, and results; failing test before and passing test after implementation for `new-test`;
- validation commands and results;
- open decisions and residual risks; and
- artifact and handoff references.

Workers do not expand scope, assemble other lanes, publish, or delegate further unless the orchestrator explicitly grants that authority.

## Roles and context

| Role | Context | Authority |
|---|---|---|
| Orchestrator | Parent | Routing, decisions, acceptance, candidate assembly |
| Scout/normalizer | Fresh | Read-only repository and input inspection |
| Worker | Fresh | Sole writer in one managed worktree; evidence per assigned test obligation |
| Reviewer | Fresh | Read-only review against the exact task diff |
| Simplifier | Fresh | Optional read-only complexity challenge |
| Oracle | Forked, exceptional | Advisory hard-decision escalation |

Profiles represent stable model, tool, thinking, context, or stance differences. Do not create a profile per task.

## Persistent intercom peers

Persistent peers are optional read-only consultants:

- `architecture-peer`: ADR and design consistency;
- `domain-peer`: product and domain ambiguity; and
- `quality-peer`: retained quality perspective before candidate assembly.

At configured checkpoints:

1. call `intercom({ action: "list" })`;
2. ask only live, explicitly configured peers bounded questions;
3. record advice as evidence in the manifest; and
4. use the configured missing-peer policy: `fresh-advisor` or `pause`.

Named peers must already be running or be opened separately as visible project panes. Do not claim that intercom created a clean session. Peers may not edit production code, commit, integrate, push, merge, deploy, or release.

Spawned children use `contact_supervisor` for blocking decisions or meaningful progress. The parent responds through `subagent_supervisor`. Do not route ordinary child lifecycle through generic intercom.
