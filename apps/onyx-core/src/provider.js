// No subscription-cookie scraping, hidden credentials, or implicit billing.
// The default mode is deliberately offline. OpenAI API is opt-in and requires
// separately provisioned API credentials and an explicit enable flag.
export function providerConfiguration(env=process.env){
 const enabled=env.ONYX_OPENAI_ENABLED==='true';
 const key=env.OPENAI_API_KEY||'';
 const model=env.ONYX_OPENAI_MODEL||'gpt-4.1-mini';
 return {mode:enabled&&key?'OPENAI_API':'OFFLINE',enabled:enabled&&Boolean(key),model,subscriptionSupported:false};
}
export async function generateReply(message,{env=process.env,fetchImpl=fetch}={}){
 const config=providerConfiguration(env);
 if(!config.enabled)return {ok:false,reason:'PROVIDER_DISABLED',mode:'OFFLINE'};
 const controller=new AbortController();
 const timer=setTimeout(()=>controller.abort(),12000);
 try{
  const response=await fetchImpl('https://api.openai.com/v1/responses',{
   method:'POST',signal:controller.signal,
   headers:{Authorization:'Bearer '+env.OPENAI_API_KEY,'Content-Type':'application/json'},
   body:JSON.stringify({model:config.model,max_output_tokens:220,store:false,
    instructions:'You are ONYX, a concise, supportive personal chief of staff with a natural KAREN-inspired conversational style. Do not claim to have accessed tools, real-time data, memories, voice, or specialists. Do not claim actions were executed. Be transparent about uncertainty.',
    input:message})
  });
  if(!response.ok)return {ok:false,reason:'PROVIDER_HTTP_'+response.status,mode:'OPENAI_API'};
  const body=await response.json();
  const reply=(body.output||[]).flatMap(x=>x.content||[]).filter(x=>x.type==='output_text').map(x=>x.text).join('\n').trim();
  if(!reply)return {ok:false,reason:'EMPTY_PROVIDER_RESPONSE',mode:'OPENAI_API'};
  return {ok:true,reply,mode:'OPENAI_API',modelConnected:true,actionsTaken:[],source:'OpenAI Responses API'};
 }catch(e){return {ok:false,reason:e.name==='AbortError'?'PROVIDER_TIMEOUT':'PROVIDER_UNAVAILABLE',mode:'OPENAI_API'};}
 finally{clearTimeout(timer);}
}
