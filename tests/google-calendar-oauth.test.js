import test from 'node:test';
import assert from 'node:assert/strict';
import {createGoogleCalendarAuthorization,consumeGoogleCalendarAuthorization} from '../src/lib/google-calendar-oauth.js';
const config={clientId:'test-client',redirectUri:'https://onyx.example.com/auth/google/callback'};
test('OAuth defaults to calendar read only and uses PKCE S256',()=>{
 const a=createGoogleCalendarAuthorization(config),u=new URL(a.url);
 assert.equal(u.searchParams.get('code_challenge_method'),'S256');
 assert.equal(u.searchParams.get('state'),a.state);
 assert.match(u.searchParams.get('scope'),/calendar.readonly/);
 assert.doesNotMatch(u.searchParams.get('scope'),/calendar.events/);
 assert.ok(a.verifier.length>=43);
});
test('write permission is opt in',()=>{
 const a=createGoogleCalendarAuthorization({...config,writeAccess:true});
 assert.match(new URL(a.url).searchParams.get('scope'),/calendar.events/);
});
test('OAuth state is one time and expires',()=>{
 const a=createGoogleCalendarAuthorization(config);
 assert.equal(consumeGoogleCalendarAuthorization(a,'wrong').ok,false);
 assert.equal(consumeGoogleCalendarAuthorization(a,a.state,a.createdAt+300001).ok,false);
 assert.equal(consumeGoogleCalendarAuthorization(a,a.state).ok,true);
 assert.equal(consumeGoogleCalendarAuthorization(a,a.state).ok,false);
});
test('OAuth requires secure callback',()=>{
 assert.throws(()=>createGoogleCalendarAuthorization({...config,redirectUri:'http://example.com/callback'}));
});
