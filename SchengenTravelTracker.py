#!/usr/bin/env python3
"""
Schengen Travel Tracker
Usage:  python3 SchengenTravelTracker.py
        Browser opens automatically at http://localhost:8765

Data is stored in SchengenTravelTracker_data.json (same folder as this script).
Press Ctrl+C to stop.

© 2026 Kit Norriss — GNU General Public License v3.0
https://github.com/CrestixUK/Schengen-Travel-Tracker

──────────────────────────────────────────────────
Changelog
──────────────────────────────────────────────────
v1.1.0  (2026-06-02)  builds 1002-1007
  [1007] - Switched to semver + build number versioning
  [1006] - Person name always shown above their trip list
  [1005] - Travelling selector in add form uses person colour + tick/cross
  [1005] - Top tab bar: tick/cross removed, colour dot retained
  [1004] - Per-person colour assignment (stored in data file)
  [1004] - People selector shows colour dot per person
  [1004] - Rename bar includes colour swatch picker (8 colours)
  [1003] - Planned trips sort toggle (nearest/furthest first)
  [1003] - Sort preference persisted to data file under settings
  [1002] - Footer version driven from VERSION constant
  [1002] - Changelog added to script header

v1.0.0  (2026-06-01)  build 1001
  [1001] - Initial release
  [1001] - Two-person Schengen 90/180-day tracking
  [1001] - Planned trip analysis with breach and at-limit warnings
  [1001] - Projected peak accounting for ongoing and planned trips
  [1001] - Next available entry date with consecutive days count
  [1001] - Available days hint when adding a trip (forward-scan,
            accounts for old trips dropping off the rolling window)
  [1001] - Transit day support (shared boundary day counts once)
  [1001] - Overlap validation (true overlaps blocked, transit allowed)
  [1001] - Older trips hidden by default behind toggle
  [1001] - Dark mode via system preference
  [1001] - Fully offline, no external dependencies
  [1001] - Data stored in plain JSON file alongside the script
──────────────────────────────────────────────────
"""

SEMVER = "v1.1.0"
BUILD  = 1007
VERSION = f"{SEMVER}+{BUILD}"

import copy
import json
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 8765
DATA_FILE = Path(__file__).parent / "SchengenTravelTracker_data.json"

DEFAULT_DATA = {
    "people": {
        "p1": {"name": "Person 1", "color": "#3b82f6", "trips": []},
        "p2": {"name": "Person 2", "color": "#f97316", "trips": []},
    },
    "settings": {
        "plannedSortAsc": True
    }
}


def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "settings" not in data:
                data["settings"] = copy.deepcopy(DEFAULT_DATA["settings"])
            # Assign default colors to people if missing
            default_colors = ["#3b82f6", "#f97316", "#22c55e", "#a855f7"]
            for i, pid in enumerate(data.get("people", {})):
                if "color" not in data["people"][pid]:
                    data["people"][pid]["color"] = default_colors[i % len(default_colors)]
            return data
        except Exception:
            pass
    return copy.deepcopy(DEFAULT_DATA)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CSS -- no external dependencies, full light/dark mode support
# ---------------------------------------------------------------------------
CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0 }
:root {
  --bg:#fff; --bg2:#f7f7f5; --bg3:#eeedea;
  --c:#1a1a18; --c2:#5f5e5a; --c3:#888780;
  --ok:#3b6d11; --okb:#eaf3de; --okr:#c0dd97;
  --warn:#854f0b; --warnb:#faeeda; --warnr:#efac27;
  --err:#a32d2d; --errb:#fcebeb; --errr:#f09595;
  --info:#185fa5; --infob:#e6f1fb; --infor:#85b7eb;
  --br:rgba(0,0,0,.12); --br2:rgba(0,0,0,.22);
  --r:8px; --rl:12px
}
@media (prefers-color-scheme:dark){
  :root {
    --bg:#1c1c1a; --bg2:#252522; --bg3:#2e2e2b;
    --c:#f0efeb; --c2:#b4b2a9; --c3:#888780;
    --ok:#c0dd97; --okb:#173404; --okr:#3b6d11;
    --warn:#fac775; --warnb:#412402; --warnr:#854f0b;
    --err:#f09595; --errb:#501313; --errr:#a32d2d;
    --info:#b5d4f4; --infob:#042c53; --infor:#185fa5;
    --br:rgba(255,255,255,.12); --br2:rgba(255,255,255,.22)
  }
}
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
       background:var(--bg2); color:var(--c); font-size:14px; line-height:1.5 }
#app { max-width:720px; margin:0 auto; background:var(--bg); min-height:100vh;
       border-left:0.5px solid var(--br); border-right:0.5px solid var(--br) }
h1 { font-size:18px; font-weight:500 }
button { font-family:inherit; font-size:13px; cursor:pointer;
         border:0.5px solid var(--br2); background:transparent; color:var(--c);
         border-radius:var(--r); padding:5px 12px; transition:background .15s }
