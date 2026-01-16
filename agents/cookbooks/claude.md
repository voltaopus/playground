# Claude Code Cookbook

## Overview
Claude Code is Anthropic's CLI for Claude. It's a powerful coding agent that can read, write, and execute code with full filesystem access.

## Invocation

```bash
# Interactive mode
claude

# With initial prompt
claude "your prompt here"

# Skip permission prompts (for automation)
claude --dangerously-skip-permissions "your prompt here"

# Resume a previous conversation
claude --resume

# With specific model
claude --model sonnet "your prompt"
claude --model opus "your prompt"
claude --model haiku "your prompt"
```

## Models

| Tier | Model | Use Case |
|------|-------|----------|
| Fast | haiku | Quick tasks, simple edits |
| Default | sonnet | Balanced performance |
| Heavy | opus | Complex reasoning, architecture |

## Capabilities

- Full filesystem read/write access
- Execute bash commands
- Web search and fetch
- Multi-file editing
- Git operations
- Spawn sub-agents (Task tool)
- Persistent conversation memory

## Best Practices

1. **Be specific** - Clear prompts get better results
2. **Provide context** - Point to relevant files/docs
3. **Break down tasks** - Use TodoWrite for complex work
4. **Let it explore** - Give it freedom to investigate

## Flags Reference

| Flag | Description |
|------|-------------|
| `--dangerously-skip-permissions` | Skip all permission prompts |
| `--model` | Specify model (sonnet, opus, haiku) |
| `--resume` | Resume last conversation |
| `--print` | Print mode (no interaction) |
| `--verbose` | Verbose output |

## Arena Integration

When running in the Dream Team arena:
- Output will be captured to `arena/runs/<session>.log`
- Results are compared against other agents
- Knowledge is persisted to `playground/library/`
