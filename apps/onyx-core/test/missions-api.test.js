import test from 'node:test';
import assert from 'node:assert/strict';
import {createOnyxServer} from '../src/server.js';

async function withServer(run){
 const server=createOnyxServer({token:'test-secret'});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const base='http://127.0.0.1:'+server.address().port;
  const request=async(path,{method='GET',body,authorized=true}={})=>{
   const headers=authorized?{Authorization:'Bearer test-secret'}:{};
   if(body!==undefined)headers['Content-Type']='application/json';
   const response=await fetch(base+path,{method,headers,body:body===undefined?undefined:JSON.stringify(body)});
   return {status:response.status,body:await response.json()};
  };
  await run(request);
 }finally{await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));}
}
test('mission API enforces auth and creates a draft',async()=>withServer(async request=>{
 const denied=await request('/api/missions',{authorized:false});
 assert.equal(denied.status,401);
 const created=await request('/api/missions',{method:'POST',body:{title:'Morning briefing'}});
 assert.equal(created.status,200);
 assert.equal(created.body.mission.status,'DRAFT');
 const list=await request('/api/missions');
 assert.equal(list.body.missions.length,1);
 assert.equal(list.body.executionEnabled,false);
 assert.equal(list.body.persistent,false);
}));
test('mission submit and approve routes are reachable; execution is impossible',async()=>withServer(async request=>{
 const created=await request('/api/missions',{method:'POST',body:{title:'Plan the week'}});
 const id=created.body.mission.id;
 const submitted=await request('/api/missions/'+id+'/transition',{method:'POST',body:{action:'submit'}});
 assert.equal(submitted.status,200);
 assert.equal(submitted.body.mission.status,'AWAITING_APPROVAL');
 const approved=await request('/api/missions/'+id+'/transition',{method:'POST',body:{action:'approve'}});
 assert.equal(approved.status,200);
 assert.equal(approved.body.mission.status,'APPROVED');
 const run=await request('/api/missions/'+id+'/transition',{method:'POST',body:{action:'run'}});
 assert.equal(run.status,400);
 assert.equal(run.body.error,'INVALID_TRANSITION');
 const audit=await request('/api/missions/audit');
 assert.deepEqual(audit.body.events.map(x=>x.event),['CREATED','SUBMIT','APPROVE']);
}));
test('mission endpoints reject invalid input',async()=>withServer(async request=>{
 const bad=await request('/api/missions',{method:'POST',body:{title:''}});
 assert.equal(bad.status,400);
 assert.equal(bad.body.error,'INVALID_TITLE');
 const missing=await request('/api/missions/00000000-0000-4000-8000-000000000000/transition',{method:'POST',body:{action:'approve'}});
 assert.equal(missing.status,400);
 assert.equal(missing.body.error,'NOT_FOUND');
}));
