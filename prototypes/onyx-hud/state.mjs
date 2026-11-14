export const STATES = Object.freeze(["idle","listening","thinking","speaking","alert","muted","offline"]);
export const MODES = Object.freeze(["glasses","holo"]);
export function normalizeState(value) { return STATES.includes(value) ? value : "idle"; }
export function normalizeMode(value) { return MODES.includes(value) ? value : "glasses"; }
export function clamp(value,min,max) { return Math.min(max,Math.max(min,Number.isFinite(value)?value:min)); }
export function shapeRadius(angle,time,state,level=0) {
  const s=normalizeState(state), audio=clamp(level,0,1);
  const wobble=Math.sin(3*angle+time*.9)*.027+Math.sin(7*angle-time*1.1)*.018;
  const stretch=s==="listening" ? .11 : s==="speaking" ? .075+audio*.12 : s==="thinking" ? .13 : .025;
  const elongation=stretch*Math.cos(2*angle-time*.35);
  const tendril=s==="thinking" ? .11*Math.pow(Math.max(0,Math.cos(9*angle+time*.85)),12) : 0;
  const alert=s==="alert" ? .065*Math.sin(time*7) : 0;
  const still=s==="muted"||s==="offline" ? .12 : 1;
  return clamp(1+still*(wobble+elongation+tendril+alert),.7,1.45);
}
export function displayState(state) {return ({idle:"STANDBY",listening:"LISTENING",thinking:"PROCESSING",speaking:"RESPONDING",alert:"ALERT",muted:"MIC MUTED",offline:"OFFLINE"})[normalizeState(state)];}
export function safePanelName(value) { return ["karen","celvani","missions"].includes(value) ? value : "missions"; }