button:hover { background:var(--bg2) }
.btn-p { background:var(--c); color:var(--bg); border-color:var(--c); font-weight:500 }
.btn-p:hover { opacity:.85; background:var(--c) }
.btn-sm { padding:3px 8px; font-size:11px }
.btn-g { border:none; padding:3px 7px; color:var(--c3); border-radius:var(--r) }
.btn-g:hover { background:var(--bg3); color:var(--c) }
select, input[type=date], input[type=text] {
  font-family:inherit; font-size:13px; padding:7px 10px;
  border:0.5px solid var(--br2); border-radius:var(--r);
  background:var(--bg); color:var(--c); width:100%
}
select:focus, input:focus { outline:2px solid var(--infor); outline-offset:-1px }
.card { background:var(--bg); border:0.5px solid var(--br);
        border-radius:var(--rl); padding:1rem 1.25rem }
.chip { display:inline-block; font-size:11px; padding:2px 8px;
        border-radius:10px; border:0.5px solid }
.slabel { font-size:11px; font-weight:500; color:var(--c3);
          text-transform:uppercase; letter-spacing:.06em; margin:12px 0 6px }
"""

# ---------------------------------------------------------------------------
# JavaScript -- vanilla, no framework, no CDN
# ---------------------------------------------------------------------------
JS = r"""
// ── Date helpers ──────────────────────────────────────────────────────────
const MO=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function toDate(s){const[y,m,d]=s.split('-').map(Number);return new Date(y,m-1,d)}
function toStr(d){return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')}
function addDays(d,n){const r=new Date(d);r.setDate(r.getDate()+n);return r}
function diffDays(a,b){return Math.round((b-a)/86400000)}
function fmtDate(s){const d=toDate(s);return d.getDate()+' '+MO[d.getMonth()]+' '+d.getFullYear()}
function fmtDMY(s){const d=toDate(s);return String(d.getDate()).padStart(2,'0')+'/'+String(d.getMonth()+1).padStart(2,'0')+'/'+d.getFullYear()}
function today0(){const d=new Date();d.setHours(0,0,0,0);return d}

// ── Schengen 90/180 calculation ───────────────────────────────────────────
// Both entry and exit days count as full days (EU Reg 610/2013).
// For any date D, the rolling window covers [D-179, D] inclusive (180 days).
function daysInWindow(at,trips){
  // Merge overlapping/touching intervals so a transit day shared between
  // two trips (end of A == start of B) is counted only once.
  const ws=addDays(at,-179);
  const ivs=[];
  for(const t of trips){
    const s=toDate(t.s),e=toDate(t.e);
    if(e<ws||s>at)continue;
    ivs.push([s<ws?ws:s, e>at?at:e]);
  }
  if(!ivs.length)return 0;
  ivs.sort((a,b)=>a[0]-b[0]);
  let count=0,cs=ivs[0][0],ce=ivs[0][1];
  for(let i=1;i<ivs.length;i++){
    const[s,e]=ivs[i];
    if(s<=ce){if(e>ce)ce=e;}          // overlapping or touching: merge
    else{count+=diffDays(cs,ce)+1;cs=s;ce=e;}
  }
  count+=diffDays(cs,ce)+1;
  return count;
}

// How many consecutive days can be used starting from startDate, given
// existingTrips. Scans forward day-by-day so old trip days dropping off
// the rolling window are naturally accounted for.
function availableDaysFrom(startDate,existingTrips){
  const sStr=toStr(startDate);
  let count=0;
  const cur=new Date(startDate);
  for(let i=0;i<91;i++){
    const test={s:sStr,e:toStr(cur)};
    if(daysInWindow(cur,[...existingTrips,test])>90)break;
    count++;
    cur.setDate(cur.getDate()+1);
  }
  return count;
}

function personStatus(trips){
  const now=today0();
  const winStart=addDays(now,-179);

  // Confirmed days up to and including today (ongoing trips clipped to today)
  const confirmedNow=trips.filter(t=>toDate(t.s)<=now).map(t=>{
    const e=toDate(t.e);
    return e>now?Object.assign({},t,{e:toStr(now)}):t;
  });
  const usedToday=daysInWindow(now,confirmedNow);

  // Period anchor calculated FIRST so the projected scan is bounded by it.
  // Anchored to oldest confirmed in-window trip start, that date + 179.
  // Fallback (no trips in window): today to today+179.
  const inWin=confirmedNow.filter(t=>toDate(t.s)>=winStart);
  let periodStart=now,periodEnd=addDays(now,179);
  if(inWin.length){
    const oldest=inWin.reduce((a,b)=>toDate(a.s)<toDate(b.s)?a:b);
    periodStart=toDate(oldest.s);
    periodEnd=addDays(periodStart,179);
  }

  // Projected peak: scan tomorrow to periodEnd (bounded within the current
  // 180-day window) using all trips at full extent (ongoing + planned).
  let projectedPeak=usedToday;
  const futureTails=trips.filter(t=>toDate(t.e)>now);
  if(futureTails.length){
    const lastTrip=futureTails.reduce((m,t)=>{const e=toDate(t.e);return e>m?e:m;},now);
    const scanUntil=lastTrip<periodEnd?lastTrip:periodEnd;
    const cur=new Date(addDays(now,1));
    while(cur<=scanUntil){
      const d=daysInWindow(cur,trips);
      if(d>projectedPeak)projectedPeak=d;
      cur.setDate(cur.getDate()+1);
    }
  }

  const used=projectedPeak;
  const remaining=Math.max(0,90-used);
  const isProjected=projectedPeak>usedToday;

  // Next available: show when at or over limit (projected peak).
  // Scans all trips at full extent so ongoing/planned travel is reflected.
  let nextAvail=null,nextAvailDays=0;
  if(used>=90){
    let chk=addDays(now,1);
    for(let i=0;i<366;i++){
      // Skip days where the person is already inside Schengen
      const inSchengen=trips.some(t=>toDate(t.s)<=chk&&toDate(t.e)>=chk);
      if(!inSchengen&&daysInWindow(chk,trips)<90){
        nextAvail=chk;
        nextAvailDays=availableDaysFrom(chk,trips);
        break;
      }
      chk=addDays(chk,1);
    }
  }

  return{used,remaining,nextAvail,nextAvailDays,periodStart,periodEnd,isProjected};
}

// Analyse a planned trip against a baseline of confirmed past trips.
// For each day of the planned trip, simulate accumulating days and check
// the rolling 180-day window. Returns peak days and first breach date.
function analysePlan(trip,base){
  const s=toDate(trip.s),e=toDate(trip.e);
  let peak=0,exceedDate=null;
  const cur=new Date(s);
  while(cur<=e){
    const d=daysInWindow(cur,[...base,{s:trip.s,e:toStr(cur)}]);
    if(d>peak)peak=d;
    if(d>90&&!exceedDate)exceedDate=new Date(cur);
    cur.setDate(cur.getDate()+1);
  }
  return{peak,exceedDate,ok:!exceedDate};
}

// ── Constants ─────────────────────────────────────────────────────────────
const SWATCHES=['#3b82f6','#f97316','#22c55e','#a855f7','#ec4899','#14b8a6','#ef4444','#eab308'];
const CTRY=['Austria','Belgium','Croatia','Czech Republic','Denmark','Estonia',
  'Finland','France','Germany','Greece','Hungary','Iceland','Italy','Latvia',
  'Liechtenstein','Lithuania','Luxembourg','Malta','Netherlands','Norway',
  'Poland','Portugal','Slovakia','Slovenia','Spain','Sweden','Switzerland'];

// ── Application state ─────────────────────────────────────────────────────
let S={
  data:null,
  view:'both',       // 'both' | 'p1' | 'p2'
  editName:null,     // 'p1' | 'p2' | null
  nameInput:'',
  colorInput:'',
  showForm:false,    // showing the add-trip form
  editKey:null,      // {pid,tripId} when editing an existing trip
  form:{country:'',s:'',e:'',persons:['p1','p2']},
  formErr:'',
  showOld:{p1:false,p2:false}
};

// ── API calls ─────────────────────────────────────────────────────────────
async function apiLoad(){
  try{const r=await fetch('/api/data');S.data=await r.json();}
  catch(e){console.error('Load failed:',e);}
  render();
}
function apiSave(){
  fetch('/api/data',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(S.data)
  }).catch(e=>console.error('Save failed:',e));
}
function set(patch){Object.assign(S,patch);render();}

