# Agent Instructions

Use `README.md` as the source of truth for the documented workflow. For
recurring Azure Update deck tasks, follow
`.github/skills/azure-update-powerpoint/SKILL.md`.

## Keep shell commands reviewable

- Use one logical operation per shell call.
- Keep approval requests short and direct.
- Never combine preflight checks, authentication, execution, validation, and
  error handling into one PowerShell command.
- Avoid embedded scripts and dense `;` or `&&` chains when separate commands
  are practical.
- If complex reusable logic is necessary, add it as a reviewed repository
  script instead of placing it inline in a tool call.

## Respect execution intent

- Requests for commands, plans, or review are read-only.
- Do not authenticate, install, fetch, generate, or modify files until the
  user explicitly asks for execution.

Never reveal `.env` values or overwrite non-empty generated artifacts without
explicit approval.
