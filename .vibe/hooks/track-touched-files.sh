#!/bin/bash
# Vibe after_tool hook — track files touched in this session
# This replaces Claude's PostToolUse hook for Write|Edit
# Vibe hooks receive JSON on stdin with different schema

DATA=$(cat)

# Extract session_id and file_path from Vibe's hook payload
SESSION_ID=$(echo "$DATA" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('session_id', 'unknown'))
" 2>/dev/null || echo "unknown")

FILE_PATH=$(echo "$DATA" | python3 -c "
import json, sys
d = json.load(sys.stdin)
tool_input = d.get('tool_input', {})
print(tool_input.get('file_path', ''))
" 2>/dev/null)

# Only proceed if we have a file path
[ -z "$FILE_PATH" ] && exit 0

PROJECT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Only track files within this project
case "$FILE_PATH" in
  "$PROJECT_DIR"*) ;;
  *) exit 0 ;;
esac

# Use .vibe directory instead of .claude
TRACKING_FILE="${PROJECT_DIR}/.vibe/session_touched_files_${SESSION_ID:-unknown}"
echo "$FILE_PATH" >> "$TRACKING_FILE"

exit 0
