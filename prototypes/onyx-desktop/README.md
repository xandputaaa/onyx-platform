# ONYX Desktop Command Center — UI prototype

A static, responsive command center shell for a future installable ONYX desktop application. It runs in a browser now, **without a computer purchase, desktop runtime, backend integrations, authenticated services, device pairing, or live data**.

From the repository root:

```sh
python3 -m http.server 8080
```

Open http://localhost:8080/prototypes/onyx-desktop/

Tests: `node --test prototypes/onyx-desktop/modules.test.mjs`

## Future desktop packaging

Evaluate Tauri 2 for a signed Windows/macOS desktop app once a target operating system and computer are selected. Use OS keychain for tokens, least-privilege permissions, per-module authentication, and explicit approval for any consequential action. Avoid embedding production secrets in the frontend. Read-only KAREN integration first; no autonomous orders.

## Modules

ONYX Core, KAREN, ONYX Glasses, ORNI/CELVANI, Development, Systems. Navigation is functional in this preview, but the modules are descriptions, not connected features.

## Architecture milestones

1. Standalone responsive shell and module registry (this stage).
2. Dedicated ONYX API contract and authenticated local/remote bridge.
3. Desktop runtime packaging and OS integration.
4. Read-only adapters to project status, KAREN, and hardware simulators.
5. Opt-in voice and device control, security review, accessibility and offline fallback.

No production changes or new paid services.
