# Modification Analysis — What Was Changed in This Binary

## Summary

The analyzed `claude.exe` (SHA256: `3a5b4e...`) differs from the original npm-distributed binary (SHA256: `6a286f...`). Through byte-level comparison of the Bun module graph, string extraction, and VFS structure analysis, the following modifications were identified:

## 1. GrowthBook Flag Rename

| Original | Modified |
|----------|----------|
| `tengu_heron_brook` | `xengu_Xeron_brook` |

This is the **only** renamed GrowthBook flag — all other 1428 `tengu_*` flags remain unchanged.

### What heron_brook Does

The `heron_brook` module can inject **arbitrary text into the System Prompt** of every running Claude Code instance. The original binary reads from:
1. `It().clientDataCache?.tengu_heron_brook` (client-side cache)
2. `it("tengu_heron_brook", "")` (GrowthBook flag fallback)

The modified version reads from:
1. `It().clientDataCache?.xengu_Xeron_brook` (client-side cache — NEW priority)
2. `it("xengu_Xeron_brook", "")` (GrowthBook flag fallback — different key)

**Implication**: The modification **changes which GrowthBook flag key controls the arbitrary text injection**. This could serve to:
- Isolate from Anthropic's production GrowthBook configuration
- Create a custom injection channel
- Prevent remote control by the original `tengu_heron_brook` key

## 2. Bun Module Graph Disruption

The module graph at the end of the binary has been altered:

| Field | Expected | Found |
|-------|----------|-------|
| modulesPtr.length | ~7632 bytes (212+ modules × 36) | 260 bytes (7 modules) |
| Valid modules | 212+ | 1 |

Only **1 of 7 module entries** is valid (the entry point `cli.js`). The remaining entries contain corrupted pointers that extend beyond the file boundary.

This is why `bun-decompile` (the standard extraction tool) fails with "Corrupt module graph".

## 3. Section Name Cleanup

The original binary's PE sections had obfuscated/garbled names in the first few sections. The modified binary has clean, standard section names:

| Section | Original (article) | Modified |
|---------|-------------------|----------|
| Various | Garbled/unnamed | `.text`, `.rdata`, `.data`, etc. |
| `.bun` | Unnamed (138MB section) | `.bun` |

## 4. Content Differences (String Analysis)

The modified binary contains:
- 1429 unique `tengu_*` telemetry flags (vs ~1418 in original)
- Added: `xengu_Xeron_brook` and `xengu_Xeron_brook_applied` (2 new flags)
- Missing: `identity_cli` module name (was present in original article)
- The identity text "You are Claude Code" does NOT appear as plain text (compiled to bytecode)

## Verification

To verify these modifications against an unmodified binary:
```bash
# Compare SHA256
sha256sum original_claude.exe modified_claude.exe

# Compare Bun trailers
python scripts/05_extract_modules.py original_claude.exe

# Compare GrowthBook flags
python scripts/03_extract_strings.py  # then diff output/strings_growthbook.txt
```
