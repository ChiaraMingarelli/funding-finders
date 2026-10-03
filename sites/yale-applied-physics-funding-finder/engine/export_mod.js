/* ---------- tick-box export: calendar (.ics in a .zip) and CSV ---------- */
const EXP={key:"",picked:new Set(),all:()=>[],prefix:"funding"};
function expInit(key,all,prefix){EXP.key=key;EXP.all=all;EXP.prefix=prefix;try{EXP.picked=new Set(JSON.parse(localStorage.getItem(key)||"[]"));}catch(e){}}
const expSave=()=>{try{localStorage.setItem(EXP.key,JSON.stringify([...EXP.picked]));}catch(e){}};
const expYmd=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
const expShift=(iso,n)=>{const d=new Date(iso+"T00:00:00");d.setDate(d.getDate()+n);return expYmd(d);};
const expToday=expYmd(new Date());
const expIso=s=>typeof s==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(s);
function expDates(x){const o=[];if(expIso(x.d)&&x.d>=expToday)o.push([x.d,"Deadline"]);if(x.yale&&expIso(x.yale.d)&&x.yale.d>=expToday)o.push([x.yale.d,"Yale internal deadline"]);return o;}
const expPicked=()=>EXP.all().filter(x=>EXP.picked.has(x.id));
function expToggle(id,on){on?EXP.picked.add(id):EXP.picked.delete(id);expSave();}
const expUrl=u=>(typeof u==="string"&&/^https:\/\//i.test(u))?u:"";
/* ---------- one-click calendar links (work for every viewer; no download needed) ---------- */
function expCalLinks(x){
  const ds=expDates(x);if(!ds.length)return "";
  const e=encodeURIComponent,h=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  return ds.map(([d,lab])=>{
    const yale=lab!=="Deadline",t=(yale?"Yale internal deadline: ":"Deadline: ")+x.n,end=expShift(d,1);
    const note=String(yale&&x.yale?x.yale.t||"":x.dt||"").slice(0,300);
    const body=[x.f,note,expUrl(x.u),"Tip: set reminders 6 and 4 weeks before."].filter(Boolean).join("\n");
    const g=`https://calendar.google.com/calendar/render?action=TEMPLATE&text=${e(t)}&dates=${d.replace(/-/g,"")}/${end.replace(/-/g,"")}&details=${e(body)}`;
    const o=`https://outlook.office.com/calendar/0/deeplink/compose?path=%2Fcalendar%2Faction%2Fcompose&rru=addevent&allday=true&subject=${e(t)}&startdt=${d}&enddt=${end}&body=${e(body)}`;
    const lbl=ds.length>1?(yale?"Yale step to ":"Deadline to "):"Add to ";
    return `<span class="cal">${lbl}<a href="${h(g)}" target="_blank" rel="noopener">Google Calendar</a> · <a href="${h(o)}" target="_blank" rel="noopener">Outlook</a></span>`;
  }).join(" ")+` <span class="cal">· <a href="#" data-ics="${h(x.id)}" title="Downloads a calendar file with reminders 6 and 4 weeks before">Apple Calendar${ds.length>1?" (both dates)":""}</a></span>`;
}
/* Apple Calendar: a one-program .ics file (keeps the 6- and 4-week reminders) */
function expToast(msg){let t=document.getElementById("expToast");if(!t){t=document.createElement("div");t.id="expToast";t.setAttribute("role","status");t.style.cssText="position:fixed;left:50%;bottom:20px;transform:translateX(-50%);max-width:min(560px,calc(100vw - 32px));background:#222;color:#fff;font-size:14px;line-height:1.45;padding:12px 16px;z-index:1000;box-shadow:0 4px 16px rgba(0,0,0,.25)";document.body.appendChild(t);}t.textContent=msg;t.hidden=false;clearTimeout(t._h);t._h=setTimeout(()=>{t.hidden=true;},9000);}
async function expSaveOne(id){
  const x=EXP.all().find(r=>r.id===id);if(!x)return;
  const {text,n}=expIcs([x]);if(!n){expToast("This program has no upcoming date yet.");return;}
  const base=String(x.id||"deadline").replace(/[^a-z0-9-]+/gi,"-").slice(0,60),name=base+".ics";
  const ok="Open the .ics file to add it to Apple Calendar, with reminders 6 and 4 weeks before.";
  if(!window.claude){expDirect(name,text,"text/calendar;charset=utf-8");expToast("Downloaded. "+ok);return;}
  const dl=await EXP_DL;
  const blocked="Downloads from this page are only available to members of the page owner's Claude organization. Use the Google Calendar or Outlook link instead.";
  if(!dl){expToast(blocked);return;}
  try{await dl.save({filename:base+".zip",data:expZip(name,text)});expToast("Saved as a .zip. Unzip it, then "+ok.charAt(0).toLowerCase()+ok.slice(1));}
  catch(e){if(e&&e.code==="declined")return;expToast(e&&e.code==="rate_limited"?"A save prompt is already open.":blocked);}
}
document.addEventListener("click",e=>{const a=e.target.closest&&e.target.closest("[data-ics]");if(a){e.preventDefault();expSaveOne(a.dataset.ics);}});
function expIcs(rows){
  const e=s=>String(s??"").replace(/\\/g,"\\\\").replace(/;/g,"\\;").replace(/,/g,"\\,").replace(/\r?\n/g,"\\n");
  const fold=l=>{const o=[];while(l.length>60){o.push(l.slice(0,60));l=" "+l.slice(60);}o.push(l);return o.join("\r\n");};
  const stamp=new Date().toISOString().replace(/[-:]/g,"").replace(/\.\d+Z$/,"Z");
  const L=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Funding Finder//EN","CALSCALE:GREGORIAN","METHOD:PUBLISH"];let n=0;
  rows.forEach(x=>expDates(x).forEach(([d,label],k)=>{n++;
    L.push("BEGIN:VEVENT",`UID:${x.id}-${d}-${k}@funding-finder`,`DTSTAMP:${stamp}`,`DTSTART;VALUE=DATE:${d.replace(/-/g,"")}`,`DTEND;VALUE=DATE:${expShift(d,1).replace(/-/g,"")}`,
      `SUMMARY:${e(label+": "+x.n)}`,`DESCRIPTION:${e([x.f,x.dt,x.a,expUrl(x.u)].filter(Boolean).join("\n"))}`,"TRANSP:TRANSPARENT");
    if(expUrl(x.u))L.push(`URL:${expUrl(x.u)}`);
    [6,4].forEach(w=>L.push("BEGIN:VALARM","ACTION:DISPLAY",`DESCRIPTION:${e(w+" weeks until: "+x.n)}`,`TRIGGER:-P${w}W`,"END:VALARM"));
    L.push("END:VEVENT");}));
  L.push("END:VCALENDAR");return {text:L.map(fold).join("\r\n")+"\r\n",n};
}
function expCsv(rows){
  const c=v=>`"${String(v??"").replace(/"/g,'""')}"`;
  const L=[["Program","Funder","Deadline","Yale internal deadline","Reminder (6 weeks before)","Reminder (4 weeks before)","Status","Award","Deadline note","Link"].map(c).join(",")];
  rows.forEach(x=>{const f=expDates(x).map(d=>d[0]).sort()[0]||"";
    L.push([x.n,x.f,expIso(x.d)?x.d:"",x.yale&&expIso(x.yale.d)?x.yale.d:"",f?expShift(f,-42):"",f?expShift(f,-28):"",x.s,x.a,x.dt,expUrl(x.u)].map(c).join(","));});
  return L.join("\r\n")+"\r\n";
}
function expCrc(u){let crc=0xFFFFFFFF;for(let i=0;i<u.length;i++){let c=(crc^u[i])&0xFF;for(let k=0;k<8;k++)c=c&1?(c>>>1)^0xEDB88320:c>>>1;crc=(crc>>>8)^c;}return (crc^0xFFFFFFFF)>>>0;}
function expZip(name,text){
  const en=new TextEncoder(),data=en.encode(text),fn=en.encode(name),crc=expCrc(data);
  const lh=new Uint8Array(30+fn.length),a=new DataView(lh.buffer);
  [[0,0x04034b50,4],[4,20,2],[6,0x0800,2],[8,0,2],[10,0,2],[12,0x21,2],[14,crc,4],[18,data.length,4],[22,data.length,4],[26,fn.length,2],[28,0,2]].forEach(([o,v,s])=>s===4?a.setUint32(o,v,true):a.setUint16(o,v,true));lh.set(fn,30);
  const ch=new Uint8Array(46+fn.length),b=new DataView(ch.buffer);
  [[0,0x02014b50,4],[4,20,2],[6,20,2],[8,0x0800,2],[10,0,2],[12,0,2],[14,0x21,2],[16,crc,4],[20,data.length,4],[24,data.length,4],[28,fn.length,2],[30,0,2],[32,0,2],[34,0,2],[36,0,2],[38,0,4],[42,0,4]].forEach(([o,v,s])=>s===4?b.setUint32(o,v,true):b.setUint16(o,v,true));ch.set(fn,46);
  const end=new Uint8Array(22),z=new DataView(end.buffer);z.setUint32(0,0x06054b50,true);z.setUint16(8,1,true);z.setUint16(10,1,true);z.setUint32(12,ch.length,true);z.setUint32(16,lh.length+data.length,true);
  return new Blob([lh,data,ch,end],{type:"application/zip"});
}
const EXP_DL=(window.claude&&typeof window.claude.use==="function")?Promise.resolve(window.claude.use("downloads")).catch(()=>null):Promise.resolve(null);
function expDirect(name,data,type){const u=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement("a");a.href=u;a.download=name;a.rel="noopener";document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),10000);}
function expFallback(kind,rows,msg){
  if(!window.claude){ /* self-hosted copy (e.g. GitHub Pages): ordinary browser download */
    if(kind==="csv"){expDirect(`${EXP.prefix}-ticked.csv`,"\ufeff"+expCsv(rows),"text/csv;charset=utf-8");msg.textContent=`Downloaded ${rows.length} program${rows.length===1?"":"s"} as a CSV.`;return;}
    const {text,n}=expIcs(rows);if(!n){msg.textContent="None of the ticked programs has an upcoming date yet.";return;}
    expDirect(`${EXP.prefix}-deadlines.ics`,text,"text/calendar;charset=utf-8");msg.textContent=`Downloaded ${n} deadline${n===1?"":"s"} with reminders 6 and 4 weeks before. Open the .ics file to add them to your calendar.`;return;}
  msg.textContent="Downloads from this page are only available to members of the page owner's Claude organization. Use the Google Calendar or Outlook link on each program instead; those work for everyone.";}
