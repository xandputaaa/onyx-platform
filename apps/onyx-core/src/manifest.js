export const SPECIALISTS=Object.freeze([
 {id:'orni',name:'ORNI',domain:'CELVANI / Blender',connection:'UNVERIFIED'},
 {id:'karen',name:'KAREN',domain:'BTC / sports',connection:'UNVERIFIED',access:'READ_ONLY'},
 {id:'nova',name:'NOVA',domain:'Creator operations',connection:'NOT_CONNECTED'}
]);
export const CAPABILITIES=Object.freeze([
 {id:'conversation',name:'Natural dialogue',status:'PLANNED'},
 {id:'briefings',name:'Daily briefings',status:'PLANNED'},
 {id:'missions',name:'Permissioned missions',status:'PLANNED'},
 {id:'vision',name:'Consent-based visual analysis',status:'PLANNED'},
 {id:'voice',name:'Interruptible voice',status:'PLANNED'},
 {id:'integrations',name:'Specialist coordination',status:'PLANNED'}
]);
export function describeOnyxCore(){return {name:'ONYX',role:'Personal chief of staff',protocol:'KAREN-inspired conversational interface',version:'0.1-foundation',operational:false,specialists:SPECIALISTS,capabilities:CAPABILITIES,disclaimer:'No integrations or intelligence services are verified by this static manifest.'};}
