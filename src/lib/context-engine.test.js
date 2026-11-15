import test from "node:test";
import assert from "node:assert/strict";
import { createContextState, grantAccess, revokeAccess, authorizeAction, selectContext, proposeAction } from "./context-engine.js";

test("default deny and explicit approval for consequential actions", () => {
  const empty = createContextState();
  assert.equal(authorizeAction(empty, {source:"calendar",domain:"schedule",capability:"schedule.modify"}).allowed, false);
  const state = grantAccess(empty, {source:"calendar",domain:"schedule",capabilities:["schedule.read","schedule.modify"]});
  assert.equal(authorizeAction(state, {source:"calendar",domain:"schedule",capability:"schedule.read"}).allowed, true);
  assert.equal(authorizeAction(state, {source:"calendar",domain:"schedule",capability:"schedule.modify"}).reason, "explicit_approval_required");
  assert.equal(authorizeAction(state, {source:"calendar",domain:"schedule",capability:"schedule.modify",approved:true}).allowed, true);
  assert.equal(authorizeAction(revokeAccess(state,"calendar","schedule"), {source:"calendar",domain:"schedule",capability:"schedule.read"}).allowed, false);
});

test("context selection excludes unrelated domains and raw account data", () => {
  const state = grantAccess(createContextState(), {source:"calendar",domain:"schedule",capabilities:["schedule.read"]});
  assert.deepEqual(selectContext(state, ["finance"]).sources, []);
  assert.deepEqual(selectContext(state, ["schedule"]).sources, [{source:"calendar",domains:["schedule"]}]);
});

test("proposals remain pending and never execute", () => {
  const next = proposeAction(createContextState(), {domain:"finance",capability:"finance.transfer",summary:"Move funds"});
  assert.equal(next.suggestions[0].status,"pending");
});