async function expSaveFile(kind,msg){
  const rows=expPicked();if(!rows.length){msg.textContent="Tick at least one program first.";return;}
  const dl=await EXP_DL;if(!dl){expFallback(kind,rows,msg);return;}
  try{
    if(kind==="csv"){await dl.save({filename:`${EXP.prefix}-ticked.csv`,data:expCsv(rows)});msg.textContent=`Saved ${rows.length} program${rows.length===1?"":"s"} as a CSV, with the 6- and 4-week reminder dates in their own columns.`;return;}
    const {text,n}=expIcs(rows);
    if(!n){msg.textContent="None of the ticked programs has an upcoming date yet, so there's nothing to put on a calendar. The CSV still lists them.";return;}
    await dl.save({filename:`${EXP.prefix}-deadlines.zip`,data:expZip(`${EXP.prefix}-deadlines.ics`,text)});
    const skip=rows.filter(x=>!expDates(x).length).length;
    msg.textContent=`Saved ${n} deadline${n===1?"":"s"} with reminders 6 and 4 weeks before. Unzip it and open the .ics file to add them to your calendar. Apple Calendar and Outlook keep both reminders; Google Calendar uses your default reminders instead.${skip?` ${skip} ticked program${skip===1?" has":"s have"} no date yet and ${skip===1?"was":"were"} left out.`:""}`;
  }catch(e){const c=e&&e.code;if(c==="declined"){msg.textContent="";return;}if(c==="rate_limited"){msg.textContent="A save prompt is already open. Finish it, then try again.";return;}expFallback(kind,rows,msg);}
}
