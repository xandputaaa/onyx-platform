# ONYX Core — KAREN Protocol Foundation v0.1

## Product identity
ONYX is a permissioned personal chief-of-staff AI. Its primary interaction reference is the conversational suit assistant Karen in *Spider-Man: Homecoming* (2017), not the separate BTC product named KAREN. Borrow operational coordination from J.A.R.V.I.S., situational analysis from F.R.I.D.A.Y., and consent-based visual overlays from E.D.I.T.H. Fictional weapons, covert surveillance, universal device access, and certainty about future events are **not** product requirements.

## Film-derived interaction reference
- Karen is a natural, context-aware voice companion who speaks with Peter while he is occupied, offers suggestions, and explains available capabilities.
- Karen helps with navigation/interception, playback and review of recorded footage, reconnaissance and visual modes, and social conversation.
- Her interactions also demonstrate failure modes: confusing or excessive feature choices, intrusive surveillance, and dangerous automatic modes. ONYX explicitly avoids these.
- J.A.R.V.I.S.: coordinated multi-system assistance and conversational control.
- F.R.I.D.A.Y.: concise real-time status and analytic support.
- E.D.I.T.H.: visual information overlays and command authorization, **without** unauthorized tracking or weapon control.

References:
- https://www.thewrap.com/voice-suit-spider-man-homecoming/
- https://www.springfieldspringfield.co.uk/movie_script.php?movie=spider-man-homecoming
- https://www.edwardsedition.com/film-review-spider-man-homecoming/
- https://nerdist.com/article/visionquest-who-are-mcu-ai-characters-marvel-jarvis-dum-e-friday/

## Conversation contract
1. Respond to ordinary speech without requiring a command phrase; optional wake phrase only when an always-listening device integration is explicitly enabled.
2. Voice answers first give a concise answer, then optional details. Support interruption, corrections, and follow-up context.
3. Proactive alerts require opt-in and show why they fired. Quiet hours and pause controls are mandatory.
4. Distinguish observed facts, inferences, predictions, and simulations. Show source, timestamp, and confidence where applicable.
5. No fabricated tool execution, connections, live feed access, completed missions, or background monitoring.
6. Personal memory must be inspectable and user-controlled; distinguish remembered preferences from fresh evidence.
7. Ask before external side effects (messages, purchases, publishing, modifying deployments, or sharing data); use scoped credentials and audit actions.
8. Never covertly access cameras, microphones, screens, contacts, or other people's accounts.
9. Graceful offline/degraded states. If an integration is disconnected, say so plainly.

## Architecture boundaries
- ONYX Core: dedicated web UI, identity, conversations, mission state machine, tool permission gateway, event stream, notifications, memory, and audit log.
- ORNI: independent CELVANI / Blender specialist, reachable through authenticated adapters. Do not replace its API or rendering workers.
- KAREN V1: independent BTC/sports service, read-only summaries and health unless a separately approved action is added. Never auto-place trades.
- NOVA: future creator/brand specialist; initially show 'not connected'.
- All providers: free/no new paid services by default. Do not assume a language model or voice service is connected.

## Mission state machine
DRAFT -> AWAITING_APPROVAL (for external effects) -> QUEUED -> RUNNING -> SUCCEEDED/FAILED/CANCELLED.
Every mission has an id, origin, owner, scope, createdAt, updatedAt, status, lastError, evidence and approval history. No success without actual tool confirmation. Idempotency keys for side effects.

## Implementation phases
P0: isolated ONYX Core app and health endpoint; auth boundary; status UI and specialist registry with honest connectivity states; tests.
P1: chat/voice interaction, turn context, interruptions, source-grounded tool calls, permissions, logs.
P2: missions, approvals, notifications, memory, daily briefings, ORNI/KAREN read-only adapters.
P3: consent-based camera/image analysis, desktop/device integrations, proactive workflows, simulations.
P4: visual polish: black/white/silver, restrained animated ferrofluid, accessible reduced-motion fallback, responsive mobile layout.

## Definition of done for P0
Dedicated ONYX service starts independently of ORNI; unauthorized protected routes return 401/403; /health is honest; no secrets in frontend; tests pass; Railway deployment verified; no regressions to ORNI/KAREN.
