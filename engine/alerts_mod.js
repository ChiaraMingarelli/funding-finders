/* ---------- email alerts for watch-list programs ---------- */
const ALERT={on:false,db:null,uid:null,email:"",items:{}};
async function alertsBoot(onChange){
  try{
    const db=await claude.use("db"), user=await claude.use("user");
    if(!db||!user) return;
    const uid=await user.id(); if(!uid) return;
    ALERT.db=db; ALERT.uid=uid;
    db.doc(`alerts/${uid}`).onSnapshot(s=>{const d=s.exists?s.data():{};ALERT.email=d.email||"";ALERT.items={...(d.items||{})};ALERT.on=true;onChange();},()=>{ALERT.on=false;onChange();});
  }catch(e){}
}
function askEmail(){
  return new Promise(res=>{
    const d=document.getElementById("alertDlg"), i=document.getElementById("alertEmail");
    i.value=ALERT.email||""; d.returnValue="";
    const onc=()=>{d.removeEventListener("close",onc);res(d.returnValue==="ok"&&i.value.trim()?i.value.trim():null);};
    d.addEventListener("close",onc); d.showModal();
  });
}
async function alertToggle(x,onChange){
  if(!x||!ALERT.on) return;
  if(ALERT.items[x.id]) delete ALERT.items[x.id];
  else{ if(!ALERT.email){const e=await askEmail(); if(!e) return; ALERT.email=e;}
        ALERT.items[x.id]={n:String(x.n||"").slice(0,300),at:new Date().toISOString().slice(0,10)}; }
  onChange();
  try{ await ALERT.db.doc(`alerts/${ALERT.uid}`).set({email:ALERT.email,items:ALERT.items,updatedAt:new Date().toISOString()}); }
  catch(e){ ALERT.on=false; onChange(); }
}
const alertLabel=x=>ALERT.items[x.id]?"✓ Email alert on":"✉ Email me when it opens";
const alertTitle=()=>ALERT.email?`Alerts go to ${ALERT.email}. Sending starts once the department sets up a sender.`:"Saves a request to be emailed when this program posts its next call.";
