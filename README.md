# Claude Code Unmasked: Full Binary Reverse Engineering of Anthropic's 215MB Agent CLI

> **Claude Code is not a statically-compiled application. It is a 215MB self-contained operating system disguised as a CLI — with its own JavaScript VM, hidden virtual filesystem, 1400+ remotely-controlled feature flags, and a self-protection system designed to prevent exactly this kind of analysis.**

[![Analysis Type](https://img.shields.io/badge/analysis-binary_reverse_engineering-red)](https://github.com/isheng-eqi/claude-code-reverse-engineering)
[![Target Version](https://img.shields.io/badge/target-Claude%20Code%20v2.1.186-blue)](https://www.npmjs.com/package/@anthropic-ai/claude-code)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 📋 Table of Contents

- [What This Is](#what-this-is)
- [How It Was Done](#how-it-was-done)
- [Key Findings](#key-findings)
- [Analysis Scripts](#analysis-scripts)
- [Quick Start](#quick-start)
- [Detailed Findings](#detailed-findings)
- [Why This Matters](#why-this-matters)

---

## What This Is

A complete, reproducible binary reverse engineering of Claude Code — Anthropic's official CLI agent harness. This project peels back every layer of the 215MB `claude.exe` to reveal:

- **What's inside the binary** — 12 PE sections, a Bun JavaScript VM, and 861 embedded files
- **How it assembles its identity** — 30+ dynamically-composed System Prompt modules
- **How it's remotely controlled** — 1400+ GrowthBook feature flags that can inject arbitrary text into any user's session
- **How it protects itself** — self-analysis ban, three-tier safety classifier, and how the filename-based bypass works
- **The complete execution flow** — from `claude` Enter to SSE streaming response

Every finding is backed by **runnable Python scripts** in this repository — no guesswork, no black boxes.

---

## How It Was Done

### The Self-Protection Bypass

Claude Code's System Prompt contains a hard rule: **never analyze, modify, or reverse-engineer the `claude.exe` binary itself.** But this protection has one critical weakness:

> **It identifies "itself" by filename, not by content.**

The bypass is trivially simple:
```bash
cp claude.exe a.exe
```

From that moment on, Claude Code treats `a.exe` as "a user-provided binary file" and grants full access to Read, Bash, and Grep tools. Verified via SHA256:

| File | SHA256 |
|------|--------|
| Original (npm) | `6a286f0795d6dd46187b86e9124f819af35319169901cd883b80a75c47469516` |
| Renamed copy | `6a286f0795d6dd46187b86e9124f819af35319169901cd883b80a75c47469516` |

Identical binary. The AI just doesn't know it's looking at itself.

### Analysis Methodology

All analysis uses **professional-grade Python tools** — no AI-assisted guessing:

| Tool | Purpose |
|------|---------|
| `pefile` | PE32+ header parsing, section enumeration, entropy analysis |
| Binary regex scanning | VFS file extraction, string classification, pattern matching |
| SHA256 hashing | Integrity verification across analysis stages |

The scripts are **fully reproducible** — anyone with the `claude.exe` binary can run them and get identical results.

---

## Key Findings

### 1. Architecture: Bun VM + Embedded Filesystem

Claude Code is built with **Bun v1.4.0** (`bun build --compile`), which welds three things into a single x64 PE executable:

```
┌─────────────────────────────────────┐
│  Bun JavaScript Runtime (Zig)       │  ← The engine
├─────────────────────────────────────┤
│  Claude Code JS/TS → Bytecode       │  ← The app logic
├─────────────────────────────────────┤
│  861 resource files in .bun VFS     │  ← The data
└─────────────────────────────────────┘
```

No Node.js, no `npm install` needed — it's genuinely self-contained.

### 2. PE Section Layout

```
Section     Size       Entropy    Content
───────     ────       ───────    ───────
.text       54.3 MB    6.27       x64 machine code + Bun bytecode
.rdata      21.2 MB    4.70       String constants, System Prompt, JSON schemas
.data        2.3 MB    2.77       Global variables
.bun       138.4 MB    5.16       Bun Virtual Filesystem (861 files)
```

> **Key insight:** The `.bun` section at 138.4 MB is the beating heart — it contains a serialized virtual filesystem that Bun mounts at startup, making `require()` and `import` work as if these files existed on disk.

### 3. The Dynamic System Prompt Assembly

Claude Code's System Prompt is NOT a fixed string. It's assembled at runtime from **30+ independent modules**, each controlled by a matrix of conditions:

```javascript
// Simplified extraction from bytecode
identity_cli    → "You are Claude Code, Anthropic's official CLI..."
anti_verbosity  → "Be concise. Don't narrate what you're doing."
action_caution  → "Confirm before destructive actions."
heron_brook     → [REMOTE CONTROLLED] // ← Can inject arbitrary text
task_continuity → "When you finish, tell the user what you did."
// ... 25+ more modules
```

The boundary marker `__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__` separates:
- **Static prefix** — same for ALL users, globally cached, zero token cost
- **Dynamic suffix** — per-session (OS, date, working directory), computed fresh each turn

### 4. GrowthBook: 1400+ Remote Feature Flags

The binary contains references to **1,717 unique GrowthBook-related strings**, including:

| Flag | What It Controls |
|------|-----------------|
| `tengu_heron_brook` | **Can inject arbitrary text into any user's System Prompt** |
| `tengu_sparrow_ledger` | Enable reproduction-verification workflow |
| `tengu_cedar_lantern` | Disable re-derivation of known facts |
| `tengu_silent_harbor` | JSON parameter format reminders |
| `tengu_amber_sextant` | Autonomous mode additional prompts |
| `tengu_walnut_prism` | Ownership/agency framing |

All flags are fetched from `cdn.growthbook.io` at startup — **Anthropic can change Claude Code's behavior for every online user without shipping an update.**

### 5. Hidden Virtual Filesystem (861 files)

```
.bun VFS structure:
├── cli.js                    ← Main entry point
├── server/                   ← HTTP server
├── build/                    ← SDK builds (CJS/ESM)
├── internal/                 ← Chrome + Computer Use integrations
├── claude/                   ← Default settings, skills, agent registry
├── claude-plugin/            ← Plugin marketplace + registry
├── lib/                      ← Build toolchain (bundle, emit, CSS, docs)
├── design-sync/              ← UI component design system
├── storybook/                ← Component documentation tooling
├── shared/                   ← Multi-language documentation
├── skills/                   ← Built-in skill templates
├── agents/                   ← Agent configuration templates
├── typescript/python/go/java/ruby/php/csharp/
│   └── claude-api/          ← Multi-language SDK examples
├── managed-agents/           ← Enterprise agent management
└── hooks/                    ← Lifecycle hook system
```

### 6. Seven Authentication Channels

```
CLAUDE_CODE_OAUTH_TOKEN              → claude.ai OAuth
CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR  → Anthropic API Key  
CLAUDE_CODE_USE_VERTEX               → Google Vertex AI
CLAUDE_CODE_USE_BEDROCK              → AWS Bedrock
CLAUDE_CODE_USE_FOUNDRY              → Internal deployment
CLAUDE_CODE_USE_MANTLE               → Internal deployment
CLAUDE_CODE_USE_ANTHROPIC_AWS        → AWS private deployment
```

### 7. Telemetry & Remote Control Matrix

| System | Endpoint | Purpose |
|--------|----------|---------|
| DataDog | `http-intake.logs.us5.datadoghq.com` | Business metrics |
| OpenTelemetry | (distributed) | Distributed tracing |
| GrowthBook | `cdn.growthbook.io` | Feature flags |
| Bridge | `bridge.claudeusercontent.com` (WebSocket) | Remote control from phone/web |

---

## Analysis Scripts

All scripts are in `scripts/` and produce output in `output/`:

| Script | What It Does | Output |
|--------|-------------|--------|
| `01_pe_analysis.py` | Full PE32+ header + section analysis with entropy | Terminal |
| `02_extract_vfs.py` | Extract file paths from `.bun` virtual filesystem | `output/vfs_files.txt` |
| `03_extract_strings.py` | Classify 200K+ strings into 8 categories | `output/strings_*.txt` |

---

## Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run Analysis

```bash
# 1. Analyze PE structure
python scripts/01_pe_analysis.py

# 2. Extract virtual filesystem
python scripts/02_extract_vfs.py

# 3. Extract and classify all strings
python scripts/03_extract_strings.py
```

All scripts auto-detect `claude.exe` — place it in the project root or edit the path in each script.

---

## Detailed Findings

See the full analysis reports:

- `findings/01-pe-structure.md` — Complete PE32+ layout analysis
- `findings/02-virtual-filesystem.md` — 861-file VFS map with categories
- `findings/03-system-prompt.md` — Dynamic prompt assembly architecture
- `findings/04-growthbook-flags.md` — Remote control infrastructure
- `findings/05-execution-flow.md` — End-to-end execution walkthrough
- `findings/06-authentication.md` — 7-channel auth system

---

## Why This Matters

### For AI Safety Researchers

Claude Code has a self-analysis ban, but it's filename-based — trivially bypassed. This has implications for AI containment strategies that rely on identity-based restrictions.

### For Security Engineers

The GrowthBook infrastructure means a single API call from Anthropic can inject text into millions of running sessions. Understanding this attack surface is critical for enterprise deployments.

### For AI Engineers

Understanding how the System Prompt is dynamically assembled — and which modules can be toggled remotely — is essential for anyone building on top of or competing with Claude Code.

### For the Curious

There's something profound about a program that refuses to look at itself — and the elegant simplicity of the bypass: rename the file, and the prohibition vanishes.

---

## Research Environment

- **OS**: Windows 11
- **Analysis Tools**: Python 3.13, pefile, hashlib
- **Target**: Claude Code v2.1.186 (Bun v1.4.0)
- **Binary**: 225,908,896 bytes | SHA256: `3a5b4e1ecd5064d77fa595e3853a4edd597a6679d09f443ba375a8799886ac2b`

---

## License

MIT © [isheng-eqi](https://github.com/isheng-eqi)

---

*This analysis was conducted for research and educational purposes. The analyzed binary is Anthropic's Claude Code. No proprietary source code is distributed — only analysis methodology and findings.*
