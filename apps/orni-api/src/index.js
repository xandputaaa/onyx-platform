import express from "express";
import helmet from "helmet";

const app = express();
app.disable("x-powered-by");
app.use(helmet());
app.use(express.json({ limit: "1mb" }));

const startedAt = new Date().toISOString();
const startedAtMs = Date.now();

app.get("/health", (_req, res) => {
  res.status(200).json({
    ok: true,
    service: "orni-api",
    status: "healthy",
    startedAt,
    uptimeSeconds: Math.floor((Date.now() - startedAtMs) / 1000),
    timestamp: new Date().toISOString()
  });
});

app.get("/api/orni/status", (_req, res) => {
  res.status(200).json({
    agent: "ORNI",
    domain: "CELVANI",
    status: "foundation",
    capabilities: {
      celvaniIntelligence: "planned",
      creativeStudio: "planned",
      blenderAutomation: "planned",
      visualWorkspaceStreaming: "planned",
      shopifyIntegration: "planned",
      onyxMessaging: "planned"
    },
    note: "Capabilities are marked planned until their integrations are implemented and verified."
  });
});

app.get("/", (_req, res) => {
  res.json({
    name: "ORNI API",
    description: "CELVANI specialist service within the ONYX platform monorepo",
    health: "/health",
    status: "/api/orni/status"
  });
});

const port = Number(process.env.PORT || 3000);
app.listen(port, "0.0.0.0", () => {
  console.log(`ORNI API listening on port ${port}`);
});
