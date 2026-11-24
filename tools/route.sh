#!/bin/sh
# Route the placed board with Freerouting (https://github.com/freerouting/freerouting) and
# bring the tracks back into KiCad. Needs Java and the jar:
#   FREEROUTING=/path/to/freerouting.jar tools/route.sh [attempts]
# The router gives a different result every time and does not always finish every connection,
# so the board is rebuilt and routed again until KiCad finds nothing open and nothing wrong.
set -e
JAR="${FREEROUTING:-$HOME/.cache/manent-band-tools/freerouting.jar}"
[ -f "$JAR" ] || { echo "Freerouting jar not found at $JAR: set FREEROUTING"; exit 1; }
here="$(cd "$(dirname "$0")" && pwd)"
out="$here/../electrical/out"
attempt=0
while [ "$attempt" -lt "${1:-8}" ]; do
  attempt=$((attempt + 1))
  "$here/kicad.sh" place > /dev/null
  "$here/kicad.sh" py gen/pcb_route.py export > /dev/null
  (cd "$out" && java ${JAVA_OPTS:--Xmx2g} -jar "$JAR" -de pendant.dsn -dr pendant.rules -do pendant.ses -mp 80 --gui.enabled=false > route.log 2>&1)
  router="$(grep 'Auto-routing stage completed' "$out/route.log" | grep -o '([0-9]* unrouted and [0-9]* violations*)' | tail -1)"
  "$here/kicad.sh" py gen/pcb_route.py import out/pendant.ses > /dev/null
  "$here/kicad.sh" check > /dev/null
  kicad="$(python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
print(len(d['violations']), 'violations,', len(d['unconnected_items']), 'open')" "$out/drc.json")"
  echo "attempt $attempt: router $router; KiCad $kicad"
  if [ "$kicad" = "0 violations, 0 open" ]; then
    cp "$out/pendant.ses" "$here/../electrical/kicad/pendant.ses"   # the tracks, kept so `make board` can rebuild them
    exit 0
  fi
done
echo "no clean result in $attempt attempts: the board on disk is the last one"
exit 1
