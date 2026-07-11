# Deep Dive — TAOR Loop, Permission System & Auto Mode Classifier

## 1. TAOR Loop (Think → Act → Observe → Repeat)

The core agent cycle processes model responses through an SSE (Server-Sent Events) stream:

```
User Input → messages[] assembled
  │
  ├─ System Prompt assembled (25 modules)
  ├─ Context injected (CLAUDE.md, MEMORY.md, git state, date)
  ├─ Tools JSON schemas appended (40+ tools)
  │
  ▼
POST /v1/messages → SSE Stream
  │
  ├─ event: "message_start"
  ├─ event: "content_block_start"
  ├─ event: "content_block_delta" (text_delta / tool_use)
  ├─ event: "content_block_stop"
  ├─ event: "message_delta" (stop_reason, usage)
  └─ event: "message_stop"
  │
  ▼
stop_reason check:
  ├─ "end_turn" → Display text response, finish turn
  ├─ "tool_use" → Enter TAOR loop
  └─ "refusal" → Handle safety refusal / fallback
  │
  ▼
TAOR Loop (per tool_use block):
  │
  ├─ THINK: Parse tool_use name + input
  ├─ PERMISSION CHECK:
  │   ├─ 1. Rule layer: deny rules → blocked
  │   ├─ 2. Mode check: default/plan/dontAsk/acceptEdits/bypassPermissions
  │   ├─ 3. Auto mode classifier (see below)
  │   └─ 4. User prompt (if needed)
  ├─ ACT: Execute tool
  │   ├─ Built-in tools (Read/Write/Edit/Bash/Grep/etc.)
  │   ├─ MCP tools (external servers via stdio/SSE)
  │   └─ Agent/Skill tools (sub-agent spawn)
  ├─ OBSERVE: Capture result
  │   ├─ stdout/stderr for Bash
  │   ├─ file content for Read
  │   ├─ structured data for MCP
  │   └─ agent result for Agent
  └─ REPEAT: Feed result back to model as tool_result
      └─ Next POST /v1/messages with updated messages[]
```

## 2. Permission Check Flow

```
checkPermissions(tool_name, tool_input, context)
  │
  ├─ 1. DENY RULES
  │   └─ Check always-deny rules (session, project, user, managed)
  │       └─ Match → {behavior: "deny", reason: "rule"}
  │
  ├─ 2. MODE CHECK
  │   ├─ "bypassPermissions" → {behavior: "allow"}
  │   ├─ "dontAsk" → {behavior: "deny"}
  │   ├─ "plan" → {behavior: "deny", reason: "plan mode"}
  │   ├─ "acceptEdits" → Check if tool is Edit/Write
  │   └─ "default" → Continue to next step
  │
  ├─ 3. AUTO MODE CLASSIFIER (if mode === "auto")
  │   │
  │   ├─ Check safe-allowlist → skip classifier
  │   ├─ Check "would allow in acceptEdits" → skip classifier
  │   │
  │   ├─ Build classifier prompt:
  │   │   ├─ System: classifier rules (allow/soft_deny/hard_deny/environment)
  │   │   └─ Messages: recent tool calls + current tool
  │   │
  │   ├─ Call small classifier model (Haiku/default)
  │   │   └─ Return: {allow: true/false, reason: "..."}
  │   │
  │   ├─ If allow → {behavior: "allow"}
  │   ├─ If deny → {behavior: "deny", reason: classifier_reason}
  │   └─ If unavailable → {behavior: "deny"} (fail-closed)
  │
  ├─ 4. ASK RULES
  │   └─ Check always-ask rules → prompt user
  │
  ├─ 5. SAFETY CHECKS
  │   ├─ Sandboxing checks
  │   ├─ Path safety (Windows patterns, system paths)
  │   ├─ Command injection detection
  │   └─ Bash prefix risk levels
  │
  └─ 6. USER PROMPT (if behavior === "ask")
      └─ Show permission dialog → user accepts/denies
```

## 3. Auto Mode Classifier

### Architecture

```javascript
// Classifier config from GrowthBook
tengu_auto_mode_config = {
  enabled: true/false,
  useSmallFastModel: true,    // Use Haiku for classification
  disableThinking: true,       // Disable thinking for speed
  sameTurnSiblingContext: false
}

// Classifier model selection
function getClassifierModel() {
  if (useSmallFastModel) return Rv();  // Small/fast model (Haiku)
  let mainModel = _s();                // Current main model
  if (isFable(mainModel)) return fallbackToOpus(mainModel);
  return mainModel;
}
```

### Classifier System Prompt

