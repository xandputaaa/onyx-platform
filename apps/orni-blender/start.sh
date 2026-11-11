#!/usr/bin/env bash
set -euo pipefail
: "${VNC_PASSWORD:?Set a strong VNC_PASSWORD in Railway Variables}"
export DISPLAY=:1
Xvfb :1 -screen 0 1600x1000x24 -ac +extension GLX +render -noreset &
sleep 2
fluxbox >/tmp/fluxbox.log 2>&1 &
sleep 2
x11vnc -display :1 -forever -shared -rfbport 5900 -localhost -passwd "$VNC_PASSWORD" -noxdamage >/tmp/x11vnc.log 2>&1 &
sleep 2
blender --factory-startup >/tmp/blender.log 2>&1 &
sleep 4
exec websockify --heartbeat 30 --web=/usr/share/novnc "${PORT:-6080}" localhost:5900
