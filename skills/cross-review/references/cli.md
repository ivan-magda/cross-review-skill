# Reviewer CLI commands

Run from the repository root. These examples use Bash/Zsh arrays so paths and options stay separate arguments. Set `repo`, `review_dir`, `review_model`, and optional `review_effort` from the resolved task; `review_dir/prompt.md` is the completed brief. Give each round its own directory. Do not paste repository text into shell commands or use `eval`.

## Select and check

| Author | Reviewer CLI | Default model |
| --- | --- | --- |
| Claude | `codex exec` | `gpt-6-astra` |
| Codex | `claude -p` | `opus` |

Honor an explicit model override. Changing from one model to another within the same family does not provide the requested cross-family review. For another provider, use its documented noninteractive CLI only when explicitly selected; this skill does not assume its flags.

Check the selected executable, version, and authentication before starting:

```sh
command -v codex
codex --version
codex login status
```

or:

```sh
command -v claude
claude --version
claude auth status
```

Missing executable/authentication is a blocker for that reviewer. Report it without falling back to your own family. Do not expose credentials or change login/configuration automatically.

## Thinking / reasoning effort

`effort=LEVEL` is optional. Without it, retain the reviewer's configured default; do not claim an effective level the CLI did not report. With it, validate the value for the selected model and installed CLI, then pass it explicitly:

| CLI | Flag | Example |
| --- | --- | --- |
| Codex | `-c 'model_reasoning_effort="LEVEL"'` | `effort=xhigh` |
| Claude | `--effort LEVEL` | `effort=high` |

Verified with Codex 0.166.0 and Claude Code 2.1.317:

- The local Codex `gpt-6-astra` model catalog supports `low`, `medium`, `high`, `xhigh`, `max`, and `ultra`. `ultra` is a Codex CLI setting, not a generic API value.
- Claude's CLI accepts `low`, `medium`, `high`, `xhigh`, and `max`; actual support depends on the model behind the alias. Current Opus supports these levels, but older versions and provider aliases can differ.
- Equal level names do not imply equal computation across providers. Do not translate levels silently.
- Claude's `CLAUDE_CODE_EFFORT_LEVEL` environment setting takes precedence over `--effort`; organization/model limits can cap it. For an explicit user value, remove a conflicting environment override **for this invocation only**, or disclose the conflict and stop. Inspect diagnostics for caps; report requested and effective values separately when they differ.

Check installed help and current provider documentation when versions or model support differ. An unsupported requested model/effort needs clarification, not silent substitution.

## Claude author → Codex reviewer

```sh
review_model="gpt-6-astra"  # replace with the resolved override, if any
effort_args=()
if [ -n "${review_effort:-}" ]; then
  effort_args=(-c "model_reasoning_effort=\"$review_effort\"")
fi

cd "$repo"
codex -a never exec --model "$review_model" \
  --sandbox read-only --ephemeral --color never \
  "${effort_args[@]}" \
  -o "$review_dir/review.md" - \
  < "$review_dir/prompt.md" > "$review_dir/run.log" 2>&1
review_status=$?
```

`--sandbox read-only` constrains sandboxed commands; it is not a blanket prohibition on every connector's side effects. The review brief governs use of normal MCP/tools as well. `--ephemeral` disables session persistence, not the user's tools or settings. Do not pass write-enabled sandbox flags or permission-bypass flags.

## Codex author → Claude reviewer

```sh
review_model="opus"  # replace with the resolved override, if any
effort_args=()
if [ -n "${review_effort:-}" ]; then
  effort_args=(--effort "$review_effort")
fi

cd "$repo"
claude -p --model "$review_model" --no-session-persistence \
  "${effort_args[@]}" \
  < "$review_dir/prompt.md" \
  > "$review_dir/review.md" 2> "$review_dir/run.log"
review_status=$?
```

Use ordinary print mode with normal tools and settings. Do not add `plan`, `safe-mode`, `bare`, `--tools`, `--allowedTools`, or permission-bypass flags. This is a **read-only assignment**, not an OS-enforced read-only Claude process. In headless mode, an operation requiring approval may be denied under existing permissions. The reviewer should report any resulting coverage gap; do not disable permission checks to make it proceed.

If an explicit effort conflicts with `CLAUDE_CODE_EFFORT_LEVEL`, use `env -u CLAUDE_CODE_EFFORT_LEVEL claude ...` for that invocation; do not change the user's persistent environment.

## Completion and failures

Prefer the harness's background execution and completion notification. Otherwise use bounded waits and occasional progress updates; reviews can take several minutes. A shell tool returning a running-session ID is not completion. If a shell uses `set -e`, capture failure with an `if`/`else` rather than letting it skip the exit-status check.

After exit, inspect `review_status`, `run.log`, and `review.md`. A zero exit code is necessary but not sufficient: check for errors, blocked reads, missing modules, or incomplete output. Preserve failure artifacts, label the result incomplete, and do not triage an error message as a finding. A retry for a clear transient execution failure is not another opinion round; keep it bounded and visible.

## Primary references

- [Codex noninteractive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Codex per-run settings](https://learn.chatgpt.com/docs/developer-settings#change-settings-for-one-run)
- [Claude programmatic usage](https://code.claude.com/docs/en/headless)
- [Claude CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Claude effort configuration](https://code.claude.com/docs/en/model-config#adjust-effort-level)
- [Claude headless permission behavior](https://code.claude.com/docs/en/permission-modes#tool-calls-denied-in-claude--p-and-agent-sdk-runs)
