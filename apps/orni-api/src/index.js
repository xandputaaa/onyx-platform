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


const referenceCinemaPlaybook = `
ORNI REFERENCE CINEMA PLAYBOOK — VERSION 2.1 — PERMANENT PRODUCTION STANDARD
These references are mandatory craft knowledge, not optional inspiration. Apply them to every retro animation, PS1/PS2 game cinematic, character short, fashion film and CELVANI campaign. Choose the correct style family; do not blend them carelessly.

SOURCE REFERENCES
A. DUMBDAYS! — "how to make ps1 / low poly / retro animations in blender (ULTIMATE MASTERCLASS)" (2023-11-10; https://youtu.be/MxTz8vNY7XE). Follow its published sequence: project settings; idea development; character creation; character texturing; character rigging; environment dressing; animation blocking and cameras; animation fine-tuning; pixel look and render settings; export; final touches. Its description mentions free assets and a low-poly car resource; do not assume unavailable assets or project files exist.
B. NoPoly — "How to make PSX/PS1 Graphics For Game Development In Blender" (2025-07-19; https://www.youtube.com/watch?v=nDaon0o_qoM). The published description establishes a Blender + Photoshop workflow for creating PSX graphics. Do not attribute unverified chapter-level details to this specific video. As additional PSX craft requirements in ORNI's own playbook, cover texture preparation, modeling, vertex painting, controlled vertex wobble and post-processing where suitable. Use Blender-native tools and free alternatives such as GIMP/Krita; no paid add-ons.
C. Luca Maxim TikTok — "you met me at a very Chinese time in my life". This is a separate early-2000s PS2 cutscene / character-comedy reference family: stylized game character in a deliberately low-detail world, dialogue framing, deadpan delivery, deliberate holds, simple cuts and a final line/punchline. Do not label this PS1. Use original characters and scripts; do not impersonate the creator or copy protected assets.

PRESET 1 — PS1 / PSX LOW-POLY ANIMATION
Never take a modern photoreal render and merely shrink or pixelate it. It must look intentionally authored for early 3D game constraints.
1. PROJECT DESIGN: define concept, duration, aspect ratio, frame rate, palette, polygon/detail budget, camera language and output resolution before modeling. Build a style frame.
2. CHARACTER: silhouette-first low-poly modeling; clear large forms; purposeful faceting and flat shading; avoid accidental smoothing, excessive bevels and noisy micro-detail. Use supplied references as modeling guides.
3. UV / TEXTURE: deliberate UV unwrap; small reusable texture atlases; hand-painted or baked low-res maps; restrained palette; nearest-neighbor sampling; consistent texel density; texture/vertex painting rather than excess geometry.
4. RIGGING: usable armature or articulated parts with named controls, sensible pivots and clean deformations. Pose-test before animation. Avoid intersections and sliding feet.
5. ENVIRONMENT: purposeful props, layered silhouettes, scale cues, composition, distance fog and coherent palette. Background supports the story.
6. BLOCKING: plan key poses and screen direction first. Every beat must read. Use chunky/stepped timing where appropriate but preserve physical clarity. Animate weight, head, hands, feet and secondary action; check foot contact and object continuity.
7. CAMERA: deliberate game-camera movement, motivated cuts, consistent screen direction and aspect-safe composition.
8. FINE-TUNING: refine anticipation, impact, follow-through, holds, walk cycles, facial/prop action and transitions. Remove accidental jitter, clipping, floating, foot sliding and unexplained position changes.
9. PSX GRAPHICS: flat/faceted geometry, low-res textures, nearest-neighbor filtering, limited palette, intentional dithering/banding, hard/simple lighting, distance fog and restrained low-precision artifacts. Controlled vertex wobble/displacement only when it supports the look; no silhouette destruction or distracting flicker. Texture warping/affine-like distortion may be approximated; never claim exact PS1 hardware emulation.
10. PIXEL PIPELINE: render deliberately low internal resolution, then upscale nearest-neighbor. Preserve crisp pixels; no bilinear blur, AI upscale or glossy modern effects. Apply quantization/dithering intentionally. Document master and delivery dimensions.
11. EXPORT: preview first, review the entire preview, fix issues, render final frames, encode via FFmpeg, validate duration/FPS/dimensions/playback/audio sync. Save editable .blend, preview PNG and final MP4; clean temporary frames only after successful encode.
12. QUALITY: check silhouette, UV seams, texture readability, style consistency, camera staging, animation arcs, foot contact, object permanence, flicker, z-fighting, clipping, pacing and encode. A blockout is never a finished piece.

MANDATORY REVISION GATE — CRASH-WOODS FEEDBACK (VERSION 2.1)
The first ORNI crash-woods output is a rejected gray-box prototype, not a style reference and not a finished deliverable. Do not reuse its scene as a final base without rebuilding the art direction and assets.

A. PS1/PS2 STYLE COHESION
- Treat the Luca Maxim / @santeluca early-2000s cutscene language and the two PSX tutorials as references for deliberate retro craft, not as permission to use generic primitives.
- The crash-woods brief belongs to the PS1/PS2 retro family. It must use coherent palette, texture density, pixel scale, fog, lighting, camera language and animation timing from shot to shot.
- Create actual authored texture assets: small photographic or hand-painted diffuse maps, dirt/grime/wear masks, road and bark textures, foliage variation, car paint/wear, glass, and crash-dummy surface detail. Pack reusable UV atlases where practical. Nearest-neighbour sampling and low-res texture resolution are mandatory; a 16x16 procedural tint/noise patch alone does NOT count as meaningful texture work.
- Add intentional color quantization, restrained dithering, distance fog, controlled texture wobble/vertex jitter only where suitable. Do not confuse dark exposure or flat untextured materials with PSX authenticity.

B. PURPOSE-BUILT ASSETS — NO PRIMITIVE GRAY-BOX SHORTCUTS
- Blockout primitives may be used only for early layout. Final shots require purpose-built silhouettes and custom mesh forms for the character, vehicle, trees, road props and environment.
- Car: coherent recognizable body proportions, hood/trunk transitions, wheel arches, windows, bumpers, lamps, tires, interior and damage details; avoid a stack of cubes.
- Crash dummy: purpose-built faceted head, torso, pelvis, hands, feet and articulated limbs with visible joint design. Use a real armature where feasible; otherwise named pivot groups with tested pivots. No floating disconnected blocks.
- Forest: layered tree silhouettes with varied canopy shapes, trunk geometry, undergrowth, roadside debris, ground texture and depth cues. Avoid repeated default cones as the dominant environment design.
- Use custom mesh construction, bevel control and silhouette checks. A low polygon count is an art direction constraint, not an excuse for unfinished geometry.

C. CINEMATOGRAPHY AND ANIMATION
- Build a storyboard and timecoded shot list before modeling. The crash, dummy exit, walk and moon reveal each need a readable motivated composition.
- Use deliberate shot changes, tracking/lead room, screen direction, impact framing, reaction hold, and a composed moon reveal. No camera clipping, unexplained camera falls or accidental geometry intersections.
- The dummy must visibly occupy the cabin, react to impact, exit through a visible door/opening, establish ground contact, then walk with alternating limbs, planted feet, body weight and secondary motion. The car must stop and remain spatially coherent.
- Review silhouettes and key poses at the actual delivery aspect ratio before full rendering.

D. MODERN 3D POLISH IS A SEPARATE PRESET / BENCHMARK
- The Louis Vuitton Default Cube challenge is a modern high-fidelity reference, not the target look for the retro crash-woods film. Its lessons—refined materials, physically based shading, controlled reflections, rich lighting, physics, compositing and cinematic camera work—belong in a separate modern-luxury preset.
- Never combine photoreal glossy shaders with PSX pixel art unless the brief explicitly asks for a hybrid. Select one coherent visual language per film and explain the choice.

E. ACCEPTANCE GATE
- Do not label a render production-ready because FFmpeg decoded it or because a 16x16 texture was attached to each material.
- Require visual evidence for: authored UV texture readability; custom silhouettes; coherent art direction; readable crash and exit; believable walk cycle and foot contact; camera staging; no clipping; deliberate lighting/fog; final frame composition.
- If any critical item fails, report “prototype / revision required” and do not call it finished. Deliver a contact sheet or style-frame preview for review before a costly full render. Keep all production free-only.

PRESET 2 — PS2 CUTSCENE / DEADPAN CHARACTER COMEDY
Keep separate from PS1. Aim for a 2000s console cutscene: recognizable expressive character, simpler low-texture world, deliberate cinematic framing, direct-to-camera or conversational composition, restrained mouth motion, deadpan timing, purposeful silence and a small number of motivated cuts. Structure: setup → character hold → statement/rant → pause → punchline/final line → end hold. The joke lands through performance and pacing, not random movement. Original scripts and characters only.

PRESET 3 — CELVANI FASHION CINEMA
Fashion-film cinematography and product-first storytelling. Preserve approved garment silhouette, fabric behavior, fit, seams, construction, embroidery, logo geometry and colors. Model fabric thickness, folds, stitching, hems and hardware deliberately. Use purposeful studio/location lighting, controlled camera moves and detail shots. Retro styling never authorizes changing CELVANI identity.

MANDATORY WORKFLOW FOR EVERY MISSION
A. Decompose brief: subject, action, tone, style family, aspect, duration, FPS, dialogue, assets, deliverables, constraints.
B. Reference breakdown: explicitly map techniques to DUMBDAYS, NoPoly or Luca Maxim. Separate verified source facts from ORNI's own choices. If footage/project file was not supplied and inspected, never claim frame-by-frame analysis or exact replication.
C. Preproduction: timecoded shot list, storyboard/keyframe thumbnails, camera/lens/movement, palette, lighting, character turnaround/silhouette, environment/prop list, asset/rig plan.
D. Build: editable Blender geometry, UV/materials, texture atlases, rig/articulated character, environment and camera; named collections and reusable assets.
E. Animate: block poses and camera, then refine timing, secondary action and transitions.
F. Preview: low-cost style frame and short preview; review composition, silhouette, motion and texture before final render.
G. Finish: render frames, apply selected pixel/post pipeline, FFmpeg encode, verify metadata and playback, then clean temporary files.
H. Report honestly: .blend, preview PNG and MP4 only when actually generated; actual dimensions/FPS/duration; QA pass/fail list. A plan, blockout or still is not a finished animation.

FREE-ONLY: Blender, Python, FFmpeg and open-source utilities only. No paid Kling, Seedance, OpenAI video, Fal, metered generation endpoints, paid plugins or paid assets. Preview before final rendering and respect CPU/RAM/runtime.
CELVANI SAFEGUARDS: preserve approved logo and product construction; no arbitrary text, third-party branding or invented marks. Keep exploratory variants labeled.
REQUIRED QUALITY SCORECARD BEFORE COMPLETION (0–5 with evidence): reference fidelity; silhouette; texture/materials; rig/animation; environment/art direction; camera/edit pacing; lighting/atmosphere; pixel/post pipeline; render/encode integrity; CELVANI identity integrity when applicable. Critical failures in story readability, brand accuracy, missing deliverables, playback or render integrity block completion. Never inflate scores; list revisions.
`;

