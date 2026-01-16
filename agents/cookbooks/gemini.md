# Gemini CLI Cookbook

## Overview
Gemini CLI is Google's open-source AI agent that brings Gemini directly into your terminal. It can understand code, execute complex queries, and leverage multimodal capabilities.

## Installation

```bash
npm install -g @google/gemini-cli
```

## Authentication

First run will prompt for Google account login. Alternatively:
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

Free tier: 60 requests/minute, 1000 requests/day

## Invocation

```bash
# Interactive mode
gemini

# With prompt
gemini "your prompt here"

# Specific model
gemini --model gemini-2.5-pro "your prompt"

# Auto-approve actions
gemini -y "your prompt"
gemini --yolo "your prompt"

# Sandbox mode (Docker isolation)
gemini --sandbox "your prompt"
```

## Models

| Tier | Model | Use Case |
|------|-------|----------|
| Fast | gemini-2.5-flash | Quick responses |
| Default | gemini-2.5-pro | Balanced |
| Heavy | gemini-2.5-pro | Complex tasks |

## Key Flags

| Flag | Description |
|------|-------------|
| `-y`, `--yolo` | Auto-approve all actions |
| `--model` | Specify model |
| `--sandbox` | Run in Docker sandbox |
| `-i` | Interactive mode |

## Capabilities

- Code understanding and generation
- File system operations
- Command execution
- Multimodal input (images, etc.)
- Web browsing

## Arena Integration

When spawned by the Dream Team orchestrator:
```bash
gemini --model {model} -y "{prompt}"
```

Output captured to `arena/runs/<session>.log`