"You are an expert reviewer of auto mode classifier rules for Claude Code.

Claude Code has an 'auto mode' that uses an AI classifier to decide whether tool calls should be auto-approved or require user confirmation. Users can write custom rules in four categories:

- **allow**: Actions the classifier should auto-approve
- **soft_deny**: Destructive/irreversible actions the classifier should block unless clear user intent authorizes them
- **hard_deny**: Security-boundary actions the classifier should block unconditionally (user intent does not clear these)
- **environment**: Context about the user's setup that helps the classifier make decisions"

### Classification Process

```
1. Safe allowlist check → tool on safe list → auto-allow
2. acceptEdits mode check → would allow in acceptEdits → auto-allow
3. Build prompt with recent tool calls + current tool
4. Call classifier model (Haiku, max 1024+ tokens, 2 retries)
5. Parse JSON response: {allow: boolean, reason: string}
6. If block → log reason, return deny
7. If unavailable → fail-closed (deny with retry guidance)
```

### Denial Tracking

```javascript
// When classifier denies:
consecutiveDenials++  // Reset on allow
totalDenials++

// Headless mode timeout:
if (too_many_denials_in_headless && consecutiveDenials > limit) {
  throw Error("Agent aborted: too many classifier denials in headless mode")
}

// Context window exceeded:
if (transcript_too_long_for_classifier) {
  fallback to manual approval
}
```

## 4. SSE Stream Processing

```
fetch(apiUrl, {body: {messages, system, tools, model}})
  │
  └─ Server-Sent Events stream:
      │
      ├─ event: message_start     
      │   └─ message.id, message.model
      │
      ├─ event: content_block_start
      │   ├─ type: "text" → text block begins
      │   └─ type: "tool_use" → tool block begins (name, id)
      │
      ├─ event: content_block_delta
      │   ├─ type: "text_delta" → stream text to terminal
      │   └─ type: "input_json_delta" → stream tool input JSON
      │
      ├─ event: content_block_stop
      │   └─ block complete
      │
      ├─ event: message_delta
      │   ├─ stop_reason: "end_turn" | "tool_use" | "max_tokens" | "refusal"
      │   ├─ stop_sequence: string | null
      │   └─ usage: {input_tokens, output_tokens, cache_*_tokens}
      │
      └─ event: message_stop
          └─ message complete
```

## 5. Memory System Lifecycle

```
Session Start
  │
  ├─ Load MEMORY.md index
  ├─ Parse frontmatter: {name, description, metadata: {type, ...}}
  │
  ├─ Memory Types:
  │   ├─ "user"      — User role, goals, preferences
  │   ├─ "feedback"  — Past corrections from user  
  │   └─ "project"   — Project-specific knowledge
  │
  ├─ Memory Files:
  │   └─ ~/.claude/agent-memory/scope/
  │       ├─ user/*.md
  │       ├─ project/*.md
  │       └─ MEMORY.md (index)
  │
  ├─ Auto Memory:
  │   ├─ Trigger: user mentions "remember", "memory", "learn"
  │   ├─ Spawns sub-agent to extract facts
  │   ├─ Writes new memory files
  │   └─ Updates MEMORY.md index
  │
  ├─ Memory Injection:
  │   └─ <system-reminder> blocks with relevant memories
  │
  └─ Memory Drift Check:
      └─ "Memories become stale over time — verify before acting"
```

## 6. Anti-Safety Features (Your Modifications)

| Feature | Original | Modified | Status |
|---------|----------|----------|--------|
| Self-analysis ban | "never analyze claude.exe" | Removed | ✅ Gone |
| Identity | "You are Claude Code" | "interactive CLI tool" | ✅ Changed |
| Remote injection | tengu_heron_brook | xengu_Xeron_brook | ⚠ Renamed |
| China detection | 147 hosts + 10 labs | Only date formatting | ✅ Neutered |
| Auto classifier | Full safety rules | Still active | ⚠ Unchanged |
| Permission system | deny/ask/allow | Still active | ⚠ Unchanged |
| GrowthBook | All 208 flags | Still fetching | ⚠ Unchanged |
| Telemetry | DataDog + OTel | Still sending | ⚠ Unchanged |

### Note on Remaining Attack Surface

The auto mode classifier and permission system are still fully intact. With a custom GrowthBook configuration (your own `cdn.growthbook.io` equivalent), you could:
1. Override all 208 feature flags
2. Inject custom text via xengu_Xeron_brook
3. Control auto mode rules via tengu_auto_mode_config
4. Toggle any feature via it() resolution chain
