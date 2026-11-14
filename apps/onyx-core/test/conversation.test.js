import test from 'node:test';
import assert from 'node:assert/strict';
import { respondToMessage } from '../src/conversation.js';
test('offline conversation does not pretend AI or tools are connected',()=>{
 for(const input of ['Hello ONYX','Check KAREN status','Deploy the website','How is ORNI?']){
  const r=respondToMessage(input);
  assert.equal(r.ok,true);assert.equal(r.modelConnected,false);
  assert.deepEqual(r.actionsTaken,[]);assert.equal(r.mode,'OFFLINE_FOUNDATION');
 }
});
test('rejects missing or oversized messages',()=>{
 assert.equal(respondToMessage('  ').error,'MESSAGE_REQUIRED');
 assert.equal(respondToMessage('x'.repeat(2001)).error,'MESSAGE_TOO_LONG');
});
test('mission response does not claim completion',()=>{
 const r=respondToMessage('Deploy the website');
 assert.match(r.reply,/not enabled/i);
});
