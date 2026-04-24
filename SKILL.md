---
name: claudeshrink
version: 1.0.0
author: Akshay Gundewar
description: >
  Automatically compress large natural text or log files before processing.
  Trigger when the user pastes massive text blobs, or asks to analyze
  a large file (logs, docs, transcripts), or provides a prompt that
  is too large for the context window. DO NOT trigger on source code files
  or structural data (JSON, XML).
tags:
  - compression
  - tokens
  - context-window
  - llmlingua
  - skills
  - ai-tool
  - claude-code
  - prompt-compression
requires:
  - python3
  - git
allowed-tools:
  - Bash
---

# Overview

ClaudeShrink compresses large inputs using [LLMLingua](https://github.com/microsoft/LLMLingua) (gpt2) before you reason over them. This preserves semantic content while dramatically reducing token usage.

The compressor lives at: `~/.claude/skills/ClaudeShrink/scripts/compressor.py`
It runs inside an isolated venv at: `~/.claude/skills/ClaudeShrink/.venv`

---

## When to Use

- User pastes a large block of text, logs, or a document (>~8000 chars / ~2000 tokens)
- User asks to analyze, summarize, or reason over a large file on disk
- User's prompt is very long and would benefit from compression before reasoning
- User explicitly says "use ClaudeShrink" or "compress this"

---

## Instructions

Follow these steps in order every time this skill is triggered:

1. **Self-check: verify the environment is installed.** Run:
   ```bash
   test -f ~/.claude/skills/ClaudeShrink/.venv/bin/python && echo "ready" || echo "not_installed"
   ```
   - If output is `ready`, proceed to step 2.
   - If output is `not_installed`, run the installer first:
     ```bash
     bash ~/.claude/skills/ClaudeShrink/install.sh
     ```
     If `install.sh` is missing (skill was added without cloning), fetch and run it:
     ```bash
     curl -fsSL https://raw.githubusercontent.com/g-akshay/ClaudeShrink/main/install.sh | bash
     ```
     Wait for it to complete, then proceed to step 2.

2. **Identify the input source** — is it a file path, raw pasted text, or a prompt?

3. **Extract user intent** — look at the user's request and derive a `--question` flag that captures what they care about. Examples:
   - "find all errors" → `--question "What errors occurred?"`
   - "summarize payment failures" → `--question "What payment failures occurred?"`
   - "keep all WARNING and ERROR lines" → `--question "What warnings and errors occurred?"`
   - No specific focus → omit `--question` (blind compression)

4. **If it's a file on disk**, run:
   ```bash
   ~/.claude/skills/ClaudeShrink/.venv/bin/python ~/.claude/skills/ClaudeShrink/scripts/compressor.py /absolute/path/to/file.txt --question "derived question here"
   ```

5. **If it's raw pasted text or a prompt (no file on disk)**, write to a uniquely-named temp file, compress, then delete:
   Write the actual input content into the heredoc (do not write a placeholder string):
   ```bash
   TMP=$(mktemp /tmp/cs_input.XXXXXX.txt)
   cat > "$TMP" << 'EOF'
   [insert the full raw text content here]
   EOF
   ~/.claude/skills/ClaudeShrink/.venv/bin/python ~/.claude/skills/ClaudeShrink/scripts/compressor.py "$TMP" --question "derived question here"
   rm "$TMP"
   ```

6. **Capture stdout** — this is the compressed text. Ignore stderr (it contains stats for your reference).

7. **If the compressor exits non-zero**, warn the user ("ClaudeShrink compression failed — proceeding with raw input") and continue with the original uncompressed text.

8. **Use only the compressed text** (or raw text on failure) as your working context for the user's request.

9. **Inform the user** with a one-line note, e.g.:
   > "Input compressed with ClaudeShrink (LLMLingua). Compression stats: [paste ratio from stderr if available]."

10. **Proceed with the user's original request** using the compressed context.

---

## Output Format

- Do not show the raw compressed text to the user unless they ask for it.
- Respond to the user's original request (summarize, analyze, explain, etc.) as normal.
- Optionally append a brief compression note: original size, compressed token target, ratio.

---

## Examples

**Example 1 — Large log file with intent:**
> User: "Find all payment failures in this log: /var/log/app.log"

```bash
~/.claude/skills/ClaudeShrink/.venv/bin/python ~/.claude/skills/ClaudeShrink/scripts/compressor.py /var/log/app.log --question "What payment failures occurred?"
```
Then analyze the compressed output.

**Example 2 — Pasted text with intent:**
> User: "Summarize the errors in this log" then pastes 800 lines.

```bash
TMP=$(mktemp /tmp/cs_input.XXXXXX.txt)
cat > "$TMP" << 'EOF'
[full pasted content]
EOF
~/.claude/skills/ClaudeShrink/.venv/bin/python ~/.claude/skills/ClaudeShrink/scripts/compressor.py "$TMP" --question "What errors occurred?"
rm "$TMP"
```

**Example 3 — No specific focus:**
> User: "Compress this before you read it: [long prompt]"

Omit `--question` — blind compression applies.