// ── Actions ───────────────────────────────────────────────────────────────
function setView(v){set({view:v,showForm:false,editKey:null,editName:null});}

function startEditName(pid){
  set({editName:pid,nameInput:S.data.people[pid].name,colorInput:S.data.people[pid].color,showForm:false,editKey:null});
}
function cancelEditName(){set({editName:null});}
function saveName(){
  if(!S.nameInput.trim())return;
  S.data.people[S.editName].name=S.nameInput.trim();
  if(S.colorInput)S.data.people[S.editName].color=S.colorInput;
  apiSave();
  set({editName:null});
}

function openAddForm(){
  const def=S.view==='p1'?['p1']:S.view==='p2'?['p2']:['p1','p2'];
  set({showForm:true,editKey:null,editName:null,formErr:'',
       form:{country:'',s:'',e:'',persons:def}});
}

// Returns conflicting trip if new dates truly overlap an existing trip.
// Same-day transitions (end of one == start of next) are permitted.
function tripOverlaps(ns,ne,trips,excludeId){
  for(const t of trips){
    if(t.id===excludeId)continue;
    const ts=toDate(t.s),te=toDate(t.e);
    if(ns<te&&ts<ne)return t; // strict < so touching boundary is allowed
  }
  return null;
}

function addTrip(){
  const f=S.form;
  if(!f.country)return set({formErr:'Please select a country.'});
  if(!f.s||!f.e)return set({formErr:'Please enter both dates.'});
  if(toDate(f.s)>toDate(f.e))return set({formErr:'Start date must be before end date.'});
  if(!f.persons.length)return set({formErr:'Select at least one person.'});
  const ns=toDate(f.s),ne=toDate(f.e);
  for(const pid of f.persons){
    const c=tripOverlaps(ns,ne,S.data.people[pid].trips,null);
    if(c)return set({formErr:S.data.people[pid].name+': overlaps with '
      +c.country+' ('+fmtDate(c.s)+' \u2014 '+fmtDate(c.e)+'). '
      +'Only same-day transitions between trips are permitted.'});
  }
  const trip={id:String(Date.now()),s:f.s,e:f.e,country:f.country};
  f.persons.forEach(pid=>S.data.people[pid].trips.push(trip));
  apiSave();
  const def=S.view==='p1'?['p1']:S.view==='p2'?['p2']:['p1','p2'];
  set({showForm:false,formErr:'',form:{country:'',s:'',e:'',persons:def}});
}

