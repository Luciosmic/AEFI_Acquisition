#!/bin/bash
# Vibe hook — inject session_id into context
# This replaces Claude's UserPromptSubmit hook
# Vibe hooks receive JSON on stdin

DATA=$(cat)

SESSION_ID=$(echo "$DATA" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('session_id', 'unknown'))
" 2>/dev/null || echo "unknown")

# For Vibe, we output a structured response that can be used by other hooks
# Vibe expects specific stdout format for structured responses
echo "vibe_session_id=${SESSION_ID}"

exit 0
