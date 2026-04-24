---
name: claudeshrink
version: 1.0.0
author: akshaygundewar
description: >
  Automatically compress large text, files, or prompts before processing.
  Trigger when the user pastes a large block of text or code, asks to analyze
  a large file (logs, docs, transcripts, source), or provides a prompt that
  is too large or token-heavy for the context window.
tags:
  - compression
  - tokens
  - context-window
  - llmlingua
requires:
  - python3
  - git
allowed-tools:
  - Bash
---

# Overview

ClaudeShrink compresses large inputs using [LLMLingua](https://github.com/microsoft/LLMLingua) (microsoft/phi-2) before you reason over them. This preserves semantic content while dramatically reducing token usage.

The compressor lives at: `~/.claude/skills/ClaudeShrink/scripts/compressor.py`  
It runs inside an isolated venv at: `~/.claude/skills/ClaudeShrink/.venv`

---

## When to Use

- User pastes a large block of text, code, logs, or a document (>200 lines)
- User asks to analyze, summarize, or reason over a large file on disk
- User's prompt is very long and would benefit from compression before reasoning
- User explicitly says "use ClaudeShrink" or "compress this"

---

## Instructions

Follow these steps in order every time this skill is triggered:

1. **Identify the input source** — is it a file path, raw pasted text, or a prompt?

2. **If it's a file on disk**, run:
   ```bash
   ~/.claude/skills/ClaudeShrink/.venv/bin/python ~/.claude/skills/ClaudeShrink/scripts/compressor.py /absolute/path/to/file.txt
   ```

3. **If it's raw pasted text or a prompt (no file on disk)**, write to a temp file first, then compress, then delete:
   ```bash
   cat > /tmp/cs_input.txt << 'EOF'
   <paste the raw text here>
   EOF
   ~/.claude/skills/ClaudeShrink/.venv/bin/python ~/.claude/skills/ClaudeShrink/scripts/compressor.py /tmp/cs_input.txt
   rm /tmp/cs_input.txt
   ```

4. **Capture stdout** — this is the compressed text. Ignore stderr (it contains stats for your reference).

5. **Use only the compressed text** as your working context for the user's request.

6. **Inform the user** with a one-line note, e.g.:
   > "Input compressed with ClaudeShrink (LLMLingua). Compression stats: [paste ratio from stderr if available]."

7. **Proceed with the user's original request** using the compressed context.

---

## Output Format

- Do not show the raw compressed text to the user unless they ask for it.
- Respond to the user's original request (summarize, analyze, explain, etc.) as normal.
- Optionally append a brief compression note: original size, compressed token target, ratio.

---

## Examples

**Example 1 — Large log file:**
> User: "Analyze this error log: /var/log/app.log"

```bash
~/.claude/skills/ClaudeShrink/.venv/bin/python ~/.claude/skills/ClaudeShrink/scripts/compressor.py /var/log/app.log
```
Then analyze the compressed output.

**Example 2 — Pasted text:**
> User pastes 800 lines of documentation inline.

Write it to `/tmp/cs_input.txt`, compress, delete, analyze.

**Example 3 — Explicit trigger:**
> User: "Use ClaudeShrink on this prompt before answering: [long prompt]"

Same as Example 2.
