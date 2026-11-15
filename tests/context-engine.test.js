import test from 'node:test';
import assert from 'node:assert/strict';
import {createContextState,grantAccess,revokeAccess,authorizeAction,selectContext,proposeAction} from '../src/lib/context-engine.js';

test('no permission without an explicit grant',()=>{
 const state=createContextState();
 assert.equal(authorizeAction(state,{source:'gmail',domain:'communications',capability:'communications.read'}).allowed,false);
});
test('read grant does not authorize send',()=>{
 const state=grantAccess(createContextState(),{source:'gmail',domain:'communications',capabilities:['communications.read']});
 assert.equal(authorizeAction(state,{source:'gmail',domain:'communications',capability:'communications.read'}).allowed,true);
 assert.equal(authorizeAction(state,{source:'gmail',domain:'communications',capability:'communications.send',approved:true}).allowed,false);
});
test('mutations require explicit approval even when granted',()=>{
 const state=grantAccess(createContextState(),{source:'calendar',domain:'schedule',capabilities:['schedule.modify']});
 assert.equal(authorizeAction(state,{source:'calendar',domain:'schedule',capability:'schedule.modify'}).reason,'explicit_approval_required');
 assert.equal(authorizeAction(state,{source:'calendar',domain:'schedule',capability:'schedule.modify',approved:true}).allowed,true);
});
test('cross-domain grants are rejected',()=>{
 const state=grantAccess(createContextState(),{source:'calendar',domain:'schedule',capabilities:['finance.read','schedule.read']});
 assert.deepEqual(state.grants.calendar.schedule,['schedule.read']);
 assert.equal(authorizeAction(state,{source:'calendar',domain:'schedule',capability:'finance.read',approved:true}).allowed,false);
 assert.throws(()=>proposeAction(state,{domain:'schedule',capability:'finance.transfer',summary:'transfer'}));
});
test('revocation removes access and context',()=>{
 const state=grantAccess(createContextState(),{source:'gmail',domain:'communications',capabilities:['communications.read']});
 const revoked=revokeAccess(state,'gmail');
 assert.equal(authorizeAction(revoked,{source:'gmail',domain:'communications',capability:'communications.read'}).allowed,false);
 assert.deepEqual(selectContext(revoked,['communications']).sources,[]);
});
