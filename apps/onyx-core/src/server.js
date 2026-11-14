import http from 'node:http';
import { readFileSync } from 'node:fs';
import { timingSafeEqual } from 'node:crypto';
import { describeOnyxCore } from './manifest.js';
import { respondToMessage } from './conversation.js';
import { generateReply, providerConfiguration } from './provider.js';
import { createMissionStore } from './missions.js';

export function authorized(header, secret) {
  if (!secret || typeof header !== 'string' || !/^Bearer\s+\S+$/i.test(header)) return false;
  const token = header.replace(/^Bearer\s+/i, '');
  const a = Buffer.from(token), b = Buffer.from(secret);
  return a.length === b.length && timingSafeEqual(a,b);
}
export function createOnyxServer({token=process.env.ONYX_CORE_TOKEN,missionStore=createMissionStore()}={}) {
  return http.createServer(async(req,res)=>{
    res.setHeader('Content-Type','application/json; charset=utf-8');
    res.setHeader('Cache-Control','no-store');
    res.setHeader('X-Content-Type-Options','nosniff');
    const respond=(status,body)=>{res.statusCode=status;res.end(JSON.stringify(body));};
    const path=new URL(req.url||'/', 'http://localhost').pathname;
    if(req.method==='GET' && path==='/'){
      res.setHeader('Content-Type','text/html; charset=utf-8');
      res.setHeader('Content-Security-Policy',"default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'");
      res.setHeader('Referrer-Policy','no-referrer');
      res.statusCode=200;
      return res.end(readFileSync(new URL('../public/index.html',import.meta.url)));
    }
    if(req.method==='GET' && path==='/health')
      return respond(200,{ok:true,service:'onyx-core',version:'0.1-foundation',modelConnected:false,modelConfigured:providerConfiguration().enabled,voiceConnected:false,missionExecutionEnabled:false});
    if(path.startsWith('/api/')) {
      if(!token) return respond(503,{error:'ONYX_CORE_TOKEN_NOT_CONFIGURED'});
      if(!authorized(req.headers.authorization,token)) return respond(401,{error:'UNAUTHORIZED'});
      if(req.method==='GET' && path==='/api/status') return respond(200,describeOnyxCore());
      if(req.method==='GET' && path==='/api/missions')return respond(200,{missions:missionStore.list(),persistent:false,executionEnabled:false});
      if(req.method==='GET' && path==='/api/missions/audit')return respond(200,{events:missionStore.audit()});
      if(req.method==='POST' && (path==='/api/missions'||/^\\/api\\/missions\\/[0-9a-f-]+\\/transition$/.test(path))){
        let data='';
        try{
          for await(const chunk of req){data+=chunk;if(data.length>4096)return respond(413,{error:'PAYLOAD_TOO_LARGE'});}
          const body=JSON.parse(data);
          const result=path==='/api/missions'?missionStore.create(body):missionStore.transition(path.split('/')[3],body?.action);
          return respond(result.error?(result.error==='MISSION_LIMIT_REACHED'?429:400):200,result);
        }catch{return respond(400,{error:'INVALID_JSON'});}
      }
      if(req.method==='POST' && path==='/api/conversation') {
        let data='';
        try {
          for await(const chunk of req){data+=chunk;if(data.length>4096)return respond(413,{error:'PAYLOAD_TOO_LARGE'});}
          const payload=JSON.parse(data);
          const answer=respondToMessage(payload?.message);
          if(!answer.ok)return respond(400,answer);
          const generated=await generateReply(payload.message);
          return respond(200,generated.ok?generated:{...answer,providerStatus:generated.reason});
        } catch {return respond(400,{error:'INVALID_JSON'});}
      }
      return respond(404,{error:'NOT_FOUND'});
    }
    return respond(404,{error:'NOT_FOUND'});
  });
}
if(process.argv[1] && import.meta.url===new URL('file://'+process.argv[1]).href) {
  const port=Number(process.env.PORT||3000);
  createOnyxServer().listen(port,'0.0.0.0',()=>console.log('ONYX Core listening on '+port));
}
