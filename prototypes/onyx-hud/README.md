# ONYX Visual Prototype (isolated, static)

No dependencies, API keys, camera, microphone, backend connection, or production route changes.

## Run locally

From repository root:

```sh
python3 -m http.server 8080
# visit http://localhost:8080/prototypes/onyx-hud/
```

Alternatively run any static server that serves ES modules. Opening index.html directly with file:// may block module imports.

## Tests

```sh
node --test prototypes/onyx-hud/state.test.mjs
```

## Features

- Canvas-rendered procedural liquid-metal droplet with stretching, wobble, transient tendrils and highlights.
- Seven states: idle, listening, thinking, speaking, alert, muted, offline.
- GLASSES HUD mode with draggable simulated panels.
- HOLO black-background output with horizontal mirror toggle for optical experiments.
- Manual simulated audio amplitude slider; does not access microphones.
- Reduced-motion toggle plus OS preference.
- Responsive layout; isolated from existing ORNI runtime.

## Scope and limitations

This is a **2D procedural visual prototype**, not a physically simulated ferrofluid, true volumetric hologram, or WebXR implementation. The GLASSES mode is a screen simulator, not a connected headset. HOLO calibration requires physical testing. The KAREN panel is deliberately a placeholder with no live data. No voice input, AI inference, trading, camera, device authentication, or real-world optical validation is included. Subsequent milestones will implement Three.js/WebGL 3D and authorized ONYX Core integration.

## Licensing

All prototype source is original; real ferrofluid videos are visual references only. Do not copy third-party shader or footage without verifying license and attribution.
