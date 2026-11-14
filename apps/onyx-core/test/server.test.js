import test from 'node:test';
import assert from 'node:assert/strict';
import { createOnyxServer, authorized } from '../src/server.js';
test('token comparison rejects missing and incorrect tokens',()=>{
 assert.equal(authorized('Bearer valid-token','valid-token'),true);
 for(const h of [undefined,'Bearer invalid','Basic valid-token','Bearer valid-token extra']) assert.equal(authorized(h,'valid-token'),false);
 assert.equal(authorized('Bearer valid-token',''),false);
});
async function request(server,path,auth){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try {const url='http://127.0.0.1:'+server.address().port+path;const response=await fetch(url,{headers:auth?{Authorization:auth}:{}});return {status:response.status,body:await response.json()};}
 finally {await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));}
}
test('health is public but does not claim AI or voice are connected',async()=>{
 const r=await request(createOnyxServer({token:'secret'}),'/health');
 assert.equal(r.status,200);assert.equal(r.body.modelConnected,false);assert.equal(r.body.voiceConnected,false);
});
test('protected status fails closed without configured token',async()=>{
 const r=await request(createOnyxServer({token:''}),'/api/status');
 assert.equal(r.status,503);
});
test('protected status rejects unauthorized requests',async()=>{
 const r=await request(createOnyxServer({token:'secret'}),'/api/status');
 assert.equal(r.status,401);
});
test('authorized status lists planned specialists without claiming connectivity',async()=>{
 const r=await request(createOnyxServer({token:'secret'}),'/api/status','Bearer secret');
 assert.equal(r.status,200);assert.equal(r.body.operational,false);
 assert.equal(r.body.specialists.find(x=>x.id==='nova').connection,'NOT_CONNECTED');
});
