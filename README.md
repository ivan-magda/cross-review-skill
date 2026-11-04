# Cross-review and cross-check

**Cross-review** asks another model family to review code changes, then checks each finding against the code. Keep confirmed bugs and useful simplifications; reject defensive noise without defending broken code.

**Cross-check** asks another model family to challenge a hypothesis, plan, explanation, or document, then checks its objections against the available evidence. Surface unsupported assumptions, factual errors, and gaps that could change the conclusion.

## Install

Install both self-contained skills for Codex and Claude Code globally with [the skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add ivan-magda/cross-review-skill -s '*' -g -a codex -a claude-code
```

Each skill also works on its own. Install only the one you need:

```sh
npx skills add ivan-magda/cross-review-skill --skill cross-review -g -a codex -a claude-code
npx skills add ivan-magda/cross-review-skill --skill cross-check -g -a codex -a claude-code
```

Omit `-g` to install only in the current project. Use one `-a` option to select a single agent. Inspect available skills without installing:

```sh
npx skills add ivan-magda/cross-review-skill --list
```

Both require Node.js supported by the skills CLI and the **other** model's authenticated CLI. Cross-review also uses Git and Python 3 for its repository-state helper. Cross-check needs no Git repository or helper. Neither skill installs model CLIs or changes authentication.

## Use cross-review

Report on branch changes in Codex:

```text
Use $cross-review on this branch against main. Report only.
```

Apply verified fixes with a finite limit and an explicit model/effort:

```text
Use $cross-review on this branch against main, fix, max-rounds=3, model=opus, effort=high.
```

In Claude Code:

```text
/cross-review this branch against main; fix max-rounds=3 model=gpt-6-astra effort=xhigh
```

You can specify a PR, commit range, or file subset, or provide existing review comments for triage without launching another reviewer.

## Use cross-check

Challenge a hypothesis in Codex:

```text
Use $cross-check on this hypothesis: most checkout failures come from expired sessions. Report only.
```

Check a plan in Claude Code:

```text
/cross-check this migration plan; report only, model=gpt-6-astra effort=xhigh
```

Review and revise a document with a bounded loop:

```text
Use $cross-check on docs/launch-plan.md, fix, max-rounds=3, model=opus, effort=high.
```

These are natural-language task options, not standalone `cross-review` or `cross-check` commands.

## Defaults and behavior

Both skills use these defaults:

| Setting | Default |
| --- | --- |
| Mode | `report`: review and triage without changing the source |
| Reviewer for a Claude author | Codex `gpt-6-astra` |
| Reviewer for a Codex author | Claude `opus` |
| Thinking / reasoning effort | Reviewer's configured default; override with `effort=...` |
| Maximum review rounds | `1` |

Cross-review covers the branch diff from the default branch's merge base, including staged, unstaged, and new untracked files. Cross-check covers the supplied material and copies the review artifacts into a separate working directory, preserving the original in report mode. Before sending confidential material to another provider, the author asks for permission.

The reviewer keeps its normal tools, skills, MCP integrations, and settings. Read-only is a task instruction; Codex also uses its read-only sandbox. Cross-review compares repository snapshots before and after review, including changes that leave `git status` unchanged. The helper requires an existing Git `HEAD`; it observes state and does not create a checkout or restore files. It is not a security sandbox: ignored files, external side effects, and nested repository/submodule contents fall outside its coverage. Untracked nested repositories appear as markers without content hashes.

The author checks findings against evidence and keeps unresolved questions visible. Both skills classify findings as **MUST FIX**, **SIMPLIFY**, **UNSURE**, or **REJECTED**. Each skill lists protected categories that require evidence before rejection. Cross-check requires sources for factual claims; agreement between models is not proof.

In `fix` mode, the author applies verified corrections and runs relevant verification. Set `max-rounds=N` for a finite loop; a loop request without a limit prompts for one. Later rounds examine revisions and affected context. Stop when no actionable findings survive triage, the limit is reached, verification fails or is blocked, or no safe progress remains. Final-round fixes receive verification without an extra review round.

Neither skill treats reviewer confidence as evidence, hides CLI failures behind a clean report, or changes model families without permission. Fix mode does not authorize commits, pushes, merges, or posted comments.

## Contents

| | Cross-review | Cross-check |
| --- | --- | --- |
| Instructions | [SKILL.md](skills/cross-review/SKILL.md) | [SKILL.md](skills/cross-check/SKILL.md) |
| CLI commands and effort | [CLI reference](skills/cross-review/references/cli.md) | [CLI reference](skills/cross-check/references/cli.md) |
| Reviewer brief | [Brief](skills/cross-review/references/reviewer-prompt.md) | [Brief](skills/cross-check/references/reviewer-prompt.md) |

Cross-review also includes the [repository snapshot helper](skills/cross-review/scripts/snapshot.py).

When changing CLI flags, update both `references/cli.md` files.

Inspired by the review approach in *Agentic Engineering*, particularly filtering defensive review noise and checking changes with another model family. The book and private development transcripts are not distributed here.

[MIT license](LICENSE).
