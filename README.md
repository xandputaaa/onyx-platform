# ONYX Platform

The central ONYX AI platform. ORNI (CELVANI), NOVA (creator operations), and specialist integrations connect through authenticated internal services. KAREN remains independently deployed.

## Architecture

- Web application: ONYX command center
- API/backend: identity, permissions, orchestration, memory, missions, agent messaging
- ORNI: CELVANI specialist and creative studio
- Blender worker: remote, AI-operated Blender with streamed visual workspace
- NOVA: personal brand and creator operations
- Integrations: secure specialist APIs, Shopify, storage, and observability

This repository is the source of truth for the ONYX platform. Secrets belong in Railway variables, never in Git.
