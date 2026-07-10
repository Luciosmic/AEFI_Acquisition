#!/bin/bash
# Vibe session start hook — clear this session's tracking file
# This replaces Claude's SessionStart hook
# Vibe uses VIBE_SESSION_ID environment variable instead of CLAUDE_CONVERSATION_ID

PROJECT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Vibe sets VIBE_SESSION_ID environment variable
SESSION_ID="${VIBE_SESSION_ID:-}"

# Also try to extract from stdin if available
if [ -z "$SESSION_ID" ]; then
    DATA=$(cat)
    SESSION_ID=$(echo "$DATA" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('session_id', ''))
" 2>/dev/null)
fi

if [ -n "$SESSION_ID" ]; then
  rm -f "${PROJECT_DIR}/.vibe/session_touched_files_${SESSION_ID}"
fi

# Also clean up files older than 7 days in .vibe directory
find "${PROJECT_DIR}/.vibe" -name 'session_touched_files_*' -mtime +7 -delete 2>/dev/null || true

exit 0
