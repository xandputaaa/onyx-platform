#!/usr/bin/env bash
set -euo pipefail
: "${VNC_PASSWORD:?Set VNC_PASSWORD in Railway Variables}"
export DISPLAY=:1
export PYTHONUNBUFFERED=1

echo "[ORNI] Starting virtual display"
Xvfb :1 -screen 0 1600x1000x24 -ac +extension GLX +render -noreset >/tmp/xvfb.log 2>&1 &
sleep 2
fluxbox >/tmp/fluxbox.log 2>&1 &
sleep 2
x11vnc -display :1 -forever -shared -rfbport 5900 -localhost -passwd "$VNC_PASSWORD" -noxdamage >/tmp/x11vnc.log 2>&1 &
sleep 2

echo "[ORNI] Starting Blender desktop and automation API"
blender --factory-startup --python /workspace/automation.py >/tmp/blender.log 2>&1 &
BLENDER_PID=$!
tail -n +1 -F /tmp/blender.log &
LOG_TAIL_PID=$!
cleanup() { kill "$BLENDER_PID" "$LOG_TAIL_PID" 2>/dev/null || true; }
trap cleanup EXIT

READY=0
for attempt in $(seq 1 60); do
  if ! kill -0 "$BLENDER_PID" 2>/dev/null; then
    echo "[ORNI] Blender exited during startup; recent log:"
    tail -n 100 /tmp/blender.log || true
    exit 1
  fi
  if grep -q "ORNI Blender control API listening" /tmp/blender.log 2>/dev/null; then READY=1; break; fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then
  echo "[ORNI] Blender did not report API readiness within 60 seconds"
  tail -n 100 /tmp/blender.log || true
  exit 1
fi
echo "[ORNI] Blender automation API is ready"

cat > /usr/share/novnc/index.html <<'HTML'
<!doctype html><html><head><meta http-equiv="refresh" content="0;url=/vnc.html?autoconnect=true&resize=remote&path=websockify"><title>ORNI Blender</title></head><body><a href="/vnc.html?autoconnect=true&resize=remote&path=websockify">Open Blender</a></body></html>
HTML

echo "[ORNI] Starting noVNC gateway on port ${PORT:-6080}"
exec websockify --heartbeat 30 --web=/usr/share/novnc "${PORT:-6080}" localhost:5900
