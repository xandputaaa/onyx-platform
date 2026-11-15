import React, {useState} from 'react';
import {createContextState,grantAccess,revokeAccess,authorizeAction,selectContext,proposeAction} from './lib/context-engine.js';

const sources=[
  {id:'google-calendar',name:'Google Calendar',domain:'schedule',capabilities:['schedule.read','schedule.propose','schedule.modify'],detail:'Schedule and availability'},
  {id:'gmail',name:'Gmail',domain:'communications',capabilities:['communications.read','communications.send'],detail:'Messages and follow-ups'},
  {id:'instagram',name:'Instagram',domain:'communications',capabilities:['communications.read'],detail:'Messages and account context, subject to provider permissions'},
  {id:'onepay',name:'OnePay',domain:'finance',capabilities:['finance.read','finance.summarize'],detail:'Balances and payday context, if supported'},
  {id:'celvani',name:'CELVANI',domain:'celvani',capabilities:['celvani.analyze','celvani.publish'],detail:'Brand operations and publishing'},
  {id:'karen',name:'KAREN',domain:'systems',capabilities:['systems.inspect'],detail:'Financial intelligence system'}
];

export default function Systems(){
  const [context,setContext]=useState(createContextState);
  const [selected,setSelected]=useState('google-calendar');
  const [notice,setNotice]=useState('No live accounts are connected. This is a permission-policy preview.');
  const [pending,setPending]=useState(null);
  const source=sources.find(s=>s.id===selected);
  const granted=context.grants[source.id]?.[source.domain]||[];
  function toggle(capability){
    if(granted.includes(capability)){
      setContext(s=>{const next=revokeAccess(s,source.id,source.domain);const keep=granted.filter(c=>c!==capability);return keep.length?grantAccess(next,{source:source.id,domain:source.domain,capabilities:keep}):next;});
    }else setContext(s=>grantAccess(s,{source:source.id,domain:source.domain,capabilities:[...granted,capability]}));
    setNotice('Local policy preview updated. This does not authorize or connect any provider.');
  }
  function request(){
    const capability=source.capabilities.find(c=>['schedule.modify','communications.send','celvani.publish'].includes(c));
    if(!capability){setNotice('No action requiring approval is configured for this source.');return;}
    const result=authorizeAction(context,{source:source.id,domain:source.domain,capability});
    if(result.reason==='grant_required'){setNotice('Enable the capability first.');return;}
    const next=proposeAction(context,{domain:source.domain,capability,summary:'Example request from '+source.name});
    setContext(next);setPending(next.suggestions.at(-1));setNotice('Example proposal created; nothing has been sent or changed.');
  }
  return <div className="systems-page">
    <div className="sectionhead"><span className="eyebrow">SYSTEMS / PERMISSIONS</span><h2>Connections.</h2><p>Choose what ONYX may see and what requires your approval.</p></div>
    <div className="panel"><div className="panelhead"><h3>ACCOUNT CONNECTIONS</h3><span className="eyebrow">DEMO / NOT CONNECTED</span></div>
      <p className="muted">Provider sign-in and encrypted server-side tokens are not implemented. The controls below only preview ONYX's access policy in this browser session.</p>
      <div className="systems-source-list">{sources.map(s=><button key={s.id} className={'system '+(selected===s.id?'open':'')} onClick={()=>{setSelected(s.id);setPending(null)}}><span><strong>{s.name}</strong><small>{s.detail}</small></span><span>{selected===s.id?'●':'○'}</span></button>)}</div>
    </div>
    <div className="panel"><div className="panelhead"><h3>{source.name.toUpperCase()} / ACCESS</h3><span className="eyebrow">LOCAL POLICY</span></div>
      {source.capabilities.map(cap=><label className="toggle" key={cap}><span>{cap.replace('.',' / ')}</span><input type="checkbox" checked={granted.includes(cap)} onChange={()=>toggle(cap)}/></label>)}
      <div className="actions"><button className="outline" onClick={()=>{setContext(s=>revokeAccess(s,source.id));setPending(null);setNotice('Local policy grants cleared for '+source.name+'.')}}>Revoke local grants</button><button className="outline" onClick={request}>Try approval preview</button></div>
      <p className="muted">Changing a permission here does not enable provider access. A real connection must use OAuth, server-side enforcement, token encryption, and a revocation endpoint.</p>
    </div>
    {pending&&<div className="panel"><h3>APPROVAL REQUIRED</h3><p>{pending.summary}</p><p className="muted">Preview only: approving this example will not execute a real-world action.</p><div className="actions"><button className="primary" onClick={()=>{setNotice('Demo approval recorded. No external action executed.');setPending(null)}}>Approve demo</button><button className="outline" onClick={()=>{setNotice('Demo proposal rejected.');setPending(null)}}>Reject</button></div></div>}
    <div className="panel"><h3>CONTEXT VISIBILITY</h3><p className="muted">Domains represented in the current session: {selectContext(context,['schedule','health','finance','celvani','communications','systems']).sources.map(s=>s.source).join(', ')||'None'}. No message contents or bank balances are stored by this preview.</p></div>
    <p className="notice" role="status">{notice}</p>
  </div>;
}
