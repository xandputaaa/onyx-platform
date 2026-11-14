# ONYX Mission Control — Foundation
The mission API is protected by ONYX_CORE_TOKEN and is **in-memory only**. Restarting the service loses mission records. It cannot execute tools, place trades, move assets, or contact third parties.

## Endpoints
- GET /api/missions — lists drafts and approval states
- POST /api/missions — JSON { "title": "...", "description": "..." }
- POST /api/missions/:id/transition — JSON { "action": "submit" | "approve" | "reject" | "cancel" }
- GET /api/missions/audit — in-memory history of mission state changes

All routes require Authorization: Bearer <ONYX_CORE_TOKEN>. An approved mission is only **APPROVED**, not executed or completed. No background jobs run.

## Next work
Persistent storage with encryption and retention controls, authenticated per-user ownership, idempotency, scoped approval expiry, safe tool gateway, event streaming and full integration tests must precede any real execution. No finance/trading work is in scope for ONYX Core yet.
