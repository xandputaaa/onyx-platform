// Deterministic, offline-safe conversation contract. This is NOT a language model.
const intents=[
 {pattern:/\b(status|connected|online|working)\b/i,reply:'ONYX Core is available, but conversational AI, voice and specialist integrations have not been verified. I can show the current capability status.'},
 {pattern:/\b(orni|celvani|blender)\b/i,reply:'ORNI is the CELVANI and Blender specialist. Its live connection to ONYX Core is not verified yet.'},
 {pattern:/\b(karen|bitcoin|btc|kalshi|sports)\b/i,reply:'KAREN is the separate BTC and sports specialist. ONYX has not connected to its live data yet.'},
 {pattern:/\b(nova|creator|content)\b/i,reply:'NOVA is planned for creator operations and is not connected yet.'},
 {pattern:/\b(mission|task|do this|send|publish|deploy)\b/i,reply:'Mission execution is not enabled. I can help outline a plan, but I cannot claim an action has been completed.'}
];
export function respondToMessage(input){
 if(typeof input!=='string'||!input.trim())return {ok:false,error:'MESSAGE_REQUIRED'};
 if(input.length>2000)return {ok:false,error:'MESSAGE_TOO_LONG'};
 const match=intents.find(x=>x.pattern.test(input));
 return {ok:true,reply:match?.reply||'I can discuss ONYX plans and capabilities, but an AI conversation provider is not connected. No external action was taken.',mode:'OFFLINE_FOUNDATION',modelConnected:false,actionsTaken:[],source:'ONYX Core local capability manifest'};
}
