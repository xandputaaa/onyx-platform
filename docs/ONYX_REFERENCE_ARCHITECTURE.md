# ONYX Reference Architecture

Status: product requirements baseline  
Source inspiration: JARVIS, FRIDAY, KAREN, and EDITH feature breakdown supplied by the owner.  
Build order: ORNI -> NOVA -> ONYX command center -> The House integration.

## Product vision

ONYX is the primary AI and chief of staff for the platform. It provides a unified natural-language, voice, and visual interface; coordinates specialist agents; monitors authorized systems; and executes approved work. The owner remains the final authority for consequential decisions.

The goal is to reproduce the useful interaction patterns and capabilities described in the reference, not fictional unrestricted access or weapon systems.

## Capability translation

### JARVIS-inspired: command center and technical intelligence
- Unified command interface for voice, text, and visual interaction.
- Multi-step task planning and orchestration across specialist agents.
- Live operational dashboards for connected services, deployments, devices, and workflows.
- Diagnostic workflows that gather evidence, explain findings, and recommend corrective action.
- Visual analysis and reconstruction tools for user-provided or explicitly authorized media and project assets.
- Creative and engineering workspaces, including the future remote Blender workspace operated by ORNI.
- Task history, artifacts, approvals, and reproducible execution records.

### FRIDAY-inspired: responsive assistant and monitoring
- Natural, low-latency voice conversation with interruption and turn-taking.
- Context-aware notifications, severity levels, and escalation to the owner.
- Health checks, scheduled monitoring, and event-driven alerts for connected services.
- Clear status reporting: working, waiting for approval, completed, failed, or needs attention.
- Secure recovery procedures, retries, and human-readable explanations.

### KAREN-inspired: personalized companion interface
- Persistent, user-controlled preferences and contextual memory.
- Conversational support and a consistent assistant personality.
- Contextual modes (for example: focus, creative, operations, and quiet mode).
- Permission-aware actions and clear confirmation before consequential operations.
- A distinct specialist identity for each agent rather than one generic assistant persona.

### EDITH-inspired: connected authorized systems
- A permissioned integration layer for accounts, devices, files, communications, cloud services, and business systems.
- Search and retrieval across sources the owner explicitly connects.
- Device and service inventory with health, access, and activity status.
- Security event monitoring, anomaly alerts, and auditable access history.
- Explicit scopes, least-privilege credentials, revocation, and per-action approval.
- No weapon control, offensive cyber capability, covert access, hidden backdoors, or unrestricted surveillance. Any camera, location, communication, or personal-data integration must be authorized, visible, and revocable.

## Agent hierarchy and ownership

1. Owner: final authority and approval for consequential decisions.
2. ONYX: primary assistant, chief of staff, orchestrator, and unified interface.
3. ORNI: CELVANI specialist for fashion strategy, creative direction, product development, supplier and quality research, brand intelligence, and commerce analysis.
4. NOVA: personal brand and creator-operations specialist.
5. KAREN: independent BTC Pulse specialist; remains independently deployed and integrates through a secured interface when authorized.

Specialists own their domain work and report structured findings to ONYX. ONYX coordinates cross-domain work and presents decisions and approvals to the owner.

## ORNI-first implementation boundary

ORNI is being built first inside this monorepo and may run as an independently deployed backend service. Its eventual user interface belongs inside the ONYX experience; a separate public ORNI website is not required.

ORNI's planned Blender workflow must use a real remote Blender worker. The future interface should show an actual streamed workspace while ORNI operates it, expose task state, and allow the owner to review outputs. The worker's compute and graphics requirements must be evaluated separately from the lightweight API service; a standard API container is not assumed to provide a usable GUI or GPU.

## Shared platform contracts

- Agent identity and service-to-service authentication.
- Structured task and message envelopes with IDs, timestamps, status, and correlation IDs.
- Explicit capability and permission scopes for each agent.
- Durable task state, artifact references, and audit events.
- Health and readiness endpoints for each service.
- Timeouts, retries, idempotency, and safe failure handling.
- Secrets stored in the deployment provider's secret manager, never in source control or chat.
- Human approval gates for purchases, publishing, sending messages, financial actions, account changes, or other consequential operations.

## Suggested future ONYX modules

- Command Center: conversation, voice, notifications, approvals, and current missions.
- Agent Registry: ORNI, NOVA, KAREN, and future specialists with health and permissions.
- Mission Control: task planning, execution state, delegation, and audit trail.
- Connected Systems: authorized accounts, devices, APIs, and integration permissions.
- Intelligence: search, analysis, diagnostics, and reports.
- Creative Workspace: image and video workflows plus ORNI's remote Blender session.
- The House: visual shared environment reflecting actual agent and task states, not simulated activity.
- Memory and Preferences: owner-controlled context, retention, and deletion controls.
- Security Center: authentication, access scopes, alerts, logs, and revocation.

## Delivery principles

- Build and verify real functionality incrementally; never label a planned capability as working.
- Keep ORNI and NOVA specialist services independently testable while sharing platform contracts.
- Build ONYX's central interface after ORNI and NOVA foundations are ready.
- Integrate KAREN through authenticated APIs without copying its internal trading logic or reusing its database.
- Every visible status must be backed by actual service or task state.
