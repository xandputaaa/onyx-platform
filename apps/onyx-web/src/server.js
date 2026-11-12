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

app.get("/api/orni/blender/preview", async (_req,res) => {
  if (!process.env.ORNI_ACCESS_TOKEN) return res.status(503).json({error:"ONYX-to-ORNI authentication is not configured."});
  try {
    const r=await fetch(orniBase+"/api/orni/blender/preview",{headers:{"Authorization":"Bearer "+process.env.ORNI_ACCESS_TOKEN},signal:AbortSignal.timeout(15000)});
    const type=r.headers.get("content-type")||"application/json"; res.status(r.status).set("Content-Type",type);
    if(type.startsWith("image/")) return res.send(Buffer.from(await r.arrayBuffer()));
    return res.send(await r.text());
  } catch { return res.status(502).json({error:"Could not reach ORNI preview service."}); }
});
app.get("/api/orni/blender/status", async (_req,res) => {
  if (!process.env.ORNI_ACCESS_TOKEN) return res.status(503).json({connected:false,state:"not_configured",message:"ONYX-to-ORNI authentication is not configured."});
  try {
    const r=await fetch(`${orniBase}/api/orni/blender/status`,{headers:{"Authorization":`Bearer ${process.env.ORNI_ACCESS_TOKEN}`},signal:AbortSignal.timeout(6000)});
    const body=await r.json().catch(()=>({}));
    if(body.connected) body.viewerUrl="https://orni-blender-production.up.railway.app/orni.html";
    return res.status(r.status).json(body);
  } catch { return res.status(502).json({connected:false,state:"unreachable",viewerUrl:null,message:"Could not reach the Blender control service."}); }
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
      signal: AbortSignal.timeout(route.includes("retro-cinema") ? 600000 : 120000)
    });
    const payload = await upstream.json().catch(() => ({ error: "ORNI returned an unreadable response." }));
    return res.status(upstream.status).json(payload);
  } catch (error) {
    return res.status(error?.name === "TimeoutError" ? 504 : 502).json({ error: "Could not reach ORNI creative services.", retryable: true });
  }
}
app.get("/api/orni/reference-cinema", (req, res) => orniForward(req, res, "/api/orni/reference-cinema"));
app.post("/api/orni/blender/scene/retro-cinema", (req,res) => orniForward(req,res,"/api/orni/blender/scene/retro-cinema","POST"));

let crashWoodsTriggerUsed=false;
app.get("/api/orni/internal/trigger-crash-woods", async (req,res) => {
  const supplied=String(req.query?.key||"");
  const expected=process.env.ORNI_BUILD_TRIGGER_TOKEN||"";
  if(!expected||supplied.length!==expected.length||supplied!==expected) return res.status(404).json({error:"Not found"});
  if(crashWoodsTriggerUsed) return res.status(409).json({error:"This one-time production trigger has already been used."});
  crashWoodsTriggerUsed=true;
  if(!process.env.ORNI_ACCESS_TOKEN) return res.status(503).json({error:"ORNI authentication is not configured."});
  try{
    const upstream=await fetch(`${orniBase}/api/orni/blender/scene/retro-cinema`,{
      method:"POST",
      headers:{"Authorization":"Bearer "+process.env.ORNI_ACCESS_TOKEN,"Content-Type":"application/json"},
      body:JSON.stringify({style:"crash-woods",duration:15,aspectRatio:"9:16",caption:""}),
      signal:AbortSignal.timeout(20000)
    });
    const payload=await upstream.json().catch(()=>({error:"ORNI returned an unreadable response."}));
    return res.status(upstream.status).json({trigger:"one-time crash-woods production",...payload});
  }catch(error){
    return res.status(error?.name==="TimeoutError"?504:502).json({error:"Could not hand the production job to ORNI.",detail:String(error?.message||error)});
  }
});


app.get("/api/orni/blender/retro-preview", async (_req,res) => {
  if(!process.env.ORNI_ACCESS_TOKEN)return res.status(503).json({error:"ONYX-to-ORNI authentication is not configured."});
  try{
    const r=await fetch(orniBase+"/api/orni/blender/retro-preview",{headers:{"Authorization":"Bearer "+process.env.ORNI_ACCESS_TOKEN},signal:AbortSignal.timeout(30000)});
    if(!r.ok)return res.status(r.status).json(await r.json().catch(()=>({error:"Retro preview not ready"})));
    res.set("Content-Type","image/png");res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  }catch{return res.status(502).json({error:"Could not reach ORNI retro preview."});}
});
app.get("/api/orni/blender/retro-video", async (_req,res) => {
  if(!process.env.ORNI_ACCESS_TOKEN)return res.status(503).json({error:"ONYX-to-ORNI authentication is not configured."});
  try{
    const r=await fetch(orniBase+"/api/orni/blender/retro-video",{headers:{"Authorization":"Bearer "+process.env.ORNI_ACCESS_TOKEN},signal:AbortSignal.timeout(30000)});
    if(!r.ok)return res.status(r.status).json(await r.json().catch(()=>({error:"Retro video not ready"})));
    res.set("Content-Type","video/mp4");res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  }catch{return res.status(502).json({error:"Could not reach ORNI retro video output."});}
});

