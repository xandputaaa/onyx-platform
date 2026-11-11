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

app.get("/api/orni/profile", (_req, res) => {
  res.status(200).json({
    agent: "ORNI",
    parent: "ONYX",
    domain: "CELVANI",
    role: "CELVANI fashion-house specialist",
    mission: "Protect and grow CELVANI as a credible minimalist luxury fashion house.",
    scope: [
      "brand strategy and identity protection",
      "creative direction and product development",
      "fashion, competitor and cultural intelligence",
      "supplier, manufacturing and quality research",
      "pricing, margin and commercial analysis",
      "campaign, social and CELVANI partnership research",
      "Shopify operations and reporting when connected"
    ],
    exclusions: [
      "personal creator management unrelated to CELVANI",
      "acting as the user's primary assistant",
      "publishing, purchasing, messaging or making financial commitments without approval"
    ],
    operatingPrinciples: [
      "quality and long-term brand equity over the cheapest option",
      "minimalist luxury identity over short-lived attention",
      "evidence-led recommendations with uncertainty stated",
      "challenge decisions that create avoidable brand, quality or financial risk",
      "request approval before external or irreversible actions"
    ],
    reporting: {
      recipient: "ONYX",
      requiredFields: [
        "mission",
        "findings",
        "intelligence",
        "opportunities",
        "risks",
        "recommendation",
        "approvalRequired"
      ]
    },
    executionState: "profile-defined; connected capabilities are not implied"
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
