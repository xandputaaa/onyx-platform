import express from "express";
import helmet from "helmet";
import { registerCreativeRoutes } from "./creative.js";
import { randomUUID, timingSafeEqual } from "node:crypto";

const app = express();
app.disable("x-powered-by");
app.use(helmet());
app.use(express.json({ limit: "24mb" }));

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

registerCreativeRoutes(app, { requireAgentToken, systemPrompt: orniSystemPrompt });

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

app.get("/ready", (_req, res) => {
  const missing = [];
  if (!process.env.ORNI_ACCESS_TOKEN) missing.push("ORNI_ACCESS_TOKEN");
  if (!process.env.GROQ_API_KEY) missing.push("GROQ_API_KEY");
  const ready = missing.length === 0;
  res.status(ready ? 200 : 503).json({
    ok: ready,
    service: "orni-api",
    status: ready ? "ready" : "not_ready",
    missing,
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


app.get("/api/orni/blender/status", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base) return res.json({connected:false,state:"not_configured",message:"Blender private API URL is not configured."});
  try {
    const r=await fetch(base+"/health",{signal:AbortSignal.timeout(4000)});
    const body=await r.json().catch(()=>({}));
    return res.status(r.ok?200:502).json({connected:r.ok,state:r.ok?"connected":"degraded",worker:body});
  } catch { return res.status(502).json({connected:false,state:"unreachable"}); }
});
app.post("/api/orni/blender/scene/celvani-hoodie", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/api/scene/celvani-hoodie",{method:"POST",headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`,"Content-Type":"application/json"},body:"{}",signal:AbortSignal.timeout(90000)});
    return res.status(r.status).json(await r.json().catch(()=>({error:"Invalid Blender response"})));
  } catch(e) { return res.status(e?.name==="TimeoutError"?504:502).json({error:"Blender worker unavailable"}); }
});

app.get("/api/orni/status", (_req, res) => {
  res.status(200).json({
    agent: "ORNI",
    domain: "CELVANI",
    status: "foundation",
    capabilities: {
      authenticatedMissionEndpoint: Boolean(process.env.ORNI_ACCESS_TOKEN && process.env.GROQ_API_KEY),
      celvaniIntelligence: "Groq model-assisted analysis; live research integration not connected",
      creativeStudio: "planned",
      blenderAutomation: "planned",
      visualWorkspaceStreaming: "planned",
      shopifyIntegration: "planned",
      onyxMessaging: "API contract ready; ONYX callback not connected"
    },
    configuration: {
      agentTokenConfigured: Boolean(process.env.ORNI_ACCESS_TOKEN),
      modelProviderConfigured: Boolean(process.env.GROQ_API_KEY),
      modelProvider: "Groq",
      model: process.env.ORNI_MODEL || "qwen/qwen3.8-27b",
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
  const requestId = req.body?.requestId == null ? null : req.body.requestId;
  if (requestId !== null && (typeof requestId !== "string" || requestId.trim().length === 0 || requestId.length > 128)) {
    return res.status(400).json({ error: "requestId must be a non-empty string of 128 characters or fewer" });
  }
  const missionId = randomUUID();
  if (!mission) return res.status(400).json({ error: "mission is required" });
  if (mission.length > 6000) return res.status(413).json({ error: "mission must be 6000 characters or fewer" });
  if (!process.env.GROQ_API_KEY) {
    return res.status(503).json({ error: "Groq model provider is not configured", required: ["GROQ_API_KEY"] });
  }

  const model = process.env.ORNI_MODEL || "qwen/qwen3.8-27b";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 45000);

  try {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.GROQ_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: orniSystemPrompt + "\\nReturn one JSON object matching the ORNI mission report schema. Do not include markdown fences or commentary." },
          { role: "user", content: mission }
        ],
        max_completion_tokens: 1800,
        temperature: 0.3,
        response_format: {
          type: "json_schema",
          json_schema: {
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
      const providerError = payload?.error || {};
      const limited = response.status === 429;
      const retryAfter = response.headers.get("retry-after");
      console.error("ORNI model provider returned an error", {
        status: response.status,
        type: providerError.type,
        code: providerError.code
      });
      return res.status(limited ? 429 : 502).json({
        error: limited ? "ORNI provider rate or quota limit reached" : "ORNI model provider request failed",
        category: limited ? "provider_rate_limited" : "provider_error",
        providerStatus: response.status,
        providerType: providerError.type || null,
        providerCode: providerError.code || null,
        retryAfter: retryAfter || null,
        action: limited
          ? "Check Groq Console billing, usage limits, and rate limits for the GROQ_API_KEY configured on the ORNI Railway service."
          : "Check the ORNI provider configuration and deployment logs."
      });
    }

    const output = payload.choices?.[0]?.message?.content || "";

    if (!output) {
      const finishReason = payload.choices?.[0]?.finish_reason || "unknown";
      return res.status(502).json({
        error: "ORNI received an empty Groq model response",
        finishReason
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
      missionId,
      requestId,
      provider: "groq",
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
    readiness: "/ready",
    profile: "/api/orni/profile",
    status: "/api/orni/status",
    mission: "POST /api/orni/mission"
  });
});

export { app };

if (process.env.NODE_ENV !== "test") {
  const port = Number(process.env.PORT || 3000);
  app.listen(port, "0.0.0.0", () => {
    console.log(`ORNI API listening on port ${port}`);
  });
}
