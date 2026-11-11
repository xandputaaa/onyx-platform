# ORNI Blender remote desktop worker

This service runs a real Blender desktop in an X virtual framebuffer and exposes it through noVNC/websockify.

## Railway configuration
- Root directory: `/apps/orni-blender`
- Builder: Dockerfile
- Healthcheck path: `/vnc.html`
- Public port: `6080` (Railway injects `PORT`)
- Required secret: `VNC_PASSWORD` (choose a long unique password; do not reuse the ONYX or Groq secrets)

## Connect it to ONYX
Set `ORNI_BLENDER_BASE_URL` to the worker's HTTPS Railway domain. Set `ORNI_BLENDER_VIEW_URL` to:
`https://YOUR-WORKER-DOMAIN/vnc.html?autoconnect=true&resize=scale&path=websockify`

The viewer uses VNC password authentication. Do not remove the password or expose the worker without it. CPU rendering is enabled; this is a functional remote desktop, not a GPU-backed render farm.
