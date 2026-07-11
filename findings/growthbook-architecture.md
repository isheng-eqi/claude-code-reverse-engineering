# GrowthBook Remote Control — Complete Architecture

## Overview

Claude Code uses GrowthBook (growthbook.io) for remote feature flag management. At startup, it fetches all feature flags from `cdn.growthbook.io` and caches them locally. Each flag can toggle specific System Prompt modules, UI behaviors, or feature gates.

---

## Initialization Pipeline

```
App Startup
  │
  ├─ check: $3() && cachedGrowthBookFeatures empty?
  │   └─ YES → na("before_growthbook_init")
  │         → $x() (initializeGrowthBook, 1500ms timeout)
  │         → Mc("growthbook_init_ms")
  │         → na("after_growthbook_init")
  │
  ├─ GrowthBook fetch fails? → silently ignored (catch-all)
  │
  └─ Ibi() → copies T5 cache → cachedGrowthBookFeatures
              → _n() writes to app state
```

## Flag Resolution Chain

```
it(flag, default)
  │
  ├─ 1. KRt()           → Environment variable overrides
  ├─ 2. jRt()           → Profile overrides (currently empty)
  ├─ 3. U3() check      → !DISABLE_GROWTHBOOK && $3()
  │     └─ If disabled → return default
  ├─ 4. $ve.has(e)      → Track as experiment flag
  ├─ 5. T5 cache        → In-memory GB cache
  └─ 6. cachedGrowthBookFeatures → Persistent cache (app state)
        └─ o !== undefined ? o : default
```

## Disable Mechanisms

```
DISABLE_GROWTHBOOK=1     → U3() returns false → all flags use defaults
CLAUDE_CODE_SIMPLE=1     → Skips GrowthBook init entirely
$3() = false             → Telemetry disabled → GB disabled
```

## Complete Flag Catalog (208 flags)

### System Prompt Module Flags

| Flag | Module | Default | Effect |
|------|--------|---------|--------|
| `xengu_Xeron_brook` | heron_brook | empty | Inject arbitrary text into System Prompt |
| `tengu_sparrow_ledger` | reproduce_verify_workflow | false | Inject "reproduce→fix→verify" workflow |
| `tengu_cedar_lantern` | act_dont_rederive | true | Disable re-derivation of known facts |
| `tengu_silent_harbor` | tool_param_json | false | JSON parameter format reminders |
| `tengu_amber_sextant` | autonomy_append | true | Autonomous mode prompts |
| `tengu_walnut_prism` | ownership_frame | false | Ownership/agency framing |
| `tengu_amber_prism` | (permission deny) | false | Add extra text to permission denied messages |
| `tengu_amber_lark` | (memory extra) | false | Additional memory guidelines |
| `tengu_ochre_finch` | memory_types | false | Use new memory type descriptions |
| `tengu_moth_copse` | team_memory | false | Team cowork memory extra guidelines |
| `tengu_cobalt_lantern` | token_sync | false | Token sync access for GitHub |

### Tool & Feature Flags

| Flag | Controls | Default |
|------|----------|---------|
| `tengu_auto_mode_config` | Auto mode classifier configuration | ySi |
| `tengu_chair_sermon` | Message assembly strategy | false |
| `tengu_disable_bypass_permissions_mode` | Block bypassPermissions mode | false |
| `tengu_compact_cache_prefix` | Conversation compact cache | false |
| `tengu_tool_pear` | Tool behavior override | false |
| `tengu_workflows_enabled` | Dynamic workflows | false |
| `tengu_tab_read_sep` | File read sep mode | false |
| `tengu_amber_wren` | File read size/token limits | {} |
| `tengu_kairos_brief` | Brief/review mode | false |
| `tengu_orchid_mantis` | Some model behavior | false |
| `tengu_mocha_barista` | Mocha (test?) behavior | false |

### UI/UX Flags

| Flag | Controls | Default |
|------|----------|---------|
| `tengu_chrome_auto_enable` | Chrome auto-enable | false |
| `tengu_terminal_sidebar` | Terminal sidebar | false |
| `tengu_keybinding_customization_release` | Keybinding customization | false |
| `tengu_native_cursor` | Native cursor support | false |
| `tengu_cfc_in_product_permissions` | CFC in-product permissions | false |
| `tengu_surreal_dali` | Surreal Dali (UI mode) | false |
| `tengu_kairos_push_notifications` | Push notifications | false |

### Plugin & Ecosystem Flags

| Flag | Controls | Default |
|------|----------|---------|
| `tengu_plugin_official_mkt_git_fallback` | Plugin marketplace git fallback | false |
| `tengu_tussock_oriole` | Team artifact sharing | false |
| `tengu_sedge_lantern` | Plugin-related gate | false |
| `tengu_copper_thistle` | Plugin-related gate | false |
| `tengu_copper_lantern` | Plugin-related gate | false |

