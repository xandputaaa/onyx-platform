import test from "node:test";import assert from "node:assert/strict";import {STATES,MODES,normalizeState,normalizeMode,shapeRadius,displayState,safePanelName,clamp} from "./state.mjs";
test("all seven visual states are available",()=>assert.deepEqual(STATES,["idle","listening","thinking","speaking","alert","muted","offline"]));
test("both device modes exist",()=>assert.deepEqual(MODES,["glasses","holo"]));
test("invalid inputs fall back safely",()=>{assert.equal(normalizeState("execute"),"idle");assert.equal(normalizeMode("production"),"glasses");assert.equal(safePanelName("secrets"),"missions");});
test("shape deformation stays finite and bounded",()=>{for(const s of STATES)for(let a=0;a<6.28;a+=.1)for(const level of [-1,0,.4,1,5]){const r=shapeRadius(a,13,s,level);assert.ok(Number.isFinite(r)&&r>=.7&&r<=1.45);}});
test("thinking produces more angular protrusion than idle",()=>{const sample=s=>Array.from({length:180},(_,i)=>shapeRadius(i*Math.PI/90,2,s));const spread=s=>Math.max(...sample(s))-Math.min(...sample(s));assert.ok(spread("thinking")>spread("idle"));});
test("speaking responds to audio envelope",()=>assert.notEqual(shapeRadius(0,2,"speaking",0),shapeRadius(0,2,"speaking",1)));
test("labels and clamp work",()=>{assert.equal(displayState("muted"),"MIC MUTED");assert.equal(clamp(Infinity,0,1),0);assert.equal(clamp(5,0,1),1);});
