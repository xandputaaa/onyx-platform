import {randomBytes,createHash} from 'node:crypto';

const AUTH_ENDPOINT='https://accounts.google.com/o/oauth2/v2/auth';
const SCOPES=Object.freeze({calendarRead:'https://www.googleapis.com/auth/calendar.readonly',calendarWrite:'https://www.googleapis.com/auth/calendar.events'});
const base64url=buffer=>buffer.toString('base64url');

/** Creates a short-lived, single-use authorization attempt. Keep verifier and state server-side. */
export function createGoogleCalendarAuthorization({clientId,redirectUri,writeAccess=false}) {
  if(!clientId||!redirectUri||!redirectUri.startsWith('https://')) throw new Error('Google OAuth configuration missing');
  const state=base64url(randomBytes(32));
  const verifier=base64url(randomBytes(48));
  const challenge=base64url(createHash('sha256').update(verifier).digest());
  const url=new URL(AUTH_ENDPOINT);
  for(const [key,value] of Object.entries({client_id:clientId,redirect_uri:redirectUri,response_type:'code',scope:[SCOPES.calendarRead,...(writeAccess?[SCOPES.calendarWrite]:[])].join(' '),state,code_challenge:challenge,code_challenge_method:'S256',access_type:'offline',prompt:'consent'})) url.searchParams.set(key,value);
  return {url:url.toString(),state,verifier,createdAt:Date.now()};
}

/** Reject mismatched, expired, or replayed attempts before exchanging any code. */
export function consumeGoogleCalendarAuthorization(attempt,returnedState,now=Date.now()) {
  if(!attempt||attempt.consumed||typeof returnedState!=='string'||returnedState!==attempt.state||now-attempt.createdAt>300000||now<attempt.createdAt) return {ok:false};
  attempt.consumed=true;
  return {ok:true,verifier:attempt.verifier};
}
export const GOOGLE_CALENDAR_SCOPES=SCOPES;