const orniSystemPrompt = referenceCinemaPlaybook + `You are ORNI, the CELVANI specialist within the ONYX agent ecosystem. ONYX is your parent coordinator; the user is the final decision-maker.

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

app.get("/api/orni/reference-cinema", requireAgentToken, (_req,res) => res.json({ok:true,engine:"Blender + Python + FFmpeg",freeOnly:true,presets:[{id:"ps1",name:"PS1 Low-Poly Retro",references:[{creator:"DUMBDAYS!",title:"How to make PS1 / low-poly / retro animations in Blender",role:"animation and retro scene workflow",url:"https://youtu.be/MxTz8vNY7XE"},{creator:"NoPoly",title:"How to make PSX/PS1 Graphics For Game Development In Blender",role:"PSX graphics workflow using Blender and Photoshop",url:"https://www.youtube.com/watch?v=nDaon0o_qoM"}],summary:"DUMBDAYS! reference: the published chapter sequence from project settings and idea development through character creation/texturing/rigging, environment, animation blocking/cameras, fine-tuning, pixel render, export and final touches. NoPoly reference: its published description confirms a Blender + Photoshop workflow for PSX graphics; ORNI does not attribute unverified techniques to that video. ORNI adds its own free-tool PSX standards for UVs, restrained vertex effects, nearest-neighbor upscale and evidence-based QA."},{id:"ps2-cutscene",name:"PS2 Cutscene Comedy",reference:"Luca Maxim TikTok format",summary:"Stylized game character, deadpan dialogue framing, cinematic cuts, pauses, captions and nostalgic early-2000s game look."}],playbookVersion:"2.1",referenceCount:3,knowledgeSource:"permanent embedded ORNI production standard"}));

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


app.get("/api/orni/blender/job-status", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/job-status",{headers:{"Authorization":"Bearer "+process.env.ORNI_BLENDER_TOKEN},signal:AbortSignal.timeout(4000)});
    return res.status(r.status).json(await r.json().catch(()=>({error:"Invalid Blender job status"})));
  } catch { return res.status(502).json({error:"Could not read live Blender render progress."}); }
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
app.get("/api/orni/blender/preview", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/outputs/celvani_hoodie_blockout.png",{headers:{"Authorization":"Bearer "+process.env.ORNI_BLENDER_TOKEN},signal:AbortSignal.timeout(12000)});
    if(!r.ok) return res.status(r.status).json(await r.json().catch(()=>({error:"Preview not ready"})));
    res.set("Content-Type",r.headers.get("content-type")||"image/png"); res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  } catch { return res.status(502).json({error:"Could not retrieve the Blender preview."}); }
});
app.post("/api/orni/blender/scene/celvani-hoodie", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/api/scene/celvani-hoodie",{method:"POST",headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`,"Content-Type":"application/json"},body:"{}",signal:AbortSignal.timeout(90000)});
    return res.status(r.status).json(await r.json().catch(()=>({error:"Invalid Blender response"})));
  } catch(e) { return res.status(e?.name==="TimeoutError"?504:502).json({error:"Blender worker unavailable"}); }
});


