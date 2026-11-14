# ONYX GLASSES MK1 — XREAL Air 2 implementation target

Decision: target **XREAL Air 2**, not Air 2 Ultra. This is a hardware/software planning target, not a purchased or connected device.

Official XREAL SDK compatibility: Air 2 supports 3DoF head rotation; it does **not** support plane detection, hand tracking, depth mesh, or spatial anchors. No outward-facing camera. Source: https://docs.xreal.com/XREALDevices/Compatibility

## Architecture
- Host: compatible Android/Beam Pro or computer with USB-C DisplayPort Alt Mode, subject to app/SDK compatibility verification.
- UI: original ONYX high-contrast, low-distraction text HUD and procedural liquid-metal avatar; support manual mute and silent-only output.
- Speech: host-side microphone permission for opt-in input; host-side TTS only when explicitly allowed. Public mode always suppresses spoken output and alerts.
- Core: ONYX API on a separate dev environment; no production/KAREN changes.
- Transport: headset display via supported host rendering; command/event bridge to ONYX Core; fallback local UI when offline.
- Safety: no environmental recording without explicit opt-in; never auto-enable camera/mic.

## Deskspace limitations
- Stage A: on-screen desk simulation and manual grid placement; not world anchored.
- Stage B: optional external camera + 6DoF tracking computer could estimate desk geometry, but needs careful calibration between tracking sensor and headset; **not** a trivial clip-on camera mod and not guaranteed.
- Stage C: native world-anchored desk experience requires glasses with supported 6DoF plane tracking (e.g., Air 2 Ultra).

## V1 milestones
1. Browser simulator: public/private prompt, text-only replies, explicit TTS policy.
2. HUD layout responsive to narrow field of view, glanceable captions, stateful ferrofluid avatar.
3. Unity/XREAL SDK demo on supported host, 3DoF mode; confirm actual hardware connection.
4. Deskspace manual mock, with honest 'not anchored' label.
5. Test reconnect and offline mode; mute must survive connection loss.

## Acceptance
- No audio before explicit opt-in; Public Mode overrides TTS.
- No claim of automatic public detection or camera capability.
- Never label simulated desk as detected.
- Confirm SDK/host compatibility before purchase.
