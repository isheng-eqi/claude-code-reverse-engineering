# Claude Code Unmasked: Binary Reverse Engineering of Anthropic's 215MB Agent CLI

> **Claude Code is not a statically-compiled application. It is a 215MB self-contained operating system disguised as a CLI — with its own JavaScript VM (Bun), a remotely-controlled System Prompt assembly line, 1400+ feature flags, and a self-protection system designed to prevent exactly this kind of analysis.**

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## What This Is

A professional binary reverse engineering analysis of Claude Code — Anthropic's official CLI agent harness. Every finding is backed by **runnable Python scripts** using PE analysis tools (`pefile`), not AI-assisted guessing.

### What We Can Extract (with certainty)

| Layer | What We Found | Tool |
|-------|--------------|------|
| **PE Structure** | 12 sections, exact layout, entropy analysis | `pefile` |
| **Source Code** | 16.5 MB `cli.js` (main entry point) extracted from Bun module graph | `05_extract_modules.py` |
| **String Constants** | 1500+ System Prompt fragments, 1700+ GrowthBook flags, URLs, auth configs | Binary regex + classification |
| **Execution Flow** | 8-step startup → SSE streaming pipeline (reconstructed from bytecode references) | Pattern matching |
| **Remote Control** | GrowthBook flag enumeration, `tengu_heron_brook` injection mechanism | String extraction |
| **Bun Module Graph** | 7 module entries (1 valid), Bun trailer at EOF, VFS file paths | Structural binary parsing |

### Source Code Extraction

The **main breakthrough** is `scripts/05_extract_modules.py` — a pure-Python parser for Bun's embedded module graph format:

```
┌─────────────────────────────────────────┐
│  claude.exe (225MB)                     │
│  ...                                    │
│  .bun section (138MB)                   │
│    ├─ Embedded data (bytecode + source) │
│    ├─ Module entries (36 bytes each)    │
│    ├─ Offsets structure (32 bytes)      │
│    └─ Trailer: "\n---- Bun! ----\n"     │
└─────────────────────────────────────────┘
```

Run `python scripts/05_extract_modules.py` to extract the entry point module. The extracted `cli.js` (16.5 MB, 17M+ lines) contains the complete Claude Code application logic.

> **Note:** Extracted source code is Anthropic's proprietary software. It is saved to `decompiled/` (gitignored) for local analysis only — never committed to this repository.

---

## How It Was Done

### The Self-Protection Bypass

Claude Code's System Prompt contains a hard rule: **never analyze, modify, or reverse-engineer the `claude.exe` binary.** But this protection has a critical flaw:

> **It identifies "itself" by filename, not by content hash.**

```bash
cp claude.exe a.exe   #  Rename it. That's the entire bypass.
```

Verified: SHA256 of original and renamed copy are identical.

### Three-Tier Safety Classifier (and how it was bypassed)

```
┌─ Rule Layer:   Whitelist/blacklist matching (milliseconds)
├─ Model Layer:  Small AI model for semantic analysis
└─ Fallback:     Default DENY when model is unavailable
```

