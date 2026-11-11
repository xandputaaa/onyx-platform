import test, { before, after } from "node:test";
import assert from "node:assert/strict";

process.env.NODE_ENV = "test";
delete process.env.ORNI_ACCESS_TOKEN;
delete process.env.OPENAI_API_KEY;
delete process.env.ONYX_ORIGIN;

const { app } = await import("../src/index.js");
let server;
let baseUrl;

before(async () => {
  server = app.listen(0, "127.0.0.1");
  await new Promise(resolve => server.once("listening", resolve));
  baseUrl = `http://127.0.0.1:${server.address().port}`;
});

after(async () => {
  await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
});

test("health endpoint reports process health", async () => {
  const response = await fetch(`${baseUrl}/health`);
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.ok, true);
  assert.equal(body.service, "orni-api");
});

test("readiness is 503 until independent credentials are configured", async () => {
  const response = await fetch(`${baseUrl}/ready`);
  const body = await response.json();
  assert.equal(response.status, 503);
  assert.equal(body.status, "not_ready");
  assert.deepEqual(body.missing.sort(), ["OPENAI_API_KEY", "ORNI_ACCESS_TOKEN"]);
});

test("profile identifies ORNI as the CELVANI specialist under ONYX", async () => {
  const response = await fetch(`${baseUrl}/api/orni/profile`);
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.agent, "ORNI");
  assert.equal(body.parent, "ONYX");
  assert.equal(body.domain, "CELVANI");
});

test("mission endpoint rejects requests without the ONYX bearer token", async () => {
  const response = await fetch(`${baseUrl}/api/orni/mission`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mission: "Review the next CELVANI product sample." })
  });
  assert.equal(response.status, 401);
});

test("mission endpoint validates ONYX correlation IDs after authentication", async () => {
  process.env.ORNI_ACCESS_TOKEN = "test-only-token";
  try {
    const response = await fetch(baseUrl + "/api/orni/mission", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer test-only-token" },
      body: JSON.stringify({ mission: "Review CELVANI sample.", requestId: 42 })
    });
    assert.equal(response.status, 400);
    assert.match((await response.json()).error, /requestId/);
  } finally { delete process.env.ORNI_ACCESS_TOKEN; }
});
