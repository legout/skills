# State lifecycles

Use this lens for lifecycle rules hidden across flags, callbacks, status fields, or call ordering. Start with an important journey in the review scope, not every conditional in the application. State what was inspected and what remains unexamined.

## Trace the current lifecycle

Follow real callers, handlers, background work, persistence, and relevant tests. Record the observed model separately from intended behavior established by requirements or domain rules; mark unknowns rather than inventing transitions.

- Identify meaningful states and their authoritative owner. Distinguish persisted state, derived views, and independent lifecycles; do not collapse unrelated flags into one global machine.
- Trace **state → event → guard → next state → side effects**, with file/symbol locations. Include who may initiate the event and who commits the transition.
- Follow applicable failure and recovery paths: rejected events, cancellation, retry, reload/resume, and delayed or out-of-order asynchronous results. Inspect only paths supported by actual callers and environment.

A compact transition table is enough; a diagram is optional. Do not create a separate inventory artifact unless requested.

## Identify worthwhile candidates

Look for contradictory flags, duplicated transition rules, scattered ownership, missing required recovery, and stale results overwriting newer state. For each candidate, name a reachable event sequence, the affected contract, and its material consequence. A theoretically possible flag combination is not evidence that the application can reach it. Implicit state alone is not a defect.

Propose the smallest organizing change that addresses the demonstrated problem: ordinary functions and an enum may suffice; a table, reducer, or state machine must earn its complexity. Do not default to a state-machine library, formal verifier, or whole-application rewrite. Proposed behavior changes are design decisions, not behavior-preserving cleanup.

## Explain the benefit

For each worthwhile candidate, describe concrete effects rather than assigning UX/DX/AX scores:

- **UX:** predictable progress, errors, cancellation, retry, or recovery for the affected user journey.
- **DX:** clearer state ownership and fewer places to update transition rules.
- **AX:** an agent can locate valid transitions, guards, and side effects without reconstructing the whole application.

State trade-offs and unaffected dimensions; do not promise every change improves all three. Name contracts to preserve and the smallest relevant verification, reusing applicable evidence. Feed candidates into the main skill's ranked report and approval handoff; discovery does not authorize edits or prove behavior preservation.
