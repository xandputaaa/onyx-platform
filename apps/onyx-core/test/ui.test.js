import test from 'node:test';
import assert from 'node:assert/strict';
import { createOnyxServer } from '../src/server.js';
test('command center serves HTML with restrictive security headers',async()=>{
 const server=createOnyxServer({token:'secret'});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const r=await fetch('http://127.0.0.1:'+server.address().port+'/');
  const html=await r.text();
  assert.equal(r.status,200);
  assert.match(r.headers.get('content-type'),/text\/html/);
  assert.match(r.headers.get('content-security-policy'),/default-src 'none'/);
  assert.match(html,/ONYX/);
  assert.match(html,/Connection unverified/);
  assert.match(html,/prefers-reduced-motion/);
 }finally{await new Promise(resolve=>server.close(resolve));}
});
