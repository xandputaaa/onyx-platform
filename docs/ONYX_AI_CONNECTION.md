# ONYX AI Provider Setup (Cost-Safe)

The default ONYX mode is OFFLINE. A ChatGPT Plus/Pro membership is **not** an OpenAI API credential and does not automatically pay for API requests. Never paste ChatGPT browser cookies, session tokens, or passwords into ONYX.

## Optional separately billed OpenAI API
Only after reviewing API pricing, usage limits, and explicitly approving spending, configure these server-side Railway variables on the **dedicated ONYX Core service**:
- `ONYX_CORE_TOKEN`: long random secret for protected ONYX routes
- `OPENAI_API_KEY`: API key from the OpenAI API platform, not ChatGPT login
- `ONYX_OPENAI_ENABLED=true`: explicit opt-in; defaults off
- `ONYX_OPENAI_MODEL`: approved Responses API model (defaults to gpt-4.1-mini)

The API adapter sends the user's message and ONYX's system instructions, requests `store:false`, limits output tokens to 220 and times out after 12 seconds. API usage may incur charges. No spend cap is enforced in ONYX code; configure account-side limits and monitoring before enabling. The interface does not currently implement user accounts, persistent memory, voice, or streaming.

## Deploy independently
Do not change the existing `onyx-web` service running ORNI. Use a distinct Railway service sourced from `xandputaaa/onyx-platform`, with root directory `/apps/onyx-core`, start command `npm start`, and healthcheck `/health`. Verify `npm test` first.

## Truthful states
- `/health` is public and reports `modelConnected:false` until an actual provider health verification is implemented; `modelConfigured` only reflects local settings.
- `/api/status` and `/api/conversation` require bearer `ONYX_CORE_TOKEN`.
- Without explicit API opt-in, the conversation endpoint uses deterministic offline responses.
- A 429, timeout, empty output, or provider failure is not a successful AI call.
- Sign-in-with-ChatGPT eligibility for this custom Railway application is **not verified**; no subscription-based authorization flow is implemented.

## Verification
`cd apps/onyx-core && npm test`. Check protected endpoints reject missing/wrong tokens and verify no network call occurs when provider is disabled.
