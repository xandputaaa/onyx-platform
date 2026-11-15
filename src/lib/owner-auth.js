import {createHash,timingSafeEqual} from 'node:crypto';
/** Temporary single-owner HTTP Basic Auth gate for the standalone preview.
 * Use HTTPS. Configure ONYX_OWNER_USERNAME and ONYX_OWNER_PASSWORD in Railway,
 * never in the repo. This is not a substitute for a full identity provider.
 */
export function isOwnerAuthenticated(header,env=process.env){
 const user=env.ONYX_OWNER_USERNAME,password=env.ONYX_OWNER_PASSWORD;
 if(!user||!password)return false;
 if(typeof header!=='string'||!header.startsWith('Basic '))return false;
 let decoded;
 try{const encoded=header.slice(6);if(!/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)||encoded.length>4096)return false;decoded=Buffer.from(encoded,'base64').toString('utf8')}catch{return false}
 const separator=decoded.indexOf(':');if(separator<0)return false;
 const [givenUser,givenPassword]=[decoded.slice(0,separator),decoded.slice(separator+1)];
 const digest=s=>createHash('sha256').update(s).digest();
 return timingSafeEqual(digest(givenUser),digest(user))&&timingSafeEqual(digest(givenPassword),digest(password));
}
export function ownerGateEnabled(env=process.env){return Boolean(env.ONYX_OWNER_USERNAME&&env.ONYX_OWNER_PASSWORD)}
