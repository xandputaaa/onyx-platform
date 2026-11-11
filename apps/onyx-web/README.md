# ONYX Web

This service is the ONYX command-center interface and secure server-side proxy to ORNI.

Railway service configuration:
- Root directory: `/apps/onyx-web`
- Start command: `npm start`
- Healthcheck: `/health`

Required variables:
- `ORNI_BASE_URL`: ORNI API origin
- `ORNI_ACCESS_TOKEN`: shared server-to-server bearer credential

The browser never receives the ORNI bearer token. Mission requests are analysis-only until additional integrations are implemented.