function startEditTrip(pid,tripId){
  const t=S.data.people[pid].trips.find(x=>x.id===tripId);
  if(!t)return;
  set({editKey:{pid,tripId},form:{country:t.country,s:t.s,e:t.e,persons:[pid]},
       showForm:false,editName:null,formErr:''});
}
function cancelEdit(){set({editKey:null,formErr:''});}
function saveEdit(){
  const f=S.form;
  if(!f.country)return set({formErr:'Please select a country.'});
  if(!f.s||!f.e)return set({formErr:'Please enter both dates.'});
  if(toDate(f.s)>toDate(f.e))return set({formErr:'Start date must be before end date.'});
  const{pid,tripId}=S.editKey;
  const ec=tripOverlaps(toDate(f.s),toDate(f.e),S.data.people[pid].trips,tripId);
  if(ec)return set({formErr:'Overlaps with '+ec.country
    +' ('+fmtDate(ec.s)+' \u2014 '+fmtDate(ec.e)+'). '
    +'Only same-day transitions between trips are permitted.'});
  const trips=S.data.people[pid].trips;
  const i=trips.findIndex(t=>t.id===tripId);
  if(i>=0)trips[i]=Object.assign({},trips[i],{s:f.s,e:f.e,country:f.country});
  apiSave();
  set({editKey:null,formErr:''});
}

function removeTrip(pid,id){
  if(!confirm('Remove this trip?'))return;
  S.data.people[pid].trips=S.data.people[pid].trips.filter(t=>t.id!==id);
  apiSave();
  render();
}
function togglePerson(pid){
  const p=S.form.persons;
  set({form:Object.assign({},S.form,{persons:p.includes(pid)?p.filter(x=>x!==pid):[...p,pid]})});
}

function toggleOldTrips(pid){set({showOld:Object.assign({},S.showOld,{[pid]:!S.showOld[pid]})});}
function togglePlannedSort(){
  S.data.settings.plannedSortAsc=!S.data.settings.plannedSortAsc;
  apiSave();
  render();
}

// ── DOM builder helpers ───────────────────────────────────────────────────
function el(tag,props,kids){
  const e=document.createElement(tag);
  for(const[k,v]of Object.entries(props||{})){
    if(k==='style'&&typeof v==='object')Object.assign(e.style,v);
    else if(k==='class')e.className=v;
    else if(k.startsWith('on'))e.addEventListener(k.slice(2).toLowerCase(),v);
    else e.setAttribute(k,v);
  }
  const arr=Array.isArray(kids)?kids:kids!=null?[kids]:[];
  for(const c of arr){
    if(c==null)continue;
    if(typeof c==='string')e.appendChild(document.createTextNode(c));
    else e.appendChild(c);
  }
  return e;
}
const div=(p,...k)=>el('div',p,k.filter(Boolean));
const span=(p,...k)=>el('span',p,k.filter(Boolean));

// ── Status card ───────────────────────────────────────────────────────────
function statusCard(pid){
  const p=S.data.people[pid];
  const st=personStatus(p.trips);
  const pct=Math.min(100,Math.round(st.used/90*100));
  const lvl=st.used>=90?'err':pct>=75?'warn':'ok';
  const lbl=st.used>90?'Over limit':st.used===90?'At limit':pct>=75?'Near limit':'OK';

  const badge=el('span',{class:'chip',style:{
    background:'var(--'+lvl+'b)',color:'var(--'+lvl+')',borderColor:'var(--'+lvl+'r)'}},lbl);

  const barFill=div({style:{height:'100%',width:pct+'%',
    background:'var(--'+lvl+')',borderRadius:'2px',transition:'width .4s'}});
  const bar=div({style:{height:'4px',background:'var(--br)',borderRadius:'2px',
    overflow:'hidden',marginBottom:'4px'}},barFill);

  const kids=[
    div({style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'12px'}},
      el('span',{style:{fontSize:'14px',fontWeight:'500'}},p.name), badge),
    div({style:{display:'flex',gap:'24px',marginBottom:'10px'}},
      div({},
        div({style:{fontSize:'30px',fontWeight:'500',lineHeight:'1',color:'var(--'+lvl+')'}},String(st.used)),
        div({style:{fontSize:'11px',color:'var(--c3)',marginTop:'2px'}},'days used')
      ),
      div({},
        div({style:{fontSize:'28px',fontWeight:'500',lineHeight:'1'}},String(st.remaining)),
        div({style:{fontSize:'11px',color:'var(--c3)',marginTop:'2px'}},'days remaining')
      )
    ),
    bar,
    div({style:{fontSize:'11px',color:'var(--c3)'}},
      st.used+' / 90 '+(st.isProjected?'incl. planned & ongoing trips':'in rolling 180-day window')),
    div({style:{fontSize:'11px',color:'var(--c3)',marginTop:'3px'}},
      'Period: '+fmtDate(toStr(st.periodStart))+' \u2014 '+fmtDate(toStr(st.periodEnd)))
  ];

  if(st.nextAvail){
    kids.push(div({style:{marginTop:'8px',fontSize:'11px',padding:'4px 8px',
      borderRadius:'var(--r)',background:'var(--errb)',color:'var(--err)'}},
      'Next available entry: '+fmtDate(toStr(st.nextAvail))
        +' for '+st.nextAvailDays+' day'+(st.nextAvailDays!==1?'s':'')));
  }
  return el('div',{class:'card'},kids);
}

