# ONYX DESKSPACE — HoloMat-inspired tabletop AR

User intent: ONYX GLASSES recognize a real desk and create a virtual engineering floor aligned with the tabletop, with 3D objects that remain anchored when the user's head moves.

This is an **independent design**, not a reproduction or verified description of HoloMat's implementation. Reference was a user-provided screenshot of Concept Bytes' HoloMat video, not the full technical video.

## Real-world pipeline
1. Explicit user permission for environmental sensing and camera access, where required.
2. Headset spatial tracking and environment mesh/plane detection. Detect horizontal desk candidates with estimated width/depth, position, normal, confidence.
3. Present a translucent candidate plane; user selects/confirms their desk. Reject uncertain planes or offer manual corner placement.
4. Establish a local desk coordinate frame (origin, axes, surface normal) and create an anchor using the headset's supported spatial anchor system.
5. Render virtual grid at a small offset above surface to avoid z-fighting. Model positions are expressed in desk-local meters.
6. Update view/projection with tracked head pose each frame; model stays world-locked. Re-localize after tracking loss, warn user instead of pretending anchor is stable.
7. Support ray/pinch selection, move/rotate/scale, mouse fallback, reset/recenter, and optional save of anchor if hardware supports persistence.

## Hardware capability gate
- Must verify device SDK access to plane detection or scene mesh, head tracking, world anchors and supported rendering APIs.
- WebXR hit-test and anchors are platform-dependent and may not provide automatic desk dimensions; use native SDK or manual calibration if needed.
- Generic camera video alone is not reliable spatial anchoring; a 2D overlay cannot stay fixed under parallax without 6DoF tracking.
- Never promise this works on a particular pair of glasses until tested with its supported SDK.

## Initial prototype
`prototypes/onyx-hud/deskspace.html` shows a simulated tabletop grid and draggable-by-slider placeholder model. It has no camera or tracking and is **not** evidence of working desk detection. `deskspace.mjs` provides desk-plane validation and local placement math with tests.

## Safety and privacy
- Require explicit consent before scanning, visible scanning status, local processing where feasible, no persistent camera recordings by default.
- Avoid obstructing real objects and hands. Provide a quick dismiss and movement-aware minimal mode.
- Use original interface design; do not copy third-party video content.
- No new paid services, no KAREN production changes.

## Next hardware milestone
Choose an actual AR device, confirm plane detection/anchor support from its SDK, then implement a real adapter with tracking-loss tests and headset-on-desk calibration.
