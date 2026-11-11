#!/usr/bin/env bash
set -euo pipefail
: "${VNC_PASSWORD:?Set a strong VNC_PASSWORD in Railway Variables}"
export DISPLAY=:1

echo "[ORNI] Starting virtual display"
Xvfb :1 -screen 0 1600x1000x24 -ac +extension GLX +render -noreset &
sleep 2
fluxbox >/tmp/fluxbox.log 2>&1 &
sleep 2
x11vnc -display :1 -forever -shared -rfbport 5900 -localhost -passwd "$VNC_PASSWORD" -noxdamage >/tmp/x11vnc.log 2>&1 &
sleep 2

echo "[ORNI] Starting Blender desktop and automation API"
blender --factory-startup --python /workspace/automation.py 2>&1 | tee /tmp/blender.log &
BLENDER_PIPE_PID=$!

# Give Blender time to initialize, but fail loudly if it exits immediately.
for attempt in $(seq 1 20); do
  if ! kill -0 "$BLENDER_PIPE_PID" 2>/dev/null; then
    echo "[ORNI] Blender exited during startup; recent log:"
    tail -n 100 /tmp/blender.log || true
    exit 1
  fi
  if grep -q "ORNI Blender control API listening" /tmp/blender.log; then
    echo "[ORNI] Blender automation API is ready"
    break
  fi
  sleep 1
done
if ! grep -q "ORNI Blender control API listening" /tmp/blender.log; then
  echo "[ORNI] Blender did not report API readiness within 20 seconds"
  tail -n 100 /tmp/blender.log || true
  exit 1
fi

# Railway probes /; noVNC normally opens at /vnc.html.
cat > /usr/share/novnc/index.html <<'HTML'
<!doctype html><html><head><meta http-equiv="refresh" content="0;url=/vnc.html?autoconnect=true&resize=remote&path=websockify"><title>ORNI Blender</title></head><body><a href="/vnc.html?autoconnect=true&resize=remote&path=websockify">Open Blender</a></body></html>
HTML

echo "[ORNI] Starting noVNC gateway on port ${PORT:-6080}"
exec websockify --heartbeat 30 --web=/usr/share/novnc "${PORT:-6080}" localhost:5900
