---
name: merge-worktree
description: Merge a completed Git worktree into a target branch locally or through an automatically merged GitHub pull request. Use whenever the user asks to merge, integrate, land, or clean up worktree changes.
compatibility: Requires git; PR mode also requires gh authentication.
---

# Merge Worktree

Merge one registered Git worktree with a merge commit. Commit pending source changes, validate the result, push the integrated branch, attempt conflict resolution, and optionally remove the source worktree.

**Required skills:** Load `github` for PR operations. If a merge or rebase conflict occurs, load `resolving-merge-conflicts` from `mattpocock/skills` and follow it before continuing.

## Inputs

Resolve these from the request and repository before asking:

- source worktree path or its checked-out branch;
- target branch;
- mode: `local` or `pr`; and
- cleanup choice: enabled by `--clean-up`, otherwise ask after a successful merge.

Use the repository default branch as the target only when it is unambiguous. Ask for any unresolved input. Never treat the target worktree as the cleanup candidate.

## Preflight

1. Run `git worktree list --porcelain` and verify that the source is a registered worktree with a non-detached branch.
2. Verify the source and target belong to the same repository, no merge/rebase is already in progress, and the target checkout is clean.
3. Fetch and prune the target remote. Stop for authentication failures or an ambiguous/diverged target; never force-push.
4. Inspect the source diff and repository instructions. Refuse unrelated or secret-bearing changes.
5. Discover and run the smallest relevant project checks.
6. If the source has intended uncommitted changes, stage them and create one concise Conventional Commit. Do not amend existing commits unless requested.

## Local mode

Keep the target branch untouched until the merged result passes validation:

1. Create a temporary integration branch and sibling worktree from the fetched target SHA. Record the target SHA and integration path.
2. In that isolated worktree, run `git merge --no-ff <source-branch>` with a concise merge message.
3. On conflicts, load `resolving-merge-conflicts`, trace both changes to their intent, resolve every conflict, run the project checks, and complete the merge commit. Do not choose `ours` or `theirs` wholesale without evidence. Regenerate conflicted generated lockfiles with their owning package manager instead of hand-editing them.
4. Run the relevant checks against the integration worktree and verify it is clean and conflict-free.
5. Reconfirm that the target branch still equals the recorded target SHA. In its existing worktree, fast-forward it to the validated integration commit; if no target worktree exists, create one first. Stop rather than replaying onto a target that moved.
6. Push the target branch normally and verify that its upstream SHA equals the local target SHA.
7. Remove the temporary integration worktree with `git worktree remove`, delete only its known ephemeral integration branch, and run `git worktree prune`. Preserve the integration worktree instead when integration stops with unresolved state.
8. Verify the final worktree list and that any original main worktree not used as the target remains unchanged.

Never use `rm -rf` or forced worktree removal for cleanup. Do not report success unless the merge commit, checks, push, SHA verification, and final worktree verification all succeed.

## PR mode

1. Load `github` and verify `gh auth status` plus the GitHub remote.
2. Push the source branch with upstream tracking.
3. Reuse its open PR or create one with `gh pr create`, targeting the selected branch and deriving the title/body from the commits and validation evidence.
4. If GitHub reports merge conflicts, merge the current target into the source locally with `--no-ff`. Load `resolving-merge-conflicts`, resolve and validate the merge, then push the source branch normally.
5. Watch required checks with `gh pr checks --watch`. Stop if checks fail; do not bypass branch protection.
6. Merge with a merge commit using `gh pr merge --merge`. If repository policy requires queued/automatic merging, enable GitHub auto-merge rather than bypassing the policy.
7. Verify the PR is merged and the remote target contains the source changes.

## Cleanup

Only after successful integration and verification:

- With `--clean-up`, remove the source worktree automatically.
- Without `--clean-up`, ask whether to remove it.
- Before removal, verify the source worktree is clean and its commit is reachable from the merged target.
- Remove it with `git worktree remove <path>`, then run `git worktree prune`.
- Do not delete local or remote branches unless the user separately requests branch deletion.
- Never use forced worktree removal to hide uncommitted changes.

## Report

Report the mode, source and target, merge commit or PR URL, checks run, pushed target SHA, and whether the source worktree was removed. If stopped, name the exact failing gate and leave all worktrees intact.
