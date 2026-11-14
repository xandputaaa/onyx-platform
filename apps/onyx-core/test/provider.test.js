import test from 'node:test';
import assert from 'node:assert/strict';
import {providerConfiguration,generateReply} from '../src/provider.js';
test('ChatGPT subscription alone never enables billable API',()=>{
 assert.equal(providerConfiguration({}).enabled,false);
 assert.equal(providerConfiguration({OPENAI_API_KEY:'secret'}).enabled,false);
 assert.equal(providerConfiguration({ONYX_OPENAI_ENABLED:'true'}).enabled,false);
});
test('provider disabled makes zero network calls',async()=>{
 let calls=0;
 const r=await generateReply('hello',{env:{},fetchImpl:async()=>{calls++;throw Error('should not call')}});
 assert.equal(r.reason,'PROVIDER_DISABLED');assert.equal(calls,0);
});
test('explicit opt-in uses Responses API with no storage and bounded output',async()=>{
 let request;
 const r=await generateReply('hello',{env:{ONYX_OPENAI_ENABLED:'true',OPENAI_API_KEY:'test',ONYX_OPENAI_MODEL:'test-model'},fetchImpl:async(url,opts)=>{
  request={url,opts};return {ok:true,json:async()=>({output:[{content:[{type:'output_text',text:'Hello.'}]}]})};
 }});
 assert.equal(r.reply,'Hello.');
 assert.equal(request.url,'https://api.openai.com/v1/responses');
 const payload=JSON.parse(request.opts.body);
 assert.equal(payload.store,false);assert.equal(payload.max_output_tokens,220);
});
test('provider HTTP failure is not misreported as AI success',async()=>{
 const r=await generateReply('hello',{env:{ONYX_OPENAI_ENABLED:'true',OPENAI_API_KEY:'test'},fetchImpl:async()=>({ok:false,status:429})});
 assert.equal(r.ok,false);assert.equal(r.reason,'PROVIDER_HTTP_429');
});
