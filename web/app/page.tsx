'use client';
import {useState, useRef, useEffect, FormEvent} from 'react';
type Citation = {label:string; title:string; url:string; excerpt:string; course_code:string|null};
type Result = {answer:string; status:'answered'|'insufficient_evidence'|'error'; citations:Citation[]; request_id:string; latency_ms:number};
type Turn = {question:string; result?:Result; error?:string};
const suggestions = ['What is CS 124?', 'What prerequisites are listed for CS 225?', 'Which courses discuss artificial intelligence?'];
export default function Home() {
 const [question,setQuestion]=useState(''); const [turns,setTurns]=useState<Turn[]>([]); const [busy,setBusy]=useState(false); const end=useRef<HTMLDivElement>(null);
 useEffect(()=>{end.current?.scrollIntoView({behavior:'smooth',block:'end'});},[turns,busy]);
 async function ask(value:string) {
  if(busy || !value.trim()) return;
  const q=value.trim(); setQuestion('');setBusy(true);setTurns(t=>[...t,{question:q}]);
  try {
   const base=process.env.NEXT_PUBLIC_API_BASE_URL;
   if(!base) throw Error('The catalog service has not been configured yet.');
   const response=await fetch(base.replace(/\/$/,'')+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,catalog_year:'2026-27'}),signal:AbortSignal.timeout(55000)});
   if(!response.ok) throw Error(response.status===429?'The request limit has been reached. Please try again later.':'The catalog service is unavailable. Please try again shortly.');
   const result:Result=await response.json(); setTurns(t=>t.map((v,i)=>i===t.length-1?{...v,result}:v));
  }catch(e){setTurns(t=>t.map((v,i)=>i===t.length-1?{...v,error:e instanceof Error?e.message:'Unable to reach the catalog service.'}:v));}finally{setBusy(false);}
 }
 function submit(e:FormEvent){e.preventDefault();void ask(question);}
 return <main>
  <header><div className="topline"><span className="kicker">THE GEN ACADEMY <span className="muted">/ WEEK 2</span></span><span className="project">A GYST NOW PROJECT</span></div>
  <div className="title-row"><h1>University<br/>Catalog Advisor<span className="dot">.</span></h1><div className="catalog-badge"><span className="badge-dot"/>UIUC · 2026–2027</div></div>
  <div className="rule"/><p className="intro">Find your way through the catalog.</p><p className="description">Ask about Computer Science and Mathematics courses, or explore Computer Science BS requirements. Answers come with evidence from the official catalog.</p>
  <p className="disclaimer">Independent educational prototype. Not an official university service or a substitute for academic advising.</p></header>
  <section className="workspace" aria-label="Catalog conversation"><div className="section-label"><span>01 / ASK THE CATALOG</span><span className="muted">3 SELECTED SOURCES</span></div>
  {turns.length===0?<div className="empty"><div className="book" aria-hidden="true">↗</div><h2>A good question is a good start.</h2><p>Look up a course. Explore a subject. Understand a requirement.</p><div className="suggestions">{suggestions.map(s=><button key={s} disabled={busy} onClick={()=>void ask(s)}>{s}<span aria-hidden="true">↗</span></button>)}</div></div>:<div className="conversation">{turns.map((t,i)=><article key={i}><div className="question"><span className="kicker">YOUR QUESTION</span><p>{t.question}</p></div>{t.error?<div role="alert" className="error">{t.error}<button onClick={()=>void ask(t.question)} disabled={busy}>Try again</button></div>:t.result?<div className="answer"><span className="kicker">{t.result.status==='answered'?'CATALOG ANSWER':'LIMITED EVIDENCE'}</span><p className="answer-text">{t.result.answer}</p>{t.result.citations.length>0&&<div className="sources"><div className="kicker">SUPPORTING SOURCES</div>{t.result.citations.map(c=><div key={c.label}><a href={c.url} target="_blank" rel="noopener noreferrer">{c.label} {c.title} ↗</a><details><summary>Read retrieved evidence</summary><p>{c.excerpt}</p></details></div>)}</div>}<div className="response-meta">{(t.result.latency_ms/1000).toFixed(1)}s · Ref {t.result.request_id.slice(0,8)}</div></div>:null}</article>)}</div>}
  <div role="status" aria-live="polite">{busy&&<p className="loading">Searching the catalog and checking evidence…</p>}</div><div ref={end}/>
  <form onSubmit={submit}><label htmlFor="question">Your catalog question</label><div className="input-row"><textarea id="question" rows={2} value={question} onChange={e=>setQuestion(e.target.value)} maxLength={1000} placeholder="e.g. What are the prerequisites for CS 225?" disabled={busy}/><button className="send" type="submit" disabled={busy||!question.trim()}>{busy?'Searching…':'Ask question'}<span aria-hidden="true">↗</span></button></div><div className="form-note"><span>CS courses · MATH courses · CS BS requirements</span><span>{question.length}/1000</span></div></form></section>
  <section className="scope"><span className="kicker">A NOTE ON SCOPE</span><p>This advisor explains published catalog text. It cannot confirm live course availability, evaluate transfer credit, or determine whether you are ready to graduate.</p></section>
  <footer><div><span className="kicker">OFFICIAL SOURCE MATERIAL</span><div className="footer-links"><a href="https://catalog.illinois.edu/courses-of-instruction/cs/">CS catalog ↗</a><a href="https://catalog.illinois.edu/courses-of-instruction/math/">MATH catalog ↗</a><a href="https://catalog.illinois.edu/undergraduate/engineering/computer-science-bs/">CS BS requirements ↗</a></div></div><a className="github" href="https://github.com/gyst-now/Group-27-project">View project on GitHub ↗</a></footer>
 </main>;
}
