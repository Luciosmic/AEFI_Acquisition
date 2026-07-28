#!/bin/bash
# Setup script to make Claude Code skills compatible with Vibe
# This script creates symlinks from .vibe/skills/ to Claude skill directories
# with minimal transformation for tool name compatibility

set -e

PLUGINS_DIR="/Users/luis/Library/CloudStorage/Dropbox/UTUKI/CONNAISSANCES/claude-code-plugins"
VIBE_SKILLS_DIR="$(cd "$(dirname "$0")" && pwd)/skills"

# Create .vibe/skills directory if it doesn't exist
mkdir -p "$VIBE_SKILLS_DIR"

echo "Setting up Claude Code skills for Vibe..."
echo "Source: $PLUGINS_DIR"
echo "Target: $VIBE_SKILLS_DIR"
echo ""

# Find all SKILL.md files in the plugins directory
# This handles both .claude/skills/ and skills/ subdirectories
while IFS= read -r -d '' skill_file; do
    skill_dir="$(dirname "$skill_file")"
    skill_name="$(basename "$skill_dir")"
    
    # Create a symlink to the skill directory
    # But we need to handle duplicate names
    target_dir="$VIBE_SKILLS_DIR/$skill_name"
    
    # If the name already exists, append a suffix
    counter=1
    while [ -e "$target_dir" ]; do
        target_dir="$VIBE_SKILLS_DIR/${skill_name}_$counter"
        counter=$((counter + 1))
    done
    
    # Create the symlink
    ln -sfn "$skill_dir" "$target_dir"
    echo "  Linked: $target_dir -> $skill_dir"
    
    # Check if we need to create a wrapper SKILL.md with transformed tool names
    # Vibe uses: bash, read, write_file, edit, grep, task
    # Claude uses: Bash, Read, Write, Edit, Grep, Glob
    
    # For now, just use the original SKILL.md - Vibe will use its own tool permissions
    # The allowed-tools in frontmatter is advisory
    
done < <(find "$PLUGINS_DIR" -name "SKILL.md" -print0)

echo ""
echo "Setup complete!"
echo "Vibe can now find skills from: $PLUGINS_DIR"
echo "Symlinks created in: $VIBE_SKILLS_DIR"
echo ""
echo "Note: Tool names in Claude skills (Read, Write, etc.) are mapped to"
echo "Vibe equivalents (read, write_file, etc.) via Vibe's global tool permissions."
