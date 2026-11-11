const MODELS = {
  image: "black-forest-labs/flux-3-image-klein",
  kling: "klingai/kling-v4-flash",
  minimax: "minimax/h3-highspeed",
};

function json(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...headers },
  });
}

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin");
  const allowed = env.ORNI_ALLOWED_ORIGIN;
  if (!origin || !allowed || origin !== allowed) return {};
  return {
    "access-control-allow-origin": allowed,
    "access-control-allow-methods": "GET, POST, OPTIONS",
    "access-control-allow-headers": "Authorization, Content-Type",
    "access-control-max-age": "86400",
    Vary: "Origin",
  };
}

function authorized(request, env) {
  const expected = env.ORNI_WORKER_TOKEN;
  const supplied = request.headers.get("Authorization")?.replace(/^Bearer\s+/i, "");
  return Boolean(expected && supplied && supplied === expected);
}

function normalizeImage(result) {
  const value = result?.result ?? result;
  const image = value?.image ?? value?.images?.[0]?.url ?? value?.url;
  return typeof image === "string" ? { url: image } : { error: "FLUX returned no image URL." };
}

function normalizeVideo(result) {
  const value = result?.result ?? result;
  const video = value?.video ?? value?.task?.content?.url ?? value?.url;
  const task = value?.task ?? null;
  return typeof video === "string" ? { url: video, task } : { task, error: "Video model did not return a completed video URL." };
}

export default {
  async fetch(request, env) {
    const cors = corsHeaders(request, env);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    const url = new URL(request.url);

    if (url.pathname === "/health" && request.method === "GET") {
      return json({ ok: true, service: "orni-cloudflare-ai", models: MODELS }, 200, cors);
    }
    if (!authorized(request, env)) return json({ error: "Unauthorized" }, 401, cors);
    if (request.method !== "POST") return json({ error: "Method not allowed" }, 405, cors);

    let body;
    try { body = await request.json(); }
    catch { return json({ error: "Expected a JSON request body." }, 400, cors); }
    const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";
    if (!prompt) return json({ error: "A prompt is required." }, 400, cors);

    try {
      if (url.pathname === "/image") {
        const images = Array.isArray(body.images)
          ? body.images.filter((item) => typeof item === "string" && /^https:\/\//i.test(item)).slice(0, 10)
          : [];
        const input = { prompt, resolution: ["2k", "4k"].includes(body.resolution) ? body.resolution : "1k" };
        if (images.length) input.images = images;
        const result = await env.AI.run(MODELS.image, input);
        const output = normalizeImage(result);
        if (!output.url) return json({ error: output.error, model: MODELS.image }, 502, cors);
        return json({ ok: true, type: "image", model: MODELS.image, output, generatedAt: new Date().toISOString() }, 200, cors);
      }

      if (url.pathname === "/video") {
        const model = body.model === "minimax" ? MODELS.minimax : MODELS.kling;
        const duration = Number(body.duration ?? 5);
        if (!Number.isInteger(duration)) return json({ error: "duration must be a whole number of seconds." }, 400, cors);
        let input;

        if (model === MODELS.kling) {
          if (duration < 3 || duration > 20) return json({ error: "Kling duration must be between 3 and 20 seconds." }, 400, cors);
          const aspect_ratio = ["21:9", "16:9", "9:16", "1:1"].includes(body.aspect_ratio) ? body.aspect_ratio : "9:16";
          input = { aspect_ratio, duration, prompt };
        } else {
          if (duration < 4 || duration > 15) return json({ error: "MiniMax duration must be between 4 and 15 seconds." }, 400, cors);
          const ratio = ["adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"].includes(body.aspect_ratio) ? body.aspect_ratio : "9:16";
          const content = [{ type: "text", text: prompt }];
          if (typeof body.first_frame === "string" && /^https:\/\//i.test(body.first_frame)) content.push({ type: "image_url", image_url: { url: body.first_frame }, role: "first_frame" });
          if (typeof body.last_frame === "string" && /^https:\/\//i.test(body.last_frame)) content.push({ type: "image_url", image_url: { url: body.last_frame }, role: "last_frame" });
          if (Array.isArray(body.reference_images)) {
            for (const image of body.reference_images.slice(0, 4)) {
              if (typeof image === "string" && /^https:\/\//i.test(image)) content.push({ type: "image_url", image_url: { url: image }, role: "reference_image" });
            }
          }
          input = { content, duration, ratio, resolution: "768P" };
        }

        const result = await env.AI.run(model, input);
        const output = normalizeVideo(result);
        if (!output.url) return json({ error: output.error, model, task: output.task }, 502, cors);
        return json({ ok: true, type: "video", model, output, generatedAt: new Date().toISOString() }, 200, cors);
      }

      return json({ error: "Not found. Use /image or /video." }, 404, cors);
    } catch (error) {
      console.error("ORNI AI model request failed", { path: url.pathname, name: error?.name });
      return json({ error: "Cloudflare AI generation failed.", detail: error?.message || "Unknown model error." }, 502, cors);
    }
  },
};
