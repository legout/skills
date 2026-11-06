# Optional cleanup review

Use only when additional reviewers are explicitly requested or required by project rules, with applicable delegation authority. The ordinary cleanup stays one bounded pass by the current agent.

> Selected review perspectives adapt [Cursor pstack poteto-mode](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/poteto-mode) and its refactoring playbook (MIT, Copyright (c) 2026 Cursor). This local brief was formerly part of the catalog's retired cleanup skill.

Give each reviewer the exact scope, diff command and file list, approved cleanup criteria, written conventions, real callers/inputs/environment, and applicable verification evidence. Paste the relevant Reuse, Quality, or Efficiency criterion from `SKILL.md` and the complete contract below into its prompt; links alone are insufficient. For an explicitly requested three-perspective review, assign one perspective per reviewer. Do not invent a required agent name, model, or extra review round. If required independent review cannot run, report that limitation rather than silently substituting self-review.

<!-- reviewer-contract:start -->
```text
Review <base>..<head or exact user scope> against <approved simplification criteria and behavior-preservation constraints>.
Written conventions: <named sources and relevant rules, or none found>.
Real use: <callers, input provenance, environment, touched boundaries>.
Priority: agreed feature, then correctness, then proven risk. Project written conventions are binding; violations are must-fix. Unwritten taste never blocks.
Report only a violation of a named requirement or written rule that this change caused or worsened, reachable through real callers, inputs, and environment, with material impact and a proportionate response. Cite the rule, changed location, scenario, impact, and response. For explicit cleanup, name the authorized cleanup criterion and demonstrate the concrete duplication/cost; the criterion does not authorize behavior changes.
Security activates only for touched boundaries: untrusted or external input (files, queries, network), credentials, auth, dependency changes. Require a named asset, realistic attacker, and an attack path through real use. Stories requiring stolen secrets, broken TLS, malicious admins, or generic extra hardening are not findings. No boundary touched: write "security: n/a". Security facts missing: mark the criterion unverified; never invent a threat model. Trusted internal callers and user-owned local files are not hostile by default; written safety guarantees still bind.
Test requests are findings too: name a reachable real scenario or drop them. Coverage percentage is not a reason.
Large or out-of-scope fixes: one line with the owner decision needed, not an automatic fix-first item. Unrelated issues: one line max, non-blocking. Do not fix, dispatch workers, or start re-reviews; the parent dispositions findings before repair.
Reuse verified evidence while the relevant code, tests, inputs, and environment still match; a rerun needs a relevant delta or specific hypothesis. A failure does not widen scope or weaken expectations. The parent owns one fix pass and one delta-only recheck; no third round.
Finish when agreed criteria, real risks, and written rules are covered; zero findings is success. Verdict: pass or fix-first (small in-scope repairs), with any unverified criterion or required human decision explicitly stated. A pass does not clear those decisions or authorize acceptance/publication. Then stop.
```
<!-- reviewer-contract:end -->

The parent deduplicates and dispositions findings before applying only authorized changes. Reviewer output grants no edit or scope authority. Recheck only the accepted fix and its affected behavior; replace the prompt's first line with the original finding and fix range, retaining the other gates. If that finding survives the one delta recheck, ask the human.
