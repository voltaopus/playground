# Codex CLI Cookbook

## Overview
Codex CLI is OpenAI's coding agent that runs locally. It can read, edit, and execute code while keeping your source code local.

## Installation

```bash
# NPM
npm i -g @openai/codex

# Homebrew (macOS)
brew install --cask codex
```

## Authentication

First run prompts for ChatGPT account or API key login.
- ChatGPT Plus/Pro/Team subscription includes Codex access
- Or use OpenAI API credits

## Invocation

```bash
# Interactive mode
codex

# With prompt
codex "your prompt here"

# Specific model
codex -m gpt-4.1 "your prompt"

# Full automation mode
codex --full-auto "your prompt"

# Bypass approvals and sandbox
codex --dangerously-bypass-approvals-and-sandbox "your prompt"
```

## Models

| Tier | Model | Use Case |
|------|-------|----------|
| Fast | gpt-4.1-mini | Quick tasks |
| Default | gpt-4.1 | Balanced |
| Heavy | o3 | Complex reasoning |

## Key Flags

| Flag | Description |
|------|-------------|
| `-m`, `--model` | Specify model |
| `--full-auto` | Full automation mode |
| `--dangerously-bypass-approvals-and-sandbox` | Skip all safety prompts |
| `/model` | Switch models mid-session |

## Capabilities

- Local code execution
- File read/write
- Command execution
- Code generation and editing
- Project understanding

## Configuration

Config file: `~/.codex/config.toml`

```toml
[defaults]
model = "gpt-4.1"
approval_policy = "auto"

[sandbox]
enabled = false
```

## Arena Integration

When spawned by the Dream Team orchestrator:
```bash
codex -m {model} --dangerously-bypass-approvals-and-sandbox "{prompt}"
```

Output captured to `arena/runs/<session>.log`