// ── Trip form (shared for add and edit) ───────────────────────────────────
function tripForm(mode){
  const f=S.form;
  const hasDur=f.s&&f.e&&toDate(f.s)<=toDate(f.e);
  const dur=hasDur?diffDays(toDate(f.s),toDate(f.e))+1:0;

  const cSel=el('select',{onchange:e=>set({form:Object.assign({},S.form,{country:e.target.value})})},
    [el('option',{value:''},'Select country...')]);
  CTRY.forEach(c=>{
    const o=el('option',{value:c},c);
    if(c===f.country)o.selected=true;
    cSel.appendChild(o);
  });
  const mo=el('option',{value:'Multiple countries'},'Multiple / other Schengen');
  if(f.country==='Multiple countries')mo.selected=true;
  cSel.appendChild(mo);

  const sInp=el('input',{type:'date',value:f.s,
    onchange:e=>set({form:Object.assign({},S.form,{s:e.target.value})})});
  const eInp=el('input',{type:'date',value:f.e,
    onchange:e=>set({form:Object.assign({},S.form,{e:e.target.value})})});

  const formKids=[
    div({style:{fontSize:'15px',fontWeight:'500',marginBottom:'1rem'}},
      mode==='add'?'Add trip':'Edit trip'),
    div({style:{marginBottom:'10px'}},
      el('label',{style:{fontSize:'12px',color:'var(--c2)',display:'block',marginBottom:'4px'}},'Country'),
      cSel),
    div({style:{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'12px',margin:'10px 0'}},
      div({},
        el('label',{style:{fontSize:'12px',color:'var(--c2)',display:'block',marginBottom:'4px'}},'Start date'),
        sInp),
      div({},
        el('label',{style:{fontSize:'12px',color:'var(--c2)',display:'block',marginBottom:'4px'}},'End date'),
        eInp))
  ];

  if(hasDur){
    formKids.push(div({style:{fontSize:'12px',color:'var(--c2)',marginBottom:'10px'}},
      dur+' day'+(dur!==1?'s':'')));
  }

  // Available days hint: show per-person availability from the chosen start date
  if(mode==='add'&&f.s){
    const avails=(['p1','p2']).map(pid=>{
      const avail=availableDaysFrom(toDate(f.s),S.data.people[pid].trips);
      const endDate=avail>0?toStr(addDays(toDate(f.s),avail-1)):null;
      return{name:S.data.people[pid].name,avail,endDate};
    });
    const txt=avails.map(a=>{
      const dp=a.endDate?' ('+fmtDMY(a.endDate)+')':'';
      return a.name+': '+a.avail+' day'+(a.avail!==1?'s':'')+dp;
    }).join(' · ');
    formKids.push(div({style:{fontSize:'12px',color:'var(--c2)',marginBottom:'10px',
      padding:'5px 10px',background:'var(--bg3)',borderRadius:'var(--r)'}},
      'Available from '+fmtDate(f.s)+': '+txt));
  }

  // Travelling toggle -- only shown when adding (editing modifies one person at a time)
  if(mode==='add'){
    const pRow=div({style:{display:'flex',gap:'8px',marginBottom:'14px'}});
    Object.keys(S.data.people).forEach(pid=>{
      const p=S.data.people[pid];
      const sel=f.persons.includes(pid);
      const btn=div({style:{flex:'1',padding:'7px 10px',fontSize:'13px',
        cursor:'pointer',borderRadius:'var(--r)',border:'0.5px solid',
        display:'flex',alignItems:'center',justifyContent:'center',gap:'7px',
        fontWeight:sel?'500':'400',
        background:sel?p.color:'transparent',
        color:sel?'#fff':'var(--c3)',
        borderColor:sel?p.color:'var(--br2)'},
        onclick:()=>togglePerson(pid)});
      btn.appendChild(el('span',{style:{fontSize:'12px',fontWeight:'700'}},
        sel?'\u2713':'\u2717'));
      btn.appendChild(document.createTextNode(p.name));
      pRow.appendChild(btn);
    });
    formKids.push(
      el('label',{style:{fontSize:'12px',color:'var(--c2)',display:'block',marginBottom:'6px'}},'Travelling'),
      pRow);
  }

  if(S.formErr){
    formKids.push(div({style:{fontSize:'12px',color:'var(--err)',background:'var(--errb)',
      padding:'6px 10px',borderRadius:'var(--r)',marginBottom:'10px'}},S.formErr));
  }

  const btnRow=div({style:{display:'flex',gap:'8px'}});
  if(mode==='add'){
    btnRow.appendChild(el('button',{style:{flex:'1'},onclick:()=>set({showForm:false,formErr:''})},'Cancel'));
    btnRow.appendChild(el('button',{class:'btn-p',style:{flex:'2'},onclick:addTrip},'Add trip'));
  }else{
    btnRow.appendChild(el('button',{style:{flex:'1'},onclick:cancelEdit},'Cancel'));
    btnRow.appendChild(el('button',{class:'btn-p',style:{flex:'2'},onclick:saveEdit},'Save changes'));
  }
  formKids.push(btnRow);

  return div({style:{border:'0.5px solid var(--br2)',borderRadius:'var(--rl)',
    padding:'1.25rem',background:'var(--bg2)'}}, ...formKids);
}

