# Runtime Analysis — Complete Startup & Execution Map

## Startup Sequence (ordered by timing markers)

```
cli_before_main_import
  │
  ├─ init_after_graceful_shutdown
  ├─ init_after_1p_event_logging
  ├─ init_after_oauth_populate  
  ├─ init_after_jetbrains_detection
  ├─ init_after_remote_settings_check
  │
  ├─ before_growthbook_init
  │   └─ $x() — fetch flags from cdn.growthbook.io (1500ms timeout)
  ├─ after_growthbook_init
  │
  ├─ startup_custom_id
  ├─ startup_resolve_model
  ├─ startup_safe_mode
  │
  ├─ prefetchAllMcpResources
  ├─ prefetch_system_context_non_interactive / has_trust / skipped_no_trust
  │
  ├─ cli_before_main_import
  ├─ cli_after_main_import  
  │
  └─ main() — REPL loop starts
```

## Configuration Files Read at Startup

| File | Purpose |
|------|---------|
| `settings.json` | User settings (model, permissions, hooks) |
| `settings.local.json` | Local overrides |
| `.mcp.json` | MCP server configurations |
| `.gitconfig` | Git configuration (proxy, user info) |
| `CLAUDE.md` | Project instructions |
| `MEMORY.md` | Persistent memory index |
| `.claude.json` | OAuth/auth cache |
| `.config.json` | GrowthBook feature cache |
| `remote-settings.json` | Remote session state |
| `managed-settings` | Enterprise policy settings |

## Network Endpoints

### Anthropic Core API
- `api.anthropic.com` — Main API
- `api-staging.anthropic.com` — Staging
- Various Bedrock/Vertex/Foundry regional endpoints

### Feature Flags & Telemetry
- `cdn.growthbook.io` — Feature flag distribution
- `http-intake.logs.us5.datadoghq.com` — DataDog telemetry
- `api.datadoghq.com` — DataDog API

### OAuth & Auth Providers
- `claude.ai` — Main auth
- `login.microsoftonline.com` (+ .de, .us, .cn variants) — Azure AD
- `accounts.google.com` — Google OAuth
- `cognito-identity.*.amazonaws.com` — AWS Cognito
- `sts.*.amazonaws.com` — AWS STS

### Claude Code Services
- `code.claude.com` — Documentation
- `downloads.claude.ai` — Binary downloads
- `platform.claude.com` — Platform API
- `bridge.claudeusercontent.com` — WebSocket remote control
- `mcp-proxy.anthropic.com` — MCP proxy

### Third-Party Integrations
- `api.github.com` — GitHub API
- `api.notion.com`, `mcp.notion.com` — Notion
- `mcp.slack.com`, `slack.com` — Slack
- `mcp.figma.com` — Figma
- `mcp.linear.app` — Linear
- `mcp.asana.com` — Asana
- `api.githubcopilot.com` — GitHub Copilot

### AWS Regional Endpoints
- `bedrock.{region}.amazonaws.com`
- `bedrock-runtime.{region}.amazonaws.com`
- `bedrock-fips.{region}.amazonaws.com`

### Google Cloud
- `aiplatform.googleapis.com`
- `cloudresourcemanager.googleapis.com`
- `storage.googleapis.com`
- `oauth2.googleapis.com`

### CDN & Static
- `raw.githubusercontent.com`
- `fonts.googleapis.com`

## API Endpoints (Anthropic Backend)

