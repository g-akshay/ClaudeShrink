# ClaudeShrink

ClaudeShrink is a Claude Code skill that compresses large inputs using LLMLingua (gpt2) before reasoning over them, dramatically reducing token usage while preserving semantic content.

## Skill

The skill definition is in `SKILL.md`. Claude Code loads it automatically after installation.

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/g-akshay/ClaudeShrink/main/install.sh | bash
```

Installs to `~/.claude/skills/ClaudeShrink/`. The gpt2 model (~500 MB) downloads on first use.

## Usage

Claude triggers this skill automatically when it detects large inputs. You can also say:

> "Use ClaudeShrink to compress this before reading it."

## Development

- Compressor: `scripts/compressor.py`
- Tests: `tests/`
- Run tests: `bash tests/run_tests.sh`