// ── Trip rows for one person ───────────────────────────────────────────────
function tripSection(pid){
  const now=today0(), ws=addDays(now,-179);
  const trips=S.data.people[pid].trips;
  // Baseline for planned trip analysis: only confirmed past trips
  const ongoing=trips.filter(t=>toDate(t.s)<=now&&toDate(t.e)>=now);
  const planned=trips.filter(t=>toDate(t.s)>now).sort((a,b)=>b.s.localeCompare(a.s));
  const past=trips.filter(t=>toDate(t.e)<now).sort((a,b)=>b.s.localeCompare(a.s));
  const wrap=div({});

  function actionBtns(trip){
    return div({style:{display:'flex',gap:'3px',flexShrink:'0',marginLeft:'8px'}},
      el('button',{class:'btn-sm btn-g',onclick:()=>startEditTrip(pid,trip.id)},'Edit'),
      el('button',{class:'btn-sm btn-g',onclick:()=>removeTrip(pid,trip.id)},'\u00D7')
    );
  }

  function mkRow(trip,type){
    // If this trip is currently being edited, render the inline edit form instead
    if(S.editKey&&S.editKey.pid===pid&&S.editKey.tripId===trip.id)
      return tripForm('edit');

    const days=diffDays(toDate(trip.s),toDate(trip.e))+1;

    if(type==='ongoing'){
      const row=div({style:{background:'var(--okb)',border:'0.5px solid var(--okr)',
        borderRadius:'var(--r)',padding:'.65rem 1rem',marginBottom:'5px',
        display:'flex',alignItems:'flex-start',justifyContent:'space-between'}});
      const left=div({},
        div({style:{fontSize:'13px',fontWeight:'500',color:'var(--ok)'}},
          '\u25CF Currently in '+trip.country),
        div({style:{fontSize:'12px',color:'var(--ok)',marginTop:'2px'}},
          fmtDate(trip.s)+' \u2014 '+fmtDate(trip.e)+' \u00B7 '+days+'d')
      );
      if(toDate(trip.e)>now){
        const an=analysePlan(trip,trips.filter(t=>t.id!==trip.id));
        if(!an.ok){
          const isFuture=an.exceedDate>now;
          const noteText=isFuture
            ? '\u26A0 Will exceed limit on '+fmtDate(toStr(an.exceedDate))+' \u00B7 Peak: '+an.peak+'/90'
            : '\u26A0 Over limit since '+fmtDate(toStr(an.exceedDate))+' \u00B7 Peak: '+an.peak+'/90';
          left.appendChild(div({style:{fontSize:'11px',color:'var(--err)',
            marginTop:'5px',fontWeight:'500'}},noteText));
        }
      }
      row.appendChild(left);
      row.appendChild(actionBtns(trip));
      return row;
    }

    if(type==='planned'){
      const an=analysePlan(trip,trips.filter(t=>t.id!==trip.id));
      const lvl=!an.ok?'err':an.peak>=80?'warn':'info';
      const row=div({style:{background:'var(--bg)',border:'0.5px solid var(--br)',
        borderLeft:'3px solid var(--'+lvl+')',borderRadius:'0',padding:'.65rem 1rem',
        marginBottom:'5px',display:'flex',alignItems:'flex-start',justifyContent:'space-between'}});
      const noteColor=!an.ok?'var(--err)':an.peak>=80?'var(--warn)':'var(--c3)';
      const noteText=!an.ok
        ? '\u26A0 Exceeds limit from '+fmtDate(toStr(an.exceedDate))+' \u00B7 Peak: '+an.peak+'/90'
        : an.peak===90
        ? '\u26A0 At limit \u00B7 Peak: 90/90'
        : an.peak>=80
        ? '\u26A0 Peak window: '+an.peak+'/90 \u2014 approaching limit'
        : 'Peak window: '+an.peak+'/90';
      row.appendChild(div({style:{flex:'1'}},
        div({style:{fontSize:'13px',fontWeight:'500'}},trip.country),
        div({style:{fontSize:'12px',color:'var(--c2)',marginTop:'2px'}},
          fmtDate(trip.s)+' \u2014 '+fmtDate(trip.e)+' \u00B7 '+days+'d'),
        div({style:{fontSize:'11px',marginTop:'4px',color:noteColor,fontWeight:!an.ok?'500':'400'}},noteText)
      ));
      row.appendChild(actionBtns(trip));
      return row;
    }

    // Past trip
    const inWin=toDate(trip.e)>=ws;
    const row=div({style:{background:'var(--bg2)',border:'0.5px solid var(--br)',
      borderRadius:'var(--r)',padding:'.55rem 1rem',marginBottom:'4px',
      display:'flex',alignItems:'center',justifyContent:'space-between',
      opacity:inWin?'1':'.4'}});
    const left=div({style:{display:'flex',alignItems:'center',gap:'10px',flex:'1',flexWrap:'wrap'}},
      el('span',{style:{fontSize:'13px',fontWeight:'500'}},trip.country),
      el('span',{style:{fontSize:'12px',color:'var(--c2)'}},fmtDate(trip.s)+' \u2014 '+fmtDate(trip.e)),
      el('span',{style:{fontSize:'11px',color:'var(--c3)'}},days+'d'),
      inWin?null:el('span',{style:{fontSize:'11px',color:'var(--c3)',fontStyle:'italic'}},'\u2014 outside window')
    );
    row.appendChild(left);
    row.appendChild(actionBtns(trip));
    return row;
  }

  if(ongoing.length) ongoing.forEach(t=>wrap.appendChild(mkRow(t,'ongoing')));

  if(planned.length){
    const asc=S.data.settings.plannedSortAsc;
    planned.sort((a,b)=>asc?a.s.localeCompare(b.s):b.s.localeCompare(a.s));
    const sortHdr=div({style:{display:'flex',alignItems:'center',
      justifyContent:'space-between',marginBottom:'6px',marginTop:'12px'}});
    sortHdr.appendChild(div({class:'slabel',style:{margin:'0'}},'\u2192 Planned'));
    const sortBtn=el('button',{
      class:'btn-g btn-sm',
      title:asc?'Showing nearest first \u2014 click to show furthest first'
                :'Showing furthest first \u2014 click to show nearest first',
      onclick:togglePlannedSort},
      asc?'\u2191 Nearest first':'\u2193 Furthest first');
    sortHdr.appendChild(sortBtn);
    wrap.appendChild(sortHdr);
    planned.forEach(t=>wrap.appendChild(mkRow(t,'planned')));
  }
  const pastInWin=past.filter(t=>toDate(t.e)>=ws);
  const pastOld=past.filter(t=>toDate(t.e)<ws);
  if(pastInWin.length){
    wrap.appendChild(div({class:'slabel'},'Past'));
    pastInWin.forEach(t=>wrap.appendChild(mkRow(t,'past')));
  }
  if(pastOld.length){
    if(S.showOld[pid]){
      wrap.appendChild(div({class:'slabel'},'Older trips'));
      pastOld.forEach(t=>wrap.appendChild(mkRow(t,'past')));
    }
    wrap.appendChild(el('button',{class:'btn-g btn-sm',
      style:{marginTop:'6px',fontSize:'11px',display:'block'},
      onclick:()=>toggleOldTrips(pid)},
      S.showOld[pid]
        ?'\u25B2 Hide older trips'
        :'\u25BC Show '+pastOld.length+' older trip'+(pastOld.length!==1?'s':'')));
  }
  if(!trips.length){
    wrap.appendChild(div({style:{fontSize:'13px',color:'var(--c3)',padding:'1.5rem',
      textAlign:'center',border:'0.5px dashed var(--br2)',borderRadius:'var(--rl)'}},
      'No trips recorded yet'));
  }
  return wrap;
}

