import {randomUUID} from 'node:crypto';
const MAX_MISSIONS=100;
export function createMissionStore({clock=()=>new Date().toISOString()}={}){
 const missions=new Map();
 const audit=[];
 const snapshot=m=>({...m,history:m.history.map(h=>({...h}))});
 const record=(m,event)=>{const at=clock();m.updatedAt=at;m.history.push({event,at});audit.push({missionId:m.id,event,at});};
 return {
  create({title,description=''}={}){
   if(typeof title!=='string'||!title.trim()||title.length>120) return {error:'INVALID_TITLE'};
   if(typeof description!=='string'||description.length>2000)return {error:'INVALID_DESCRIPTION'};
   if(missions.size>=MAX_MISSIONS)return {error:'MISSION_LIMIT_REACHED'};
   const now=clock(),m={id:randomUUID(),title:title.trim(),description,status:'DRAFT',createdAt:now,updatedAt:now,history:[]};
   record(m,'CREATED');missions.set(m.id,m);return {mission:snapshot(m)};
  },
  list(){return [...missions.values()].map(snapshot)},
  get(id){const m=missions.get(id);return m?{mission:snapshot(m)}:{error:'NOT_FOUND'}},
  transition(id,action){
   const m=missions.get(id);if(!m)return {error:'NOT_FOUND'};
   const transitions={DRAFT:{submit:'AWAITING_APPROVAL',cancel:'CANCELLED'},AWAITING_APPROVAL:{approve:'APPROVED',reject:'CANCELLED'},APPROVED:{cancel:'CANCELLED'}};
   const next=transitions[m.status]?.[action];
   if(!next)return {error:'INVALID_TRANSITION'};
   m.status=next;record(m,action.toUpperCase());return {mission:snapshot(m)};
  },
  audit(){return audit.map(e=>({...e}))}
 };
}
// In-memory draft/approval tracking only. No action runner or external effects.
