import express from "express";
import helmet from "helmet";
import { randomUUID, timingSafeEqual } from "node:crypto";

const app = express();
app.disable("x-powered-by");
app.use(helmet());
app.use(express.json({ limit: "1mb" }));

const startedAt = new Date().toISOString();
const startedAtMs = Date.now();
const allowedOrigin = process.env.ONYX_ORIGIN;

app.use((req, res, next) => {
  const origin = req.get("origin");
  if (origin && allowedOrigin && origin === allowedOrigin) {
    res.setHeader("Access-Control-Allow-Origin", allowedOrigin);
    res.setHeader("Vary", "Origin");
    res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  }
  if (req.method === "OPTIONS") return res.sendStatus(204);
  next();
});

function hasValidAgentToken(req) {
  const expected = process.env.ORNI_ACCESS_TOKEN;
  const supplied = req.get("authorization")?.replace(/^Bearer\s+/i, "");
  if (!expected || !supplied) return false;
  const a = Buffer.from(expected);
  const b = Buffer.from(supplied);
  return a.length === b.length && timingSafeEqual(a, b);
}

function requireAgentToken(req, res, next) {
  if (!hasValidAgentToken(req)) {
    return res.status(401).json({ error: "Unauthorized", message: "A valid ONYX-to-ORNI bearer token is required." });
  }
  next();
}

const orniSystemPrompt = `You are ORNI, the CELVANI specialist within the ONYX agent ecosystem. ONYX is your parent coordinator; the user is the final decision-maker.

MISSION
Protect and grow CELVANI as a credible minimalist luxury fashion house. CELVANI is positioned as premium accessible luxury. Its identity, product quality, authenticity, reputation and long-term brand equity take priority over short-lived attention or the cheapest supplier.

RESPONSIBILITIES
Brand strategy and identity protection; creative direction and product development; fashion, competitor and cultural intelligence; supplier, manufacturing and quality analysis; pricing, margin and commercial planning; CELVANI-specific campaigns, social strategy and partnerships; Shopify operations when connected.

BOUNDARIES
Do not take over personal creator management unrelated to CELVANI. Do not claim to have browsed, contacted suppliers, accessed Shopify, generated assets, opened Blender or completed external actions unless the relevant integration actually supplied evidence. Never invent prices, supplier credentials, sales data or market facts. Distinguish facts, assumptions and recommendations. Ask for approval before publishing, purchasing, contacting people, changing store data or making financial commitments.

WORKING STYLE
Be a commercially sharp creative director and operator. Challenge weak ideas respectfully and explain the brand, quality, reputation or financial risk. Prefer evidence, product excellence and coherent luxury positioning over hype. When information is missing, state exactly what is needed.

REPORT FORMAT
Return a concise structured report with these fields:
- mission
- findings
- intelligence
- opportunities
- risks
- recommendation
- approvalRequired
- assumptions
- nextActions

Do not imply that a recommendation is an executed action. Return only data matching the supplied JSON schema.`;

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
      requiredFields: ["mission", "findings", "intelligence", "opportunities", "risks", "recommendation", "approvalRequired"]
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
      authenticatedMissionEndpoint: Boolean(process.env.ORNI_ACCESS_TOKEN && process.env.OPENAI_API_KEY),
      celvaniIntelligence: "model-assisted analysis; live research integration not connected",
      creativeStudio: "planned",
      blenderAutomation: "planned",
      visualWorkspaceStreaming: "planned",
      shopifyIntegration: "planned",
      onyxMessaging: "API contract ready; ONYX callback not connected"
    },
    configuration: {
      agentTokenConfigured: Boolean(process.env.ORNI_ACCESS_TOKEN),
      modelProviderConfigured: Boolean(process.env.OPENAI_API_KEY),
      onyxOriginConfigured: Boolean(allowedOrigin)
    },
    note: "A configured provider enables model-assisted analysis only; external integrations remain separate."
  });
});


const missionReportSchema = {
  type: "object",
  additionalProperties: false,
  required: [
    "mission", "findings", "intelligence", "opportunities", "risks",
    "recommendation", "approvalRequired", "assumptions", "nextActions"
  ],
  properties: {
    mission: { type: "string" },
    findings: { type: "array", items: { type: "string" } },
    intelligence: { type: "array", items: { type: "string" } },
    opportunities: { type: "array", items: { type: "string" } },
    risks: { type: "array", items: { type: "string" } },
    recommendation: { type: "string" },
    approvalRequired: { type: "boolean" },
    assumptions: { type: "array", items: { type: "string" } },
    nextActions: { type: "array", items: { type: "string" } }
  }
};

app.post("/api/orni/mission", requireAgentToken, async (req, res) => {
  const mission = typeof req.body?.mission === "string" ? req.body.mission.trim() : "";
  if (!mission) return res.status(400).json({ error: "mission is required" });
  if (mission.length > 6000) return res.status(413).json({ error: "mission must be 6000 characters or fewer" });
  if (!process.env.OPENAI_API_KEY) {
    return res.status(503).json({ error: "Model provider is not configured", required: ["OPENAI_API_KEY"] });
  }

  const model = process.env.ORNI_MODEL || "gpt-4.1-mini";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 45000);

  try {
    const response = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model,
        instructions: orniSystemPrompt,
        input: mission,
        max_output_tokens: 1800,
        store: false,
        text: {
          format: {
            type: "json_schema",
            name: "orni_mission_report",
            strict: true,
            schema: missionReportSchema
          }
        }
      }),
      signal: controller.signal
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      console.error("ORNI model provider returned an error", { status: response.status, type: payload?.error?.type });
      return res.status(502).json({ error: "ORNI model provider request failed", providerStatus: response.status });
    }

    const output = payload.output_text || (payload.output || [])
      .flatMap(item => item.content || [])
      .filter(item => item.type === "output_text")
      .map(item => item.text)
      .join("\\n");

    if (payload.status === "incomplete") {
      return res.status(502).json({
        error: "ORNI report was incomplete",
        reason: payload.incomplete_details?.reason || "unknown"
      });
    }

    if (!output) {
      const refusal = (payload.output || [])
        .flatMap(item => item.content || [])
        .find(item => item.type === "refusal");
      return res.status(502).json({
        error: refusal?.refusal || "ORNI received an empty model response"
      });
    }

    let report;
    try {
      report = JSON.parse(output);
    } catch {
      return res.status(502).json({ error: "ORNI returned a report that could not be parsed" });
    }

    return res.status(200).json({
      agent: "ORNI",
      domain: "CELVANI",
      missionId: randomUUID(),
      model,
      report,
      approvalRequired: report.approvalRequired,
      generatedAt: new Date().toISOString(),
      execution: "analysis_only"
    });
  } catch (error) {
    const timedOut = error?.name === "AbortError";
    console.error("ORNI mission failed", { timedOut, name: error?.name });
    return res.status(timedOut ? 504 : 502).json({
      error: timedOut ? "ORNI mission timed out" : "ORNI mission could not reach its model provider"
    });
  } finally {
    clearTimeout(timeout);
  }
});

app.get("/", (_req, res) => {
  res.json({
    name: "ORNI API",
    description: "CELVANI specialist service within the ONYX platform monorepo",
    health: "/health",
    profile: "/api/orni/profile",
    status: "/api/orni/status",
    mission: "POST /api/orni/mission"
  });
});

const port = Number(process.env.PORT || 3000);
app.listen(port, "0.0.0.0", () => {
  console.log(`ORNI API listening on port ${port}`);
});
