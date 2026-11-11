import express from "express";
import helmet from "helmet";
import path from "node:path";
import { fileURLToPath } from "node:url";

const app = express();
const here = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 8080);
const orniBase = (process.env.ORNI_BASE_URL || "https://orni-api-production.up.railway.app").replace(/\/$/, "");

app.disable("x-powered-by");
app.use(helmet({ contentSecurityPolicy: false }));
app.use(express.json({ limit: "24mb" }));
app.use(express.static(path.join(here, "../public"), { extensions: ["html"] }));

app.get("/health", (_req, res) => res.json({ ok: true, service: "onyx-web" }));
app.get("/api/agents", async (_req, res) => {
  let orni = { status: "unknown" };
  try {
    const r = await fetch(`${orniBase}/api/orni/status`, { signal: AbortSignal.timeout(5000) });
    const body = await r.json();
    orni = { status: r.ok ? "reachable" : "degraded", details: body };
  } catch {
    orni = { status: "unreachable" };
  }
  res.json({
    platform: "ONYX",
    agents: [
      { id: "onyx", name: "ONYX", role: "Chief of Staff", status: "online" },
      { id: "orni", name: "ORNI", role: "CELVANI Specialist", status: orni.status }
    ]
  });
});


app.get("/api/orni/ready", async (_req, res) => {
  try {
    const r = await fetch(`${orniBase}/ready`, { signal: AbortSignal.timeout(5000) });
    const body = await r.json().catch(() => ({ status: "unreadable" }));
    return res.status(r.ok ? 200 : 503).json({ ...body, provider: "Groq" });
  } catch {
    return res.status(502).json({ ok: false, status: "unreachable", provider: "Groq" });
  }
});

app.get("/api/orni/blender/status", async (_req, res) => {
  const workerBase = (process.env.ORNI_BLENDER_BASE_URL || "").replace(/\/$/, "");
  const viewerUrl = process.env.ORNI_BLENDER_VIEW_URL || "";
  if (!workerBase) {
    return res.json({
      connected: false,
      state: "not_configured",
      message: "The Blender worker has not been provisioned or connected yet."
    });
  }
  try {
    const r = await fetch(`${workerBase}/`, { signal: AbortSignal.timeout(4000) });
    const body = await r.json().catch(() => ({}));
    return res.status(r.ok ? 200 : 502).json({ connected: r.ok, state: r.ok ? "connected" : "degraded", viewerUrl: viewerUrl || null, worker: body });
  } catch {
    return res.status(502).json({ connected: false, state: "unreachable", viewerUrl: viewerUrl || null, message: "The configured Blender worker could not be reached." });
  }
});


async function orniForward(req, res, route, method = "GET") {
  if (!process.env.ORNI_ACCESS_TOKEN) return res.status(503).json({ error: "ORNI connection is not configured." });
  try {
    const upstream = await fetch(`${orniBase}${route}`, {
      method,
      headers: {
        "Authorization": `Bearer ${process.env.ORNI_ACCESS_TOKEN}`,
        ...(method !== "GET" ? { "Content-Type": "application/json" } : {})
      },
      ...(method !== "GET" ? { body: JSON.stringify(req.body || {}) } : {}),
      signal: AbortSignal.timeout(120000)
    });
    const payload = await upstream.json().catch(() => ({ error: "ORNI returned an unreadable response." }));
    return res.status(upstream.status).json(payload);
  } catch (error) {
    return res.status(error?.name === "TimeoutError" ? 504 : 502).json({ error: "Could not reach ORNI creative services.", retryable: true });
  }
}
app.get("/api/orni/creative/status", (req, res) => orniForward(req, res, "/api/orni/creative/status"));
app.get("/api/orni/assets", (req, res) => orniForward(req, res, "/api/orni/assets"));
app.post("/api/orni/assets", (req, res) => orniForward(req, res, "/api/orni/assets", "POST"));
app.post("/api/orni/designs/generate", (req, res) => orniForward(req, res, "/api/orni/designs/generate", "POST"));
app.post("/api/orni/videos/generate", (req, res) => orniForward(req, res, "/api/orni/videos/generate", "POST"));

app.post("/api/orni/mission", async (req, res) => {
  const mission = req.body?.mission;
  if (typeof mission !== "string" || !mission.trim() || mission.length > 6000) {
    return res.status(400).json({ error: "Provide a mission between 1 and 6000 characters." });
  }
  if (!process.env.ORNI_ACCESS_TOKEN) {
    return res.status(503).json({ error: "ORNI connection is not configured on the server." });
  }
  try {
    const upstream = await fetch(`${orniBase}/api/orni/mission`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.ORNI_ACCESS_TOKEN}`
      },
      body: JSON.stringify({ mission: mission.trim(), requestId: crypto.randomUUID() }),
      signal: AbortSignal.timeout(90000)
    });
    const payload = await upstream.json().catch(() => ({ error: "ORNI returned an unreadable response." }));
    return res.status(upstream.status).json(payload);
  } catch (error) {
    const timedOut = error?.name === "TimeoutError";
    return res.status(timedOut ? 504 : 502).json({
      error: timedOut ? "ORNI mission timed out." : "Could not reach ORNI.",
      retryable: true
    });
  }
});

app.use((_req, res) => res.sendFile(path.join(here, "../public/index.html")));
app.listen(port, "0.0.0.0", () => console.log(`ONYX web listening on ${port}`));