| Path | Purpose |
|------|---------|
| `/v1/messages` | Main chat completion |
| `/v1/messages/count_tokens` | Token counting |
| `/v1/messages/batches` | Batch processing |
| `/v1/complete` | Legacy completion |
| `/v1/models` | Model listing |
| `/v1/token`, `/v1/oauth/token` | OAuth token |
| `/v1/code/agent-proxy` | Agent proxy |
| `/v1/code/github/import-token` | GitHub token import |
| `/v1/code/triggers` | Managed triggers |
| `/v1/design/` | Design sync |
| `/v1/ultrareview/preflight` | Ultrareview preflight |
| `/v1/filestore/fs/readFile` | Remote file read |
| `/api/claude_code/skills` | Skill marketplace |
| `/api/claude_code/notification/preferences` | Notification prefs |
| `/api/claude_code/organizations/metrics_enabled` | Org metrics |
| `/api/claude_code_grove` | Grove feature |
| `/api/claude_code_shared_session_transcripts` | Shared transcripts |
| `/api/event_logging/v2/batch` | Event logging |
| `/api/frame/deploy/init` | Artifact publish init |
| `/api/frame/deploy/direct` | Artifact direct upload |
| `/api/frame/deploy/complete` | Artifact publish complete |
| `/api/oauth/account/settings` | Account settings |
| `/api/oauth/usage` | Usage/billing |
| `/api/oauth/account/grove_notice_viewed` | Grove notice |
| `/api/organization/claude_code_first_token_date` | Org first token |
| `/api/claude_cli_feedback` | CLI feedback |
| `/api/ws/speech_to_text/voice_stream` | Voice dictation |

## Key Environment Variables (500+ total)

### Core Configuration
- `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`
- `CLAUDE_CODE_OAUTH_TOKEN` — OAuth token (76 refs!)
- `CLAUDE_CODE_ENTRYPOINT` — Entry point identifier (67 refs)

### Disable Switches
- `DISABLE_GROWTHBOOK` — Disable feature flags
- `DISABLE_TELEMETRY` — Disable telemetry
- `DISABLE_PROMPT_CACHING` — Disable prompt caching (17 refs)
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` — Block non-essential network
- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` — Block background tasks

### Provider Selection
- `CLAUDE_CODE_USE_BEDROCK` — AWS Bedrock (17 refs)
- `CLAUDE_CODE_USE_VERTEX` — GCP Vertex (16 refs)
- `CLAUDE_CODE_USE_ANTHROPIC_AWS` — AWS private (13 refs)
- `CLAUDE_CODE_USE_MANTLE` — Internal Mantle (13 refs)
- `CLAUDE_CODE_USE_FOUNDRY` — Internal Foundry (11 refs)

### Telemetry Control
- `OTEL_EXPORTER_OTLP_ENDPOINT` — OpenTelemetry endpoint
- `OTEL_EXPORTER_OTLP_HEADERS` — OTel headers
- `CLAUDE_CODE_ENABLE_TELEMETRY` — Telemetry toggle

## System Prompt Assembly

The System Prompt is assembled at startup via `QLo()` with this module order:

```
Static Modules (always):
  1. Nkf()  — Identity declaration
  2. $kf()  — Tool definitions  
  3. Ukf()  — Coding instructions
  4. Fkf()  — Action caution
  5. Bkf()  — (unknown)
  6. Gkf()  — (unknown)

Dynamic Modules (conditionally):
  7.  _k("task_continuity")
  8.  _k("action_caution")
  9.  _k("fable_identity")       → Fable model only
  10. _k("tool_param_json")      → tengu_silent_harbor
  11. _k("investigate_first")
  12. _k("session_guidance")
  13. _k("memory")

Environment Modules:
  14. _k("env_info_simple/static") → OS, git, cwd, model
  15. _k("language")
  16. _k("output_style")
  17. _k("bg-session")            → Background only

GrowthBook-Controlled:
  18. _k("scratchpad")
  19. _k("context_management")
  20. _k("brief")
  21. _k("focus_mode")
  22. _k("reproduce_verify_workflow") → tengu_sparrow_ledger
  23. _k("act_dont_rederive")         → tengu_cedar_lantern
  24. _k("heron_brook")               → xengu_Xeron_brook
  25. _k("autonomy_append")           → tengu_amber_sextant

Boundary:
  __SYSTEM_PROMPT_DYNAMIC_BOUNDARY__
  (separates cacheable static from per-session dynamic)
```

After assembly, additional context is injected as `<system-reminder>` blocks:
- `CLAUDE.md` content (if exists)
- `MEMORY.md` index (if exists)
- Git state (branch, status)
- Current date
- Screenshot attachments (if applicable)