app.get("/api/orni/blender/crash-woods-preview", async (_req,res) => {
  if(!process.env.ORNI_ACCESS_TOKEN)return res.status(503).json({error:"ONYX-to-ORNI authentication is not configured."});
  try{
    const r=await fetch(orniBase+"/api/orni/blender/crash-woods-preview",{headers:{"Authorization":"Bearer "+process.env.ORNI_ACCESS_TOKEN},signal:AbortSignal.timeout(30000)});
    if(!r.ok)return res.status(r.status).json(await r.json().catch(()=>({error:"Crash-woods preview not ready"})));
    res.set("Content-Type","image/png");res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  }catch{return res.status(502).json({error:"Could not reach ORNI crash-woods preview."});}
});
app.get("/api/orni/blender/crash-woods-video", async (_req,res) => {
  if(!process.env.ORNI_ACCESS_TOKEN)return res.status(503).json({error:"ONYX-to-ORNI authentication is not configured."});
  try{
    const r=await fetch(orniBase+"/api/orni/blender/crash-woods-video",{headers:{"Authorization":"Bearer "+process.env.ORNI_ACCESS_TOKEN},signal:AbortSignal.timeout(30000)});
    if(!r.ok)return res.status(r.status).json(await r.json().catch(()=>({error:"Crash-woods video not ready"})));
    res.set("Content-Type","video/mp4");res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  }catch{return res.status(502).json({error:"Could not reach ORNI crash-woods video output."});}
});

app.get("/api/orni/blender/crash-woods-blend", async (_req,res) => {
  if(!process.env.ORNI_ACCESS_TOKEN)return res.status(503).json({error:"ONYX-to-ORNI authentication is not configured."});
  try{
    const r=await fetch(orniBase+"/api/orni/blender/crash-woods-blend",{headers:{"Authorization":"Bearer "+process.env.ORNI_ACCESS_TOKEN},signal:AbortSignal.timeout(30000)});
    if(!r.ok)return res.status(r.status).json(await r.json().catch(()=>({error:"Crash-woods Blender file not ready"})));
    res.set("Content-Type","application/octet-stream");res.set("Content-Disposition",'attachment; filename="ORNI-crash-woods.blend"');res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  }catch{return res.status(502).json({error:"Could not reach ORNI crash-woods Blender file."});}
});
app.get("/api/orni/blender/retro-blend", async (_req,res) => {
  if(!process.env.ORNI_ACCESS_TOKEN)return res.status(503).json({error:"ONYX-to-ORNI authentication is not configured."});
  try{
    const r=await fetch(orniBase+"/api/orni/blender/retro-blend",{headers:{"Authorization":"Bearer "+process.env.ORNI_ACCESS_TOKEN},signal:AbortSignal.timeout(30000)});
    if(!r.ok)return res.status(r.status).json(await r.json().catch(()=>({error:"Retro Blender file not ready"})));
    res.set("Content-Type","application/octet-stream");res.set("Content-Disposition",'attachment; filename="ORNI-retro-cinema.blend"');res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  }catch{return res.status(502).json({error:"Could not reach ORNI retro Blender file."});}
});
app.get("/api/orni/creative/status", (req, res) => orniForward(req, res, "/api/orni/creative/status"));
app.get("/api/orni/assets", (req, res) => orniForward(req, res, "/api/orni/assets"));
app.post("/api/orni/assets", (req, res) => orniForward(req, res, "/api/orni/assets", "POST"));
app.post("/api/orni/designs/generate", (req, res) => orniForward(req, res, "/api/orni/designs/generate", "POST"));
app.post("/api/orni/videos/generate", (req, res) => orniForward(req, res, "/api/orni/videos/generate", "POST"));
app.get("/api/orni/blender/job-status", (req, res) => orniForward(req, res, "/api/orni/blender/job-status"));
app.get("/api/orni/blender/status", (req, res) => orniForward(req, res, "/api/orni/blender/status"));
app.post("/api/orni/blender/scene/celvani-hoodie", (req, res) => orniForward(req, res, "/api/orni/blender/scene/celvani-hoodie", "POST"));

app.post("/api/orni/research", (req,res) => orniForward(req,res,"/api/orni/research","POST"));

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
      body: JSON.stringify({ mission: mission.trim(), requestId: crypto.randomUUID(), liveResearch: req.body?.liveResearch===true, researchQuery: typeof req.body?.researchQuery==="string" ? req.body.researchQuery.slice(0,300) : undefined }),
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