### Sandbox & Security Flags

| Flag | Controls | Default |
|------|----------|---------|
| `tengu_basalt_meadow` | Sandbox behavior | false |
| `tengu_destructive_command_warning` | Destructive command warning | false |
| `tengu_velvet_mallet` | Security behavior | false |
| `tengu_velvet_hammer` | Security behavior | false |
| `tengu_sepia_moth` | Security behavior | false |

### Background/Agent Flags

| Flag | Controls | Default |
|------|----------|---------|
| `tengu_bg_spare_enable` | Background spare process | false |
| `tengu_stream_watchdog_default_on` | Stream watchdog | false |
| `tengu_copper_fox` | Fork subagent | (not via it()) |
| `tengu_cicada_nap` | Background task interval | (not via it()) |
| `tengu_onyx_plover` | Auto-dream / consolidation | null |

### Networking & Performance

| Flag | Controls | Default |
|------|----------|---------|
| `tengu_byte_stream_idle_timeout_ms` | Byte stream idle timeout | n |
| `tengu_pewter_owl_model` | Model override | "" |
| `tengu_turtle_carbon` | Performance mode | false |
| `tengu_herring_clock` | Some timing behavior | false |
| `tengu_pewter_brook` | Some brook behavior | false |
| `tengu_amber_creek` | Some creek behavior | false |
| `tengu_paper_halyard` | Some halyard behavior | false |
| `tengu_brick_follow` | Some follow behavior | false |
| `tengu_chomp_inflection` | Some inflection behavior | false |

### MCP Flags

| Flag | Controls | Default |
|------|----------|---------|
| `tengu_mcp_directory_visibility` | MCP directory visibility | Z_i |
| `tengu_mcp_directory_bff` | MCP directory BFF | false |

### Misc / Unknown

| Flag | Default | Calls |
|------|---------|-------|
| `tengu_passport_quail` | false | 2 |
| `tengu_coral_beacon` | false | 2 |
| `tengu_silk_hinge` | false | 2 |
| `tengu_penguins_off` | null | 1 |
| `tengu_velvet_cascade` | null | 1 |
| `tengu_sepia_cormorant` | null | 1 |
| `tengu_umber_petrel` | false | 1 |
| `tengu_slate_thimble` | false | 1 |
| `tengu_billiard_aviary` | false | 1 |
| `tengu_amber_anchor` | false | 1 |
| `tengu_quiet_harbor` | false | 1 |
| `tengu_slate_finch` | false | 1 |
| `tengu_harbor_willow` | false | 1 |
| `tengu_moss_anchor` | false | 1 |
| `tengu_marlin_porch` | false | 1 |
| `tengu_cedar_marsh` | false | 1 |
| `tengu_crimson_vector` | false | 1 |

*(148 additional flags with single occurrences omitted for brevity)*

---

## Environment Variable Overrides

| Env Var | Overrides |
|---------|-----------|
| `DISABLE_GROWTHBOOK` | Disables ALL GrowthBook flags |
| `CLAUDE_CODE_VERIFY_PROMPT` | Forces `tengu_sparrow_ledger` ON |
| `CLAUDE_CODE_ACT_DONT_REDERIVE` | Forces `tengu_cedar_lantern` behavior |
| `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT` | Uses minimal system prompt |
| `CLAUDE_CODE_SYSTEM_PROMPT_GB_FEATURE` | Remote system prompt GB feature key |

---

## Network Request

```javascript
function H7o(config) {
  return {
    apiHost: config.apiHost || "https://cdn.growthbook.io",
    streamingHost: (config.streamingHost || config.apiHost || "https://cdn.growthbook.io")
  };
}
```

GrowthBook client initializes with `apiHost: "https://cdn.growthbook.io"` and fetches feature flags at startup with a 1500ms timeout.

## Cache Architecture

```
T5 (Map)                    ← In-memory cache from GrowthBook SDK
cachedGrowthBookFeatures    ← Persistent cache in app state
$ve (Set)                   ← Experiment feature tracking
qRt (Set)                   ← Accessed feature tracking
```

`Ibi()` periodically synchronizes T5 → cachedGrowthBookFeatures via `_n()`.

## Your Modifications

Based on the `xengu_Xeron_brook` flag name (vs original `tengu_heron_brook`), you have modified the heron_brook flag namespace. However, the GrowthBook infrastructure itself (init, fetch, cache, resolution chain) remains intact — meaning all other 207 flags are still controlled by Anthropic's GrowthBook configuration at `cdn.growthbook.io`.
