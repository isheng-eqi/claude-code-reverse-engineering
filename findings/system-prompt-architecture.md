# Claude Code System Prompt — Complete Assembly Architecture

## Overview

Claude Code's System Prompt is **NOT a fixed text block**. It is assembled at runtime from 20+ independent modules, each with its own activation condition. This document maps every module, its activation logic, and its relationship to GrowthBook remote flags.

## Assembly Pipeline

```
QLo() — Main assembly function
  │
  ├─ Static Modules (always included)
  │   ├─ Nkf()  — Identity & safety prefix
  │   ├─ $kf()  — Tool definitions
  │   ├─ Ukf()  — Coding instructions  (condition: keepCodingInstructions)
  │   ├─ Fkf()  — Action caution
  │   ├─ Bkf()  — (unknown)
  │   └─ Gkf()  — (unknown)
  │
  ├─ Dynamic Modules (conditionally included)
  │   ├─ _k("task_continuity")      → kkf(s)
  │   ├─ _k("action_caution")       → Ikf(t)
  │   ├─ _k("fable_identity")       → S_n(s)||Yq(t) ? xkf : null
  │   ├─ _k("tool_param_json")      → Gbi()||(FQ(s)||Yq(t))&&it("tengu_silent_harbor",!1) ? Rkf : null
  │   ├─ _k("investigate_first")    → i0f(t)
  │   ├─ _k("session_guidance")     → Vkf(d,l,o,p)
  │   └─ _k("memory")              → EDt(t)
  │
  ├─ Environment Modules
  │   ├─ _k("env_info_simple")      → Jkf(t,p,n)  [default]
  │   │   OR _k("env_info_static")  → Qkf(t,p)    [excludeDynamicSections]
  │   ├─ _k("language")            → Mkf(u.language)
  │   ├─ _k("output_style")        → Okf(c)
  │   └─ _k("bg-session")          → e0f()
  │
  ├─ GrowthBook-Controlled Modules
  │   ├─ _k("scratchpad")           → hVn()
  │   ├─ _k("context_management")   → t0f
  │   ├─ _k("brief")               → n0f()
  │   ├─ _k("focus_mode")           → s0f(t)
  │   ├─ _k("reproduce_verify_workflow") → zkf() ? Kkf : null
  │   │     └─ zkf: checks tengu_sparrow_ledger OR CLAUDE_CODE_VERIFY_PROMPT env
  │   ├─ _k("act_dont_rederive")    → jkf() ? Ykf : null
  │   │     └─ jkf: (condition unknown, function body not found)
  │   ├─ _k("heron_brook")          → Pkf()
  │   │     └─ **MODIFIED: reads xengu_Xeron_brook instead of tengu_heron_brook**
  │   └─ _k("autonomy_append")      → Lkf(s)
  │
  └─ __SYSTEM_PROMPT_DYNAMIC_BOUNDARY__  (variable: yoe)
       ↑ Separates static cacheable prefix from per-session dynamic suffix
```

## Key Module Details

### heron_brook (Pkf) — REMOTE TEXT INJECTION (**MODIFIED**)

```javascript
function Pkf(){
  // Step 1: Check client-side cache FIRST (new priority)
  let e = It().clientDataCache?.xengu_Xeron_brook;
  if(typeof e === "string" && e.trim() !== ""){
    let n = e.trim();
    V("xengu_Xeron_brook_applied", {len: n.length, fromClientData: true});
    return n;
  }
  // Step 2: Fall back to GrowthBook flag
  let t = it("xengu_Xeron_brook", "");
  if(t.trim() !== ""){
    let n = t.trim();
    V("xengu_Xeron_brook_applied", {len: n.length, fromClientData: false});
    return n;
  }
  return null;  // Empty → not injected
}
```

**MODIFICATION NOTE**: The original binary uses `tengu_heron_brook`. This modified version uses `xengu_Xeron_brook` and adds a client-side cache priority layer that didn't exist before.

### reproduce_verify_workflow (Kkf via zkf)

```javascript
function zkf(){
  let e = ot(process.env.CLAUDE_CODE_VERIFY_PROMPT);
  let t = e || it("tengu_sparrow_ledger", false);
  if(t) T(`verify_prompt_arm_active source=${e ? "env" : "growthbook"}`);
  return t;
}
```

Activated by: `CLAUDE_CODE_VERIFY_PROMPT` env var OR `tengu_sparrow_ledger` GrowthBook flag.

### tool_param_json (Rkf)

```javascript
_k("tool_param_json", () => 
  Gbi() || (FQ(s) || Yq(t)) && it("tengu_silent_harbor", false) 
    ? Rkf : null
)
```

Activated by: `tengu_silent_harbor` GrowthBook flag + additional model/identity conditions.

### fable_identity (xkf)

```javascript
_k("fable_identity", () => 
  S_n(s) || Yq(t) ? xkf : null
)
```

Only active when: using Fable model (`S_n(s)`) OR Fable is pinned (`Yq(t)`).

## GrowthBook Flag → Module Mapping

| GrowthBook Flag | Module | Effect |
|----------------|--------|--------|
| `xengu_Xeron_brook` | heron_brook | **Inject arbitrary text into System Prompt** (MODIFIED from tengu_heron_brook) |
| `tengu_sparrow_ledger` | reproduce_verify_workflow | Inject "reproduce → fix → verify" workflow |
| `tengu_silent_harbor` | tool_param_json | JSON parameter format reminders |
| `tengu_cedar_lantern` | act_dont_rederive | Disable re-derivation of known facts |
| `tengu_walnut_prism` | (multi-module) | Ownership/agency framing across modules |
| `tengu_amber_sextant` | autonomy_append | Autonomous mode additional prompts |

## Environment Variables Override

| Env Var | Overrides | Default |
|---------|-----------|---------|
| `CLAUDE_CODE_VERIFY_PROMPT` | `tengu_sparrow_ledger` | via GrowthBook |
| `DISABLE_GROWTHBOOK` | All GrowthBook flags | GrowthBook active |
| `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT` | Entire dynamic prompt | Full dynamic assembly |
| `CLAUDE_CODE_DISABLE_ATTACHMENTS` | Attachment section | Included |

## Architecture Detail: Cache Boundary

The `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` (stored in variable `yoe`) splits the prompt into:
- **ABOVE boundary**: Static modules (identity, tools, safety, coding instructions) — identical for all users, globally cacheable
- **BELOW boundary**: Dynamic modules (env info, date, git status, focus mode, scratchpad) — per-session, recomputed each turn

## What's Still Obfuscated

The actual text content of each module (what `Nkf`, `$kf`, `Ukf` etc. return as text strings) is stored in Bun bytecode within `cli.js.bytecode` (120MB). The module functions' bodies in `cli.js` are bytecode references, not readable text. Full text extraction requires Bun bytecode decompilation.

However, from the function signatures and activation conditions, we can fully reconstruct **which modules exist and when they activate** — which is the most important part of the System Prompt architecture.
