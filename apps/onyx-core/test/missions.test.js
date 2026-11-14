import test from 'node:test';
import assert from 'node:assert/strict';
import {createMissionStore} from '../src/missions.js';
test('mission requires valid bounded title',()=>{
 const s=createMissionStore();
 assert.equal(s.create({title:''}).error,'INVALID_TITLE');
 assert.equal(s.create({title:'x'.repeat(121)}).error,'INVALID_TITLE');
});
test('mission approvals never execute actions',()=>{
 const s=createMissionStore();
 const {mission}=s.create({title:'Prepare morning briefing'});
 assert.equal(mission.status,'DRAFT');
 assert.equal(s.transition(mission.id,'approve').error,'INVALID_TRANSITION');
 assert.equal(s.transition(mission.id,'submit').mission.status,'AWAITING_APPROVAL');
 assert.equal(s.transition(mission.id,'approve').mission.status,'APPROVED');
 assert.equal(s.transition(mission.id,'run').error,'INVALID_TRANSITION');
 assert.equal(s.get(mission.id).mission.status,'APPROVED');
 assert.deepEqual(s.audit().map(e=>e.event),['CREATED','SUBMIT','APPROVE']);
});
test('cancelled missions cannot be reactivated',()=>{
 const s=createMissionStore();
 const id=s.create({title:'Test'}).mission.id;
 assert.equal(s.transition(id,'cancel').mission.status,'CANCELLED');
 assert.equal(s.transition(id,'submit').error,'INVALID_TRANSITION');
});
test('list returns copies, not mutable internal state',()=>{
 const s=createMissionStore();
 s.create({title:'Test'});
 const a=s.list();a[0].title='tampered';a[0].history.push({});
 assert.equal(s.list()[0].title,'Test');assert.equal(s.list()[0].history.length,1);
});
