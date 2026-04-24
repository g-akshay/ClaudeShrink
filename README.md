# ClaudeShrink

A Claude Code skill that shrinks massive prompts and files using LLMLingua to save tokens.

This skill enables Claude Code to handle massive files (logs, documentation, long traces) by compressing them using [LLMLingua](https://github.com/microsoft/LLMLingua). It uses the `gpt2` model locally on your CPU to reduce text size while maintaining semantic integrity, significantly saving context window tokens.

## Installation

Run this one-liner in your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/g-akshay/ClaudeShrink/main/install.sh | bash
```

This will:
1. Clone the repo into `~/.claude/skills/ClaudeShrink`
2. Create an **isolated Python venv** (no system pollution)
3. Install `llmlingua`, `torch`, `transformers`, and `accelerate`

> **Requirements:** Python 3.9+ and `git` must be on your PATH.
> - macOS: install Python via `brew install python` or [python.org](https://www.python.org/downloads/)
> - Linux (Ubuntu/Debian): `sudo apt install python3 git` — `python3-venv` is auto-handled by the installer
>
> **Note:** The `gpt2` model (~500 MB) is downloaded on **first use**, not at install time.

### Updating

To update to the latest version, simply run the exact same command again. It is designed to be safe, additive, and will pull the latest code without destroying your environment:

```bash
curl -fsSL https://raw.githubusercontent.com/g-akshay/ClaudeShrink/main/install.sh | bash
```

## How to Trigger

Claude will automatically use this skill when it detects a request to process a large file. You can also explicitly trigger it by asking:

> "Use the ClaudeShrink skill to read ./very_large_log.log and summarize the errors."

## Configuration

Defaults in `scripts/compressor.py`:

| Setting | Default | Notes |
|---|---|---|
| **Model** | `gpt2` | Lightweight, CPU-friendly |
| **Device** | `cpu` | Change to `cuda` if you have a GPU |
| **Target Tokens** | Auto (30% of input, 512–4096) | Adaptive — no manual tuning needed |

Edit `~/.claude/skills/ClaudeShrink/scripts/compressor.py` to override.

## Platform Support

| Platform | Supported | Notes |
|---|---|---|
| macOS | ✅ | Intel + Apple Silicon |
| Linux | ✅ | Ubuntu, Debian (auto-installs `python3-venv`), Fedora, Arch |
| Windows | ⚠️ | Via [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) (Ubuntu recommended) only |