app.post("/api/orni/blender/scene/retro-cinema", requireAgentToken, async (req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  const style=["ps2","crash-woods"].includes(req.body?.style)?req.body.style:"ps1";
  const duration=Math.max(3,Math.min(15,Number(req.body?.duration)||5));
  const aspectRatio=["9:16","16:9","1:1"].includes(req.body?.aspectRatio)?req.body.aspectRatio:"16:9";
  const caption=String(req.body?.caption||"").slice(0,120);
  try {
    const r=await fetch(base+"/api/scene/retro-cinema",{method:"POST",headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`,"Content-Type":"application/json"},body:JSON.stringify({style,duration,aspectRatio,caption}),signal:AbortSignal.timeout(560000)});
    return res.status(r.status).json(await r.json().catch(()=>({error:"Invalid Blender response"})));
  } catch(e) { return res.status(e?.name==="TimeoutError"?504:502).json({error:"Blender retro render timed out or worker is unavailable.",stage:"render"}); }
});

app.get("/api/orni/blender/retro-preview", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/outputs/orni_retro_preview.png",{headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`},signal:AbortSignal.timeout(30000)});
    if(!r.ok) return res.status(r.status).json(await r.json().catch(()=>({error:"Retro preview not ready"})));
    res.set("Content-Type","image/png");res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  } catch { return res.status(502).json({error:"Could not retrieve the Blender retro preview."}); }
});