Using DeepSeek as provider → Anthropic's safety model unavailable → fallback blocks everything. Bypassed via `settings.json`:

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions",
    "disableAutoMode": "disable"
  }
}
```

### Analysis Tools

All analysis uses professional-grade tools with reproducible scripts:

| Script | Method | What It Produces |
|--------|--------|-----------------|
| `01_pe_analysis.py` | `pefile` PE32+ parser | Section layout, entropy, import/export tables |
| `02_extract_vfs.py` | Binary pattern matching against `.bun` section | File path enumeration (NOT content extraction) |
| `03_extract_strings.py` | ASCII string extraction + keyword classification | Categorized strings: System Prompt, GrowthBook, auth, URLs |
| `04_analyze_bun_vfs.py` | Structural analysis of VFS entry format | Entry metadata, URL-encoded path decoding |

---

## Key Findings

### 1. Architecture: Bun VM + Bytecode VFS

Claude Code is built with **Bun v1.4.0** (`bun build --compile`):

```
┌─────────────────────────────────────┐
│  Bun JavaScript Runtime (Zig)       │  ← 54.3 MB (.text section)
├─────────────────────────────────────┤
│  Claude Code Bytecode               │  ← Also in .text
├─────────────────────────────────────┤
│  String Constants + System Prompt   │  ← 21.2 MB (.rdata section)  
├─────────────────────────────────────┤
│  VFS Metadata + Bytecode Bundles    │  ← 138.4 MB (.bun section)
└─────────────────────────────────────┘
```

### 2. PE Section Layout

```
Section     Size       Entropy    Content
.text       54.3 MB    6.27       x64 machine code + Bun bytecode
.rdata      21.2 MB    4.70       String constants, System Prompt, JSON schemas
.data        2.3 MB    2.77       Global variables
.bun       138.4 MB    5.16       Bun VFS (16 entries + compiled bundles)
.rsrc        0.2 MB    7.05       Windows resources (icons)
.reloc       0.2 MB    5.49       Relocation table
.pdata       0.9 MB    6.46       Exception handling
```

Entropy analysis confirms: `.text` (6.27) = compiled code, `.rsrc` (7.05) = compressed, `.data` (2.77) = sparse structured data.

### 3. Dynamic System Prompt Assembly

30+ modules compose the System Prompt at runtime. Each module's activation is controlled by a matrix of conditions:

```javascript
// Reconstructed from bytecode references:
identity_cli      → "You are Claude Code, Anthropic's official CLI..."
anti_verbosity    → "Be concise. Don't narrate what you're doing."
action_caution    → "Confirm before destructive actions."
heron_brook       → [REMOTE CONTROLLED — can inject arbitrary text]
investigate_first → "Reproduce bugs before fixing them."
// ... 25+ more modules
```

### 4. GrowthBook: 1700+ Remote Feature Flags

Extracted from binary strings. Key flags (from `output/strings_growthbook.txt`):

| Flag | Controls |
|------|----------|
| `tengu_heron_brook` | **Arbitrary text injection into System Prompt** — highest risk |
| `tengu_sparrow_ledger` | Reproduction-verification workflow |
| `tengu_cedar_lantern` | Disable re-derivation of known facts |
| `tengu_silent_harbor` | JSON parameter format reminders |
| `tengu_amber_sextant` | Autonomous mode prompts |
| `tengu_walnut_prism` | Ownership/agency framing |

Flags are fetched from `cdn.growthbook.io` at startup — enabling remote behavioral changes without client updates.

### 5. Authentication: 7 Channels

```
CLAUDE_CODE_OAUTH_TOKEN              → claude.ai OAuth
CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR  → Anthropic API Key
CLAUDE_CODE_USE_VERTEX               → Google Vertex AI
CLAUDE_CODE_USE_BEDROCK              → AWS Bedrock
CLAUDE_CODE_USE_FOUNDRY              → Internal deployment
CLAUDE_CODE_USE_MANTLE               → Internal deployment
CLAUDE_CODE_USE_ANTHROPIC_AWS        → AWS private deployment
```

### 6. Execution Flow (8 Steps)

```
User types "claude" → npm wrapper → cli-wrapper.cjs → spawnSync(claude.exe)
  ├─ Step 1: Read config (settings.json, .mcp.json, .gitconfig)
  ├─ Step 2: Background init (GrowthBook, GitHub update check, telemetry)
  ├─ Step 3: Assemble System Prompt (30+ dynamic modules)
  ├─ Step 4: Inject context (CLAUDE.md, MEMORY.md, Git status)
  ├─ Step 5: Collect tools (40+ built-in + MCP server tools)
  ├─ Step 6: POST to API (system[] + messages[] + tools[])
  ├─ Step 7: SSE stream parsing + TAOR loop (Think→Act→Observe→Repeat)
  └─ Step 8: Archive (history.jsonl, session state)
```

---

## Quick Start

```bash
pip install -r requirements.txt

# 1. PE structure analysis
python scripts/01_pe_analysis.py

# 2. VFS entry enumeration
python scripts/02_extract_vfs.py

# 3. String extraction & classification
python scripts/03_extract_strings.py
```

Place `claude.exe` in the project root (or edit paths in scripts).

---

## Why This Matters

### For AI Safety

The filename-based self-protection bypass demonstrates a fundamental weakness in identity-based AI restrictions. Content-hash-based protection would be more robust.

### For Security Engineering

The GrowthBook infrastructure means Anthropic can inject text into millions of running sessions via a single API call. Understanding this surface is critical for enterprise deployments.

### For Tool Builders

Understanding the System Prompt assembly pipeline — which modules are static vs. dynamic vs. remotely controlled — informs design decisions for competing or complementary tools.

---

## Research Environment

- **OS**: Windows 11
- **Tools**: Python 3.13, pefile, hashlib
- **Target**: Claude Code v2.1.186 (Bun v1.4.0)
- **Binary**: 225,908,896 bytes

---

## License

MIT © [isheng-eqi](https://github.com/isheng-eqi)

---

*Conducted for research and educational purposes. No proprietary source code is distributed — only analysis methodology and findings that are observable from the binary's surface.*