// ── Main render ───────────────────────────────────────────────────────────
function render(){
  const root=document.getElementById('root');
  root.innerHTML='';
  if(!S.data){
    root.appendChild(div({style:{padding:'2rem',color:'var(--c3)'}},'Loading...'));
    return;
  }

  const persons=S.view==='both'?['p1','p2']:[S.view];
  const app=div({id:'app'});

  // Header
  app.appendChild(div({style:{padding:'1.25rem 1.25rem .75rem',borderBottom:'0.5px solid var(--br)'}},
    el('h1',{},'\uD83C\uDDEA\uD83C\uDDFA Schengen Travel Tracker'),
    div({style:{fontSize:'12px',color:'var(--c2)',marginTop:'3px'}},
      '90 days in any rolling 180-day window \u00B7 Entry and exit days both count as full days')
  ));

  // Person tabs + rename buttons
  const tabBar=div({style:{display:'flex',alignItems:'center',gap:'6px',
    padding:'.75rem 1.25rem',borderBottom:'0.5px solid var(--br)'}});
  // Both button
  const bothActive=S.view==='both';
  tabBar.appendChild(el('button',{
    style:{padding:'4px 14px',borderRadius:'20px',fontSize:'13px',
           fontWeight:bothActive?'500':'400',border:'0.5px solid',
           background:bothActive?'var(--c)':'transparent',
           color:bothActive?'var(--bg)':'var(--c2)',
           borderColor:bothActive?'var(--c)':'var(--br2)'},
    onclick:()=>setView('both')},'Both'));
  // Per-person buttons: colour dot + name, simple pill style
  Object.keys(S.data.people).forEach(pid=>{
    const p=S.data.people[pid];
    const active=S.view===pid;
    const btn=div({style:{display:'flex',alignItems:'center',gap:'6px',
      padding:'4px 12px',borderRadius:'20px',fontSize:'13px',cursor:'pointer',
      border:'0.5px solid',
      background:active?'var(--c)':'transparent',
      color:active?'var(--bg)':'var(--c2)',
      borderColor:active?'var(--c)':'var(--br2)'},
      onclick:()=>setView(pid)});
    btn.appendChild(div({style:{width:'8px',height:'8px',borderRadius:'50%',
      flexShrink:'0',background:p.color}}));
    btn.appendChild(document.createTextNode(p.name));
    tabBar.appendChild(btn);
  });
  const nr=div({style:{marginLeft:'auto',display:'flex',gap:'4px'}});
  Object.keys(S.data.people).forEach(pid=>{
    const dot=div({style:{width:'8px',height:'8px',borderRadius:'50%',
      background:S.data.people[pid].color,flexShrink:'0',display:'inline-block'}});
    const btn=el('button',{class:'btn-g btn-sm',
      style:{display:'flex',alignItems:'center',gap:'5px'},
      onclick:()=>startEditName(pid)},'\u270E '+S.data.people[pid].name);
    btn.insertBefore(dot, btn.firstChild);
    nr.appendChild(btn);
  });
  tabBar.appendChild(nr);
  app.appendChild(tabBar);

  // Inline name editor
  if(S.editName){
    const bar=div({style:{display:'flex',alignItems:'center',gap:'10px',
      padding:'.75rem 1.25rem',background:'var(--bg2)',borderBottom:'0.5px solid var(--br)'}});
    bar.appendChild(el('span',{style:{fontSize:'13px',color:'var(--c2)'}},'Rename '+S.data.people[S.editName].name+':'));
    const inp=el('input',{type:'text',value:S.nameInput,style:{maxWidth:'180px'},
      oninput:e=>S.nameInput=e.target.value,
      onkeydown:e=>{if(e.key==='Enter')saveName();if(e.key==='Escape')cancelEditName();}});
    bar.appendChild(inp);
    // Colour swatches
    SWATCHES.forEach(c=>{
      const sel=c===S.colorInput;
      const sw=div({style:{width:'20px',height:'20px',borderRadius:'50%',
        background:c,cursor:'pointer',flexShrink:'0',
        boxSizing:'border-box',
        border:sel?'2px solid var(--c)':'2px solid transparent',
        outline:sel?'1.5px solid var(--br2)':'none'},
        onclick:()=>{S.colorInput=c;render();}});
      bar.appendChild(sw);
    });
    bar.appendChild(el('button',{onclick:saveName},'Save'));
    bar.appendChild(el('button',{onclick:cancelEditName},'Cancel'));
    app.appendChild(bar);
    setTimeout(()=>inp.focus(),30);
  }

  // Body
  const body=div({style:{padding:'1.25rem'}});

  // Status cards
  const grid=div({style:{display:'grid',
    gridTemplateColumns:'repeat('+persons.length+',minmax(0,1fr))',
    gap:'12px',marginBottom:'1.5rem'}});
  persons.forEach(pid=>grid.appendChild(statusCard(pid)));
  body.appendChild(grid);

  // Add trip button / form (above trips)
  if(!S.showForm){
    body.appendChild(el('button',{
      style:{width:'100%',marginBottom:'1rem',padding:'.75rem',
             border:'0.5px dashed var(--br2)',borderRadius:'var(--rl)',
             fontSize:'14px',color:'var(--c2)'},
      onclick:openAddForm},'+ Add trip'));
  }else{
    body.appendChild(div({style:{marginBottom:'1rem'}},tripForm('add')));
  }

  // Trip lists
  persons.forEach(pid=>{
    // Always show person name label, with colour dot
    const pLabel=div({style:{fontSize:'11px',fontWeight:'500',color:'var(--c3)',
      textTransform:'uppercase',letterSpacing:'.06em',marginBottom:'8px',
      display:'flex',alignItems:'center',gap:'6px'}});
    pLabel.appendChild(div({style:{width:'7px',height:'7px',borderRadius:'50%',
      background:S.data.people[pid].color,flexShrink:'0'}}));
    pLabel.appendChild(document.createTextNode(S.data.people[pid].name));
    body.appendChild(pLabel);
    body.appendChild(tripSection(pid));
  });

  app.appendChild(body);

  // Footer
  const footer=div({style:{padding:'.75rem 1.25rem',borderTop:'0.5px solid var(--br)',
    fontSize:'11px',color:'var(--c3)',display:'flex',justifyContent:'space-between',
    alignItems:'center',flexWrap:'wrap',gap:'6px'}});
  footer.appendChild(div({},'Data saved to: SchengenTravelTracker_data.json'));
  const fRight=div({style:{display:'flex',gap:'12px',alignItems:'center'}});
  fRight.appendChild(el('span',{},'© 2026 Kit Norriss · '+VERSION+' · GNU GPL v3.0'));
  const ghLink=el('a',{href:'https://github.com/CrestixUK/Schengen-Travel-Tracker',
    target:'_blank',rel:'noopener noreferrer',
    style:{color:'var(--info)',textDecoration:'none'}},
    'GitHub ↗');
  fRight.appendChild(ghLink);
  footer.appendChild(fRight);
  app.appendChild(footer);

  root.appendChild(app);
}

