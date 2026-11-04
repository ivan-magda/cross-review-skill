# Cross-review

An agent skill for cross-model code review with skeptical, evidence-based triage.

The author asks another model family to review the change, checks every claim against the code, and keeps only real bugs and useful simplifications. The guiding prior is **“assume most findings are needlessly defensive slop”**: neither accept every suggestion nor use skepticism to defend broken code.

## Install

Install for Codex and Claude Code globally with [the skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add ivan-magda/cross-review-skill --skill cross-review -g -a codex -a claude-code
```

Omit `-g` to install only in the current project. Use one `-a` option to select a single agent. To inspect available skills without installing:

```sh
npx skills add ivan-magda/cross-review-skill --list
```

Requirements: Node.js supported by the skills CLI, Git, Python 3 for the small repository-state helper, and the **other** model's authenticated CLI. The skill does not install model CLIs or change their authentication.

## Use

In Codex:

```text
Use $cross-review on this branch against main. Report only.
```

In Claude Code:

```text
/cross-review this branch against main; report only
```

Apply verified fixes and run up to three review rounds:

```text
Use cross-review in fix mode, max-rounds=3.
Review this branch against main; fix confirmed bugs and useful simplifications.
```

Choose a model and thinking effort explicitly:

```text
# When the author is Codex
Use cross-review, fix, max-rounds=3, model=opus, effort=high.

# When the author is Claude
/cross-review fix max-rounds=3 model=gpt-6-astra effort=xhigh
```

These are natural-language task options, not a standalone `cross-review` command. You can also specify a PR, commit range, or file subset, or provide existing review comments for triage without launching another reviewer.

## Defaults and behavior

| Setting | Default |
| --- | --- |
| Mode | `report` — no source edits |
| Reviewer for a Claude author | Codex `gpt-6-astra` |
| Reviewer for a Codex author | Claude `opus` |
| Thinking / reasoning effort | Reviewer's configured default; override with `effort=...` |
| Maximum review rounds | `1` |
| Scope | Branch diff from the default branch's merge base, including staged, unstaged, and new untracked files |

The reviewer keeps its normal tools, skills, MCP integrations, and settings. Claude runs with ordinary `claude -p`; there is no plan mode, safe mode, or tool allowlist. Read-only is an explicit task instruction. Codex additionally uses its read-only sandbox. A before/after repository snapshot detects tracked/index changes and untracked content changes, including edits that leave `git status` unchanged. It is not a security sandbox and does not cover ignored files, external side effects, or contents of nested repositories/submodule worktrees. Untracked nested repositories are recorded as markers without content hashes.

Each finding is checked and classified as **MUST FIX**, **SIMPLIFY**, **UNSURE**, or **REJECTED**. Findings about concurrency, persistence, security, payments, and data loss cannot be dismissed without evidence. Missing evidence remains visible as **UNSURE**.

In `fix` mode, the author applies confirmed fixes and behavior-preserving simplifications, then runs relevant verification. Every finding receives a one-line **FIXED** or **SKIPPED** disposition with a reason. A valid bug does not make the reviewer's proposed fix automatically correct.

## Bounded review loops

Set `fix, max-rounds=N` to enable a loop with a finite limit. If you request a loop without specifying the limit, the agent asks for it. A review-only request never implicitly authorizes fixes.

1. Round one reviews the requested change.
2. The author verifies claims, applies accepted fixes, and runs verification.
3. Later rounds review the fixes and affected code, carrying prior dispositions forward.
4. The loop stops when **no actionable findings survive triage**, the limit is reached, verification is blocked/failing, or no safe progress can be made.

A raw review can still contain rejected findings when the loop stops. The aim is not to make a reviewer return an empty report. Unresolved questions remain in the final report. Fixes from the last allowed round are verified but do not secretly trigger an extra review.

The workflow never silently changes model families, hides CLI failures behind “No significant findings,” or commits, pushes, merges, or posts comments without separate authorization.

## Contents

- [Skill instructions](skills/cross-review/SKILL.md)
- [CLI commands and effort settings](skills/cross-review/references/cli.md)
- [Reviewer brief](skills/cross-review/references/reviewer-prompt.md)
- [Repository snapshot helper](skills/cross-review/scripts/snapshot.py)

The helper requires an existing Git `HEAD`. It observes state; it does not create a checkout or restore files.

Inspired by the review approach in *Agentic Engineering*, particularly filtering defensive review noise and checking changes with another model family. The book and private development transcripts are not distributed here.

[MIT license](LICENSE).
