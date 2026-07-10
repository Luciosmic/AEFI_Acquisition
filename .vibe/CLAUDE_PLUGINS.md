# Using Claude Code Plugins with Vibe

## Overview

This repository is configured to use **both Claude Code and Mistral Vibe** with shared skills/plugins from the central plugins directory.

## Current Setup

The Vibe configuration (`.vibe/config.toml`) includes the Claude Code plugins directory in its `skill_paths`:

```toml
[skills]
skill_paths = [
    "/Users/luis/Library/CloudStorage/Dropbox/UTUKI/CONNAISSANCES/claude-code-plugins",
]
```

This allows Vibe to **discover and load Claude skills directly** without any file duplication.

## How It Works

### Skill Discovery

Vibe's skill system searches for directories containing `SKILL.md` files in the following order:

1. Paths in `skill_paths` from config.toml (✅ Our plugins directory)
2. `.vibe/skills/` in the project
3. `.agents/skills/` in the project  
4. User-level skill directories

### Tool Name Compatibility

| Claude Tool | Vibe Equivalent | Status |
|-------------|-----------------|---------|
| `Read` | `read` | ✅ Mapped via global permissions |
| `Write` | `write_file` | ✅ Mapped via global permissions |
| `Edit` | `edit` | ✅ Mapped via global permissions |
| `Bash` | `bash` | ✅ Mapped via global permissions |
| `Grep` | `grep` | ✅ Mapped via global permissions |
| `Glob` | - | ⚠️ No direct equivalent (use `grep` patterns) |
| `mcp_*` | - | ⚠️ MCP-specific (not available in Vibe by default) |

**Important**: The `allowed-tools` in a skill's SKILL.md frontmatter is **advisory**. Vibe uses its **global tool permissions** from `config.toml` as the source of truth. Skills will work as long as the corresponding tools are enabled in Vibe's configuration.

## Usage

### Option 1: Direct Usage (Recommended)

Vibe will automatically discover skills from the plugins directory. Just invoke them:

```
/skill arscontexta:refactor
/skill solidai-domain-modeling
```

### Option 2: Setup Symlinks (For Better Organization)

Run the setup script to create symlinks in `.vibe/skills/`:

```bash
.vibe/setup-claude-skills.sh
```

This creates symlinks like:
```
.vibe/skills/arscontexta-refactor -> /Users/.../claude-code-plugins/solidai/.claude/skills/arscontexta-refactor
.vibe/skills/solidai-domain-modeling -> /Users/.../claude-code-plugins/solidai/.claude/skills/solidai-domain-modeling
```

### Option 3: Add Specific Plugin Directories

If you want to add specific plugin directories (not the entire collection), update `.vibe/config.toml`:

```toml
[skills]
skill_paths = [
    "/Users/luis/Library/CloudStorage/Dropbox/UTUKI/CONNAISSANCES/claude-code-plugins/solidai",
    "/Users/luis/Library/CloudStorage/Dropbox/UTUKI/CONNAISSANCES/claude-code-plugins/solidwriting",
]
```

## Tool Name Translation

Claude skills may reference tools like `Read`, `Write`, `Grep` which don't exactly match Vibe's tool names (`read`, `write_file`, `grep`). 

**Vibe handles this gracefully**:
- Tool permissions are controlled globally in `[tools]` section of `config.toml`
- The skill's `allowed-tools` frontmatter doesn't restrict Vibe's behavior
- Vibe will use its own tool name resolution

If a skill tries to use a tool that's disabled in Vibe's config, it will be denied (unless `bypass_tool_permissions = true`).

## Compatibility Notes

### ✅ Works Perfectly
- Skill discovery and loading
- Basic tool usage (read, write_file, edit, bash, grep)
- YAML frontmatter parsing
- Skill invocation via `/skill` command

### ⚠️ May Need Attention
- **`Glob` tool**: Claude has a `Glob` tool for file pattern matching. Vibe doesn't have this exact tool, but `grep` with patterns can achieve similar results.
- **MCP tools**: Claude skills using MCP server tools (e.g., `mcp__qmd__search`) won't work in Vibe unless you configure the same MCP servers.

### 🔧 Configuration Tips

If you encounter tool permission issues:

1. **Enable the tool globally** in `.vibe/config.toml`:
   ```toml
   [tools]
   enabled_tools = ["bash", "read", "write_file", "edit", "grep", "todo", "task"]
   ```

2. **Or bypass tool permissions** (not recommended for security):
   ```toml
   bypass_tool_permissions = true
   ```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  /Users/luis/Library/CloudStorage/Dropbox/UTUKI/CONNAISSANCES/ │
│  claude-code-plugins/                                        │
│  ├── solidai/                                               │
│  │   └── .claude/skills/                                   │
│  │       ├── arscontexta-refactor/                        │
│  │       │   └── SKILL.md  ◄──┐                            │
│  │       └── solidai-domain-modeling/                    │
│  │           └── SKILL.md  ◄──┘                            │
│  └── solidwriting/                                         │
│      └── .claude/skills/                                   │
│          └── ...                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  AEFI_Acquisition/.vibe/config.toml                         │
│  skill_paths = ["/Users/.../claude-code-plugins"]             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Vibe discovers and loads skills
```

## Dual Agent Workflow

Both agents can use the same plugins:

**Claude Code:**
- Uses `.claude/settings.json` and its own hook system
- Loads plugins from `.claude/skills/` directories
- Uses VSCode extension

**Mistral Vibe:**
- Uses `.vibe/config.toml` and its hook system
- Discovers skills via `skill_paths` configuration
- Uses terminal-based CLI

Both can coexist and share the same skill definitions without conflicts.

## Troubleshooting

### Skills not appearing in Vibe

1. Check Vibe is trusted in the project:
   ```bash
   vibe --trust
   ```

2. Verify the skill directory structure:
   ```bash
   find /Users/luis/Library/CloudStorage/Dropbox/UTUKI/CONNAISSANCES/claude-code-plugins -name "SKILL.md"
   ```

3. Check Vibe's skill loading:
   ```
   /skill list  # (if available in your Vibe version)
   ```

### Tool permission errors

Add the required tools to `[tools.enabled_tools]` in `.vibe/config.toml`:

```toml
[tools]
enabled_tools = ["bash", "read", "write_file", "edit", "grep", "todo", "task"]
```

## Summary

✅ **Minimal additions**: Only config.toml update and optional setup script  
✅ **Maximum decoupling**: No modifications to existing skill files  
✅ **Dual agent support**: Both Claude and Vibe work with the same plugins  
✅ **Tool compatibility**: Vibe's global permissions handle tool name differences  