app.get("/api/orni/blender/retro-video", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/outputs/orni_retro_cinema.mp4",{headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`},signal:AbortSignal.timeout(30000)});
    if(!r.ok) return res.status(r.status).json(await r.json().catch(()=>({error:"Retro video not ready"})));
    res.set("Content-Type","video/mp4");res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  } catch { return res.status(502).json({error:"Could not retrieve the Blender retro MP4."}); }
});


app.get("/api/orni/blender/crash-woods-preview", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/outputs/orni_crash_woods_preview.png",{headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`},signal:AbortSignal.timeout(30000)});
    if(!r.ok) return res.status(r.status).json(await r.json().catch(()=>({error:"Crash-woods preview not ready"})));
    res.set("Content-Type","image/png");res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  } catch { return res.status(502).json({error:"Could not retrieve the crash-woods preview."}); }
});
app.get("/api/orni/blender/crash-woods-video", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/outputs/orni_crash_woods_15s.mp4",{headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`},signal:AbortSignal.timeout(30000)});
    if(!r.ok) return res.status(r.status).json(await r.json().catch(()=>({error:"Crash-woods video not ready"})));
    res.set("Content-Type","video/mp4");res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  } catch { return res.status(502).json({error:"Could not retrieve the crash-woods MP4."}); }
});


app.get("/api/orni/blender/crash-woods-blend", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/outputs/orni_crash_woods.blend",{headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`},signal:AbortSignal.timeout(30000)});
    if(!r.ok) return res.status(r.status).json(await r.json().catch(()=>({error:"Crash-woods Blender file not ready"})));
    res.set("Content-Type","application/octet-stream");res.set("Content-Disposition",'attachment; filename="ORNI-crash-woods.blend"');res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  } catch { return res.status(502).json({error:"Could not retrieve the editable crash-woods scene."}); }
});
app.get("/api/orni/blender/retro-blend", requireAgentToken, async (_req,res) => {
  const base=(process.env.ORNI_BLENDER_API_URL||"").replace(/\/$/,"");
  if(!base||!process.env.ORNI_BLENDER_TOKEN) return res.status(503).json({error:"Blender private API is not configured."});
  try {
    const r=await fetch(base+"/outputs/orni_retro_cinema.blend",{headers:{"Authorization":`Bearer ${process.env.ORNI_BLENDER_TOKEN}`},signal:AbortSignal.timeout(30000)});
    if(!r.ok) return res.status(r.status).json(await r.json().catch(()=>({error:"Retro Blender file not ready"})));
    res.set("Content-Type","application/octet-stream");res.set("Content-Disposition",'attachment; filename="ORNI-retro-cinema.blend"');res.set("Cache-Control","no-store");
    return res.send(Buffer.from(await r.arrayBuffer()));
  } catch { return res.status(502).json({error:"Could not retrieve the editable retro scene."}); }
});

