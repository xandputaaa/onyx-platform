import http from 'node:http';
import { timingSafeEqual } from 'node:crypto';
import { describeOnyxCore } from './manifest.js';

export function authorized(header, secret) {
  if (!secret || typeof header !== 'string' || !/^Bearer\s+\S+$/i.test(header)) return false;
  const token = header.replace(/^Bearer\s+/i, '');
  const a = Buffer.from(token), b = Buffer.from(secret);
  return a.length === b.length && timingSafeEqual(a,b);
}
export function createOnyxServer({token=process.env.ONYX_CORE_TOKEN}={}) {
  return http.createServer((req,res)=>{
    res.setHeader('Content-Type','application/json; charset=utf-8');
    res.setHeader('Cache-Control','no-store');
    res.setHeader('X-Content-Type-Options','nosniff');
    const respond=(status,body)=>{res.statusCode=status;res.end(JSON.stringify(body));};
    const path=new URL(req.url||'/', 'http://localhost').pathname;
    if(req.method==='GET' && path==='/health')
      return respond(200,{ok:true,service:'onyx-core',version:'0.1-foundation',modelConnected:false,voiceConnected:false,missionExecutionEnabled:false});
    if(path.startsWith('/api/')) {
      if(!token) return respond(503,{error:'ONYX_CORE_TOKEN_NOT_CONFIGURED'});
      if(!authorized(req.headers.authorization,token)) return respond(401,{error:'UNAUTHORIZED'});
      if(req.method==='GET' && path==='/api/status') return respond(200,describeOnyxCore());
      return respond(404,{error:'NOT_FOUND'});
    }
    return respond(404,{error:'NOT_FOUND'});
  });
}
if(process.argv[1] && import.meta.url===new URL('file://'+process.argv[1]).href) {
  const port=Number(process.env.PORT||3000);
  createOnyxServer().listen(port,'0.0.0.0',()=>console.log('ONYX Core listening on '+port));
}
