#!/bin/bash
# Renders shots one after another: render_queue.sh <script>:<shot> ...
# Waits for an earlier queue to finish. Finished frames are kept.
cd "$(dirname "$0")" || exit 1
state=../../../Saved/Trailer/queue.state
while [ "$(cat "$state" 2>/dev/null)" = busy ]; do sleep 5; done
echo busy > "$state"
for job in "$@"; do
  echo "START $job $(date +%T)"
  /c/bin/blender5.3/blender.exe --background --python "${job%%:*}.py" \
    -- "${job##*:}" 2>&1 | grep -E "Error|Traceback|line "
  echo "DONE $job $(date +%T)"
done
echo free > "$state"
