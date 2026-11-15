import test from 'node:test';import assert from 'node:assert/strict';import {isOwnerAuthenticated,ownerGateEnabled} from '../src/lib/owner-auth.js';
const env={ONYX_OWNER_USERNAME:'owner',ONYX_OWNER_PASSWORD:'a-long-test-password'};
const basic=(u,p)=>'Basic '+Buffer.from(u+':'+p).toString('base64');
test('gate requires both credentials to be configured',()=>{assert.equal(ownerGateEnabled({}),false);assert.equal(ownerGateEnabled(env),true);assert.equal(isOwnerAuthenticated(basic('owner','a-long-test-password'),{}),false)});
test('only correct owner credentials are accepted',()=>{assert.equal(isOwnerAuthenticated(basic('owner','a-long-test-password'),env),true);assert.equal(isOwnerAuthenticated(basic('owner','incorrect'),env),false);assert.equal(isOwnerAuthenticated(basic('other','a-long-test-password'),env),false)});
test('malformed headers are rejected',()=>{for(const header of [undefined,'Bearer x','Basic !!!','Basic ','Basic '+Buffer.from('nocolon').toString('base64')])assert.equal(isOwnerAuthenticated(header,env),false)});
