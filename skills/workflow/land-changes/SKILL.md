---
name: land-changes
description: Land completed work end to end - integrate through merge-worktree, push, close the linked issues with evidence, and clean up run worktrees and environments. Use when asked to land, ship, or finish a branch or candidate, merge and push, close issues, or clean up worktrees after integration.
compatibility: Requires git and the merge-worktree skill; issue closure and PR mode require an authenticated gh CLI.
---

# Land Changes

One approved sequence takes finished work to its target and closes it out: commit any intended residue, integrate, push, close issues, clean up. This skill owns that sequence and its single approval; [`merge-worktree`](../merge-worktree/SKILL.md) owns the integration mechanics and target safety; `make-release` owns versioned releases. An `orchestrate-implementation` candidate handoff is a valid source; accept it under merge-worktree's candidate rules.

## Landing plan

Resolve from the request and repository: source (registered worktree/branch or candidate handoff), target branch, integration mode (local or GitHub PR), push scope, issues to close, and cleanup scope — the source worktree, the run's worktrees under `${XDG_STATE_HOME:-$HOME/.local/state}/worktrees/`, and any BB/Orca environments the run used. Then display one exact plan — integration, commits, pushes, each issue with its closing evidence, the cleanup list, and the stop boundary after each step — and require explicit approval before the first mutation. `--dry-run` stops after the plan. Later steps need only the previous step's verified result, never a fresh approval.

## Land

1. **Commit:** stage only intended uncommitted changes in the source per merge-worktree's preflight and create a concise commit; never fold in unrelated edits.
2. **Integrate:** hand the approved source and target to `merge-worktree` and take its verified result (local merge commit or merged PR) as the only integration authority. A conflict, moved target, or failed check stops the sequence with the validated state preserved.
3. **Push:** in local mode push the target branch normally and verify its remote SHA; in PR mode verify the remote target contains the merge commit. Never force-push.

## Close issues

Close only issues named in the approved plan, only after the push is verified. Close with `gh issue close <number> --repo <owner/repo> --comment "<evidence>"`, where the comment names the merge commit or PR URL and how the acceptance criteria were met. An issue whose criteria are unmet or disputed stays open with a comment stating exactly what remains. If the project selects Epiq in `project/agents/issue-tracker.md` (legacy `docs/agents/issue-tracker.md`), use only its `epiq_*` tools instead of `gh`. Closing an issue never authorizes reopening scope or editing its history.

## Clean up

Only after the push is verified (and the PR merged in PR mode):

- Remove the source worktree through merge-worktree's cleanup rule.
- Remove the completed run's remaining worktrees beneath the shared state root — worker/fix, review/reconstruction, and candidate paths — after their result refs are frozen and no consumer needs them (`git worktree remove`, then `git worktree prune`). Delete the run's `refs/heads/orchestrator/<run>/...` refs only when separately approved.
- Return BB environments and Orca workspaces through their dispatch adapters' documented cleanup routes; do not force-remove resources the host still owns.
- Preserve failed or uncertain work and anything with unknown ownership; report it instead of removing it.

## Report

Report the integration result (merge commit or PR URL), pushed refs with remote SHAs, each issue closed or deliberately left open with its link, worktrees and environments removed vs preserved, and any residual risk. If the sequence stopped early, name the completed steps, the failing gate, and the safest retry — never rewrite history, delete published state, or conceal a partial landing.
