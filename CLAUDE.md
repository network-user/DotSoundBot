# Claude Policy Adapter

Follow `docs/ai-boundary-policy.md` as mandatory rules.

If a request may mix public bot logic with private bridge logic,
stop and ask for explicit confirmation first.

## Secrets & .env (HARD RULE)

`.env` and other secret files (see
`.cursor/rules/secrets-and-env.mdc` for the full list) are
**off-limits** to the agent unless the user explicitly grants
per-session, per-file permission.

The agent MUST NOT:
- read, search, write, patch, restore, copy, delete, or otherwise
  touch any secret file;
- print or quote contents of secret files anywhere
  (chat replies, commit messages, logs, PR descriptions,
  subagent prompts, terminal output);
- pipe secret files into external tools that would surface them.

Allowed without asking:
- `*.example`, `*.sample`, `*.template` env templates;
- talking about variable **names** in the abstract;
- referencing secret files by **path** in config (e.g. listing
  `env_file: - .env` in `docker-compose.yml`).

If a value is needed, the agent MUST stop and ask the user to
either paste the value into chat or grant explicit permission to
read a specific file. Permission does not carry over between
sessions or files.