apiLoad();
"""

# ---------------------------------------------------------------------------
# Assemble HTML (concatenation avoids str.format() escaping curly braces in JS)
# ---------------------------------------------------------------------------
HTML = (
    "<!DOCTYPE html>\n<html lang='en'>\n"
    "<head>\n<meta charset='UTF-8'>\n"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>\n"
    "<title>Schengen Travel Tracker</title>\n"
    "<style>\n" + CSS + "\n</style>\n"
    "</head>\n<body>\n"
    "<div id='root'></div>\n"
    "<script>\n" + JS.replace("'+VERSION+'", VERSION) + "\n</script>\n"
    "</body>\n</html>"
)


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # suppress access log noise

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/data":
            self._json(200, load_data())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/data":
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n)
            try:
                data = json.loads(raw)
                save_data(data)
                self._json(200, {"ok": True})
            except Exception as exc:
                self._json(400, {"error": str(exc)})
        else:
            self.send_response(404)
            self.end_headers()


def _open_browser(url: str) -> None:
    import time
    time.sleep(0.9)
    webbrowser.open(url)


if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"\n  Schengen Tracker  \u2192  {url}")
    print(f"  Data file         \u2192  {DATA_FILE}")
    print("  Stop              \u2192  Ctrl+C\n")
    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
