# Reviewer CLI commands

Run from the artifact directory outside any repository. These examples use Bash/Zsh arrays so paths and options stay separate arguments. Set `review_dir`, `review_model`, optional `review_effort`, and `source_dirs=()` (or absolute extra-source directories); `review_dir/prompt.md` is the completed brief. Give each round its own directory. Do not paste artifact text into shell commands or use `eval`.

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

cd "$review_dir"
codex --search -a never exec --model "$review_model" \
  --sandbox read-only --ephemeral --skip-git-repo-check --color never \
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

source_args=()
for source_dir in "${source_dirs[@]}"; do
  source_args+=(--add-dir "$source_dir")
done

cd "$review_dir"
claude -p --model "$review_model" --no-session-persistence \
  --allowedTools "WebSearch,WebFetch" \
  "${source_args[@]}" \
  "${effort_args[@]}" \
  < "$review_dir/prompt.md" \
  > "$review_dir/review.md" 2> "$review_dir/run.log"
review_status=$?
```

Use ordinary print mode with normal tools and settings. `--allowedTools "WebSearch,WebFetch"` pre-approves web calls without restricting other tools. Do not add `plan`, `safe-mode`, `bare`, `--tools`, other `--allowedTools` entries, or permission-bypass flags. This is a **read-only assignment**, not an OS-enforced read-only Claude process. Calls needing other approvals may be denied; report the resulting coverage gaps.

If an explicit effort conflicts with `CLAUDE_CODE_EFFORT_LEVEL`, use `env -u CLAUDE_CODE_EFFORT_LEVEL claude ...` for that invocation; do not change the user's persistent environment.

## Web access

- Codex: put `--search` before `exec` to enable live search.
- Claude: `--allowedTools "WebSearch,WebFetch"` pre-approves those tools when available. It does not provide missing tools or override network and policy restrictions.

Check actual access each run. If unavailable, mark factual claims **unverified (model knowledge only)** unless inspected supplied sources support them, and list the coverage gap. Do not bypass permissions to enable search. `--json` (Codex) or `--output-format stream-json --verbose` (Claude) can capture diagnostic tool events; retain the final reviewer text separately when using them.

## Completion and failures

If evidence shows the author's sandbox blocked the reviewer CLI, request narrowly scoped approval for that command through the harness's normal mechanism, when available and permitted. Retry only after approval; if escalation is unavailable, denied, or forbidden (for example, approval policy `never`), report the review as incomplete.

Wait for the reviewer to exit using the harness's background completion notification or bounded waits with occasional progress updates. If a shell uses `set -e`, capture failure with an `if`/`else` rather than letting it skip the exit-status check.

After exit, inspect `review_status`, `run.log`, and `review.md`. A zero exit code is necessary but not sufficient: check for errors, blocked reads, missing modules, or incomplete output. Preserve failure artifacts, label the result incomplete, and do not triage an error message as a finding. A retry for a clear transient execution failure is not another opinion round; keep it bounded and visible.

## Primary references

- [Codex noninteractive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Codex web-search configuration](https://learn.chatgpt.com/docs/config-file/config-basic#web-search-mode)
- [Codex per-run settings](https://learn.chatgpt.com/docs/developer-settings#change-settings-for-one-run)
- [Claude programmatic usage](https://code.claude.com/docs/en/headless)
- [Claude CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Claude effort configuration](https://code.claude.com/docs/en/model-config#adjust-effort-level)
- [Claude headless permission behavior](https://code.claude.com/docs/en/permission-modes#tool-calls-denied-in-claude--p-and-agent-sdk-runs)
