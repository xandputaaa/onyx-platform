# ONYX Spatial Hardware V1 — implementation specification

Status: design proposal; not deployed or hardware-validated.

## Devices
- GLASSES: see-through AR client with voice, glanceable cards, spatial anchors, hand tracking when supported. Prototype with a regular browser and mock pose input before choosing headset SDK.
- HOLO: Pepper's Ghost desk display with high-contrast black-background renderer and calibrated mirrored orientation. Apparent floating avatar has constrained viewing cone; no claim of true volumetric projection.
- STEM GO/HOME: audio/LED control surfaces, physical microphone mute, local volume, shared session handoff.

## Ferrofluid visual language
Reference: real magnetic liquid droplet stretching, merging and separating. Recreate procedurally; do not embed copyrighted source footage. Idle = slow viscous wobble; listening = directional elongation with smoothed RMS audio envelope; thinking = transient stretched tendrils and restrained Rosensweig-like peaks; speaking = syllable-linked amplitude deformation; alert = short controlled contraction. Provide reduced-motion setting. Aim for 60 FPS desktop, adaptive fidelity on mobile/AR. Three.js shader mesh with vertex displacement driven by low-frequency noise and smooth impulse fields; metalness and environment reflections, avoid full computational fluid simulation.

## Interaction
- Voice command parser -> authorized intent -> ONYX Core -> device-specific response.
- Hand tracking: hover, pinch/select, drag, two-hand rotate/scale; confidence thresholds, dwell/debounce, and mouse fallback.
- Avoid occluding real-world hazards; low-distraction mode during movement.
- User-initiated camera access only; camera processing locally when feasible, no silent recording.

## Device transport
Authenticated HTTPS + WebSocket with per-device short-lived credentials, pairing/revocation, monotonic event sequence, and reconnect snapshots.
Event envelope:
```json
{"version":1,"type":"avatar.state","deviceId":"holo-01","sessionId":"session-uuid","sequence":42,"timestamp":"ISO-8601","payload":{"state":"listening"}}
```
Allowed avatar states: idle, listening, thinking, speaking, alert, muted, offline.
Other event types: panel.open, panel.close, object.transform, voice.partial, voice.final, session.handoff, device.health.
Validate payloads server-side; no credentials in client bundles. No automatic trading actions or secret financial data in display event payloads.

## Architecture
ONYX Core (identity, permissions, session coordinator, specialist adapters)
  <-> real-time event gateway
  <-> GLASSES (WebXR adapter / fallback browser)
  <-> HOLO (optical renderer / local audio)
  <-> STEM (hardware client)
KAREN remains a separately deployed read-only integration until independently authorized and verified.

## Milestones and acceptance tests
1. Web-only simulator with shared state machine and selectable device view. Verify all seven states, reduced motion, and offline fallback.
2. Three.js ferrofluid mesh: stretch, merge visual approximation, audio-reactive surface. Verify frame timing and mobile fallback.
3. Local HOLO calibration screen: reflector angle, image flip, contrast, black levels and viewing cone.
4. AR simulator with 3D panels and pointer/mouse; add supported WebXR and hand tracking only after device testing.
5. Backend device registry, authenticated event schema, replay protection, single active speaking endpoint, and handoff tests.
6. Physical prototypes: measure optical brightness, audio echo, microphone privacy switch, thermal performance, and power.

## Engineering constraints
- No new paid services or hardware purchases without approval.
- Never assume ChatGPT subscription includes API usage.
- Never change KAREN production while developing these clients.
- Verify open-source license compatibility before copying shader implementations.
- Existing ONYX repository currently starts ORNI API; decouple in a separate tested change before routing production traffic.
