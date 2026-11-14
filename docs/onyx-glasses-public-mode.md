# ONYX GLASSES — Public Mode V1

User-requested interaction: when ONYX suspects the wearer is in public, show the private lens prompt **“Boss, are we in public?”** and use lens text instead of text-to-speech (TTS).

## Privacy-first behavior
- Default to silent text while the public/private context is unknown. Never speak the confirmation prompt aloud.
- Show: "Boss, are we in public?" with Yes / No / Not now.
- YES: switch to PUBLIC mode; no TTS output, no audible notification, compact text-only HUD. Respect manual override; don't unmute without consent.
- NO: switch to PRIVATE mode; TTS permitted only if separately enabled in audio settings.
- NOT NOW / timeout: remain silent, do not assume privacy, dismiss unobtrusively.
- Remember selection for session, with optional user-approved per-location preferences later. Do not infer or retain location without explicit consent.
- Provide immediate silent toggle from glasses and companion app. A mute switch always wins.
- Text should be short, glanceable, high contrast and low-distraction; don't display sensitive content without user consent or where bystanders can see reflected lenses.
- Input options: touch, gesture, button or silent voice command only if microphone is enabled. Speech input and spoken output are distinct controls.

## Context hints (opt-in only)
Possible indicators: movement, ambient sound level processed locally, user-set routine, or device scene classification. Never claim these prove public/private context. Do not require camera surveillance, record bystanders, or continuously upload ambient audio. Prefer explicit user selection.

## State machine
UNKNOWN -> (prompt) -> PUBLIC | PRIVATE | UNKNOWN
PUBLIC -> PRIVATE only via explicit user action.
PRIVATE -> PUBLIC via explicit action, or ask again on material context change (no repeated prompts).
OFFLINE -> retain last selected mute policy; default silent if no known setting.

## Acceptance tests
1. Initial state is silent; no TTS emitted before consent.
2. Suspected public context shows text prompt without sound.
3. YES disables TTS and audio alerts, preserves text HUD.
4. NO does not enable TTS when global TTS permission is off.
5. Timeout stays silent and does not repeatedly prompt.
6. Manual mute always overrides private mode.
7. Session reconnect does not accidentally enable speech.
8. Device has a low-distraction display mode while walking.

Status: design specification, not yet integrated into glasses firmware or production.
