# ORNI API contract

ORNI is the CELVANI specialist service inside the ONYX platform. ONYX is the authenticated caller and coordinator; the user remains the final decision-maker.

## Production service

Base URL: `https://orni-api-production.up.railway.app`

## Endpoints

| Method | Path | Purpose | Authentication |
| --- | --- | --- | --- |
| GET | `/health` | Process liveness; suitable for Railway health checks | None |
| GET | `/ready` | Application readiness; returns 503 until both required secrets exist | None |
| GET | `/api/orni/profile` | Agent identity, scope and operating boundaries | None |
| GET | `/api/orni/status` | Configuration presence and capability state (never secret values) | None |
| POST | `/api/orni/mission` | Run a CELVANI analysis mission and return a structured report | Bearer token |

## Required Railway secrets

Configure these only in the Railway service's Variables interface:

- `OPENAI_API_KEY`: a dedicated ORNI OpenAI API key. Do not reuse KAREN's key.
- `ORNI_ACCESS_TOKEN`: a high-entropy secret shared only between ONYX's server-side caller and ORNI.

Optional non-secret settings:

- `ORNI_MODEL`: defaults to `gpt-4.1-mini`.
- `ONYX_ORIGIN`: exact browser origin for a future approved browser integration. Server-to-server ONYX calls do not depend on browser CORS.

Never commit credentials to this repository or expose them to browser code.

## Readiness behavior

`GET /ready` returns HTTP 200 and `status: "ready"` only when both required secrets are configured. Otherwise it returns HTTP 503, `status: "not_ready"`, and the names of missing variables only.

Liveness and readiness are deliberately separate: a healthy process can be alive while provider credentials are not configured.

## Mission request

```http
POST /api/orni/mission
Authorization: Bearer <ORNI_ACCESS_TOKEN>
Content-Type: application/json

{
  "mission": "Evaluate the next CELVANI hoodie sample against the brand's product and quality standards."
}
```

Mission text must be a non-empty string of at most 6,000 characters.

## Mission response

Successful responses contain:

- `agent`, `domain`, `missionId`, `model`, `generatedAt`
- `report.mission`
- `report.findings[]`
- `report.intelligence[]`
- `report.opportunities[]`
- `report.risks[]`
- `report.recommendation`
- `report.approvalRequired`
- `report.assumptions[]`
- `report.nextActions[]`
- `execution: "analysis_only"`

The model response is constrained with a strict JSON Schema. ORNI must not imply that research, messaging, purchasing, publishing, file editing, Blender work, or Shopify changes have been executed unless a corresponding integration provides evidence. External or irreversible actions require approval.

## Error behavior

- `400`: missing or invalid mission text.
- `401`: missing or invalid ONYX bearer token.
- `413`: mission exceeds the size limit.
- `502`: provider failure, refusal, incomplete output, or invalid structured output.
- `503`: provider configuration missing.
- `504`: provider request timeout.

## Current integration boundary

The current service provides authenticated model-assisted analysis only. It does not yet have durable mission storage, live web research, a task queue, artifact storage, ONYX callbacks, Shopify access, image generation, or a Blender worker/visual stream. Those require separate integrations and explicit permissions.