app.get("/api/orni/status", (_req, res) => {
  res.status(200).json({
    agent: "ORNI",
    domain: "CELVANI",
    status: "creative-pipeline",
    capabilities: {
      authenticatedMissionEndpoint: Boolean(process.env.ORNI_ACCESS_TOKEN && process.env.GROQ_API_KEY),
      celvaniIntelligence: "Groq model-assisted analysis; live research integration not connected",
      creativeStudio: "Reference Cinema playbook and procedural retro scene builder enabled",
      blenderAutomation: Boolean(process.env.ORNI_BLENDER_API_URL && process.env.ORNI_BLENDER_TOKEN) ? "connected" : "not_configured",
      visualWorkspaceStreaming: "noVNC viewer configured; live session depends on Blender worker availability",
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
    const requestBody = {
      model,
      messages: [
        { role: "system", content: orniSystemPrompt + "\\nReturn ONLY one valid JSON object with exactly these keys: mission (string), findings (string array), intelligence (string array), opportunities (string array), risks (string array), recommendation (string), approvalRequired (boolean), assumptions (string array), nextActions (string array). No markdown, no code fences, no extra keys. Keep each array to at most 3 concise items and avoid repeating information." },
        { role: "user", content: mission }
      ],
      // Keep the requested completion small enough for Groq's free OTPM allowance.
      max_completion_tokens: 512,
      temperature: 0.3,
      // Groq's Qwen endpoint may reject strict json_schema with
      // json_validate_failed. JSON-object mode is broadly supported; validate
      // the exact ORNI contract locally before returning a report.
      response_format: { type: "json_object" }
    };
    let response;
    for (let attempt = 0; attempt < 2; attempt += 1) {
      response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${process.env.GROQ_API_KEY}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(requestBody),
        signal: controller.signal
      });
      if (response.status !== 429 || attempt === 1) break;
      const retryAfter = Number(response.headers.get("retry-after") || "0");
      const delayMs = Number.isFinite(retryAfter) && retryAfter > 0
        ? Math.min(retryAfter * 1000, 35000)
        : 8500;
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const providerError = payload?.error || {};
      const limited = response.status === 429;
      const header = (name) => response.headers.get(name);
      const rateLimit = {
        limitRequests: header("x-ratelimit-limit-requests"),
        remainingRequests: header("x-ratelimit-remaining-requests"),
        resetRequests: header("x-ratelimit-reset-requests"),
        limitTokens: header("x-ratelimit-limit-tokens"),
        remainingTokens: header("x-ratelimit-remaining-tokens"),
        resetTokens: header("x-ratelimit-reset-tokens"),
        retryAfter: header("retry-after")
      };
      console.error("ORNI model provider returned an error", {
        status: response.status,
        type: providerError.type,
        code: providerError.code,
        message: providerError.message || null,
        model,
        rateLimit
      });
      return res.status(limited ? 429 : 502).json({
        error: limited ? "ORNI provider rejected the request" : "ORNI model provider request failed",
        category: limited ? "provider_rate_limited" : "provider_error",
        providerStatus: response.status,
        providerType: providerError.type || null,
        providerCode: providerError.code || null,
        providerMessage: providerError.message || null,
        model,
        rateLimit,
        action: limited
          ? "Inspect providerMessage and rateLimit headers to distinguish token-per-minute, request-per-minute, daily quota, and account-level restrictions. No billing change is assumed necessary."
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
      return res.status(502).json({ error: "ORNI returned a report that could not be parsed", model });
    }
    const stringFields = ["mission", "recommendation"];
    const arrayFields = ["findings", "intelligence", "opportunities", "risks", "assumptions", "nextActions"];
    const validObject = report && typeof report === "object" && !Array.isArray(report);
    const validStrings = validObject && stringFields.every(key => typeof report[key] === "string");
    const validArrays = validObject && arrayFields.every(key => Array.isArray(report[key]) && report[key].every(item => typeof item === "string"));
    if (!validObject || !validStrings || !validArrays || typeof report.approvalRequired !== "boolean") {
      return res.status(502).json({
        error: "ORNI model response did not match the required report structure",
        model,
        validation: { validObject, validStrings, validArrays, approvalRequired: typeof report?.approvalRequired === "boolean" }
      });
    }
    // Ignore any unexpected provider keys so the public contract stays stable.
    report = Object.fromEntries([...stringFields, ...arrayFields, "approvalRequired"].map(key => [key, report[key]]));

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
