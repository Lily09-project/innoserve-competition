// Deterministic method animation. Recorded aggregate data; topology illustrates the method.
import fs from 'node:fs';
import {metrics as m,percent,count} from './metrics.mjs';
const palette=JSON.parse(fs.readFileSync(new URL('../../design-system/palette.json',import.meta.url),'utf8'));
const typography=JSON.parse(fs.readFileSync(new URL('../../design-system/typography.json',import.meta.url),'utf8'));
const icons=JSON.parse(fs.readFileSync(new URL('../../design-system/icons.json',import.meta.url),'utf8'));
const cjkRuns=new RegExp('('+typography.cjk_pattern+'+)','u');
const isCjk=new RegExp('^'+typography.cjk_pattern+'+$','u');
export const duration=60;
export const playbackSpeed=2;
export const presentationDuration=duration/playbackSpeed;
export const maxDuration=40;
export const chapters=[{at:0,title:'作品名稱'},{at:5,title:'網路拓樸'},{at:12,title:'流量表徵'},{at:21,title:'17類判定'},{at:30,title:'證據檢索'},{at:38,title:'本機AI稽核'},{at:45,title:'受控處置'},{at:52,title:'實測成果'},{at:57,title:'展示結束'}];
export const controlTimeline={start:45,apply:46,readback:48,expiry:50};
export const chapterAt=t=>Math.max(0,chapters.findLastIndex(c=>t>=c.at));
// Night console: the film shares the deck's night cover so slide 1 -> 2 reads as one scene.
const B=palette.blue,G=palette.gold,T=palette.teal,N=palette.navy,FONT=typography.latin+', '+typography.cjk;
const PANEL=palette.night_panel,EDGE=palette.night_line,FG=palette.white,SUB=palette.on_dark_muted,FLOW=palette.cyan;
const ON_DARK={white:'navy',blue:'cyan',gray:'night_line',blue_tint:'night_panel',line:'night_line'};
const resolveColors=source=>source.replace(/#[0-9a-fA-F]{6}\b/g,hex=>palette[palette.legacy_roles[hex.slice(1).toUpperCase()]]||hex);
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const ease=v=>1-Math.pow(1-Math.max(0,Math.min(1,v)),3);
const tx=(x,y,s,z=24,c=FG,w=400,anchor='start')=>{
 const runs=String(s).split(cjkRuns).filter(Boolean).map(part=>`<tspan font-family="${isCjk.test(part)?typography.cjk:typography.latin}">${esc(part)}</tspan>`).join('');
 return `<text x="${x}" y="${y}" text-anchor="${anchor}" font-size="${z}" fill="${c}" font-weight="${w}">${runs}</text>`;
};
const box=(x,y,w,h,c,r=10)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${c}"/>`;
const frame=(x,y,w,h,c,r=10)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="none" stroke="${c}" stroke-width="1.5"/>`;
const line=(x,y,a,b,c=EDGE)=>`<path d="M${x} ${y}L${a} ${b}" fill="none" stroke="${c}" stroke-width="3" stroke-linecap="round"/>`;
const arrow=(x,y,a,b,c=FLOW)=>line(x,y,a,b,c)+`<path d="M${a-6} ${b-5}L${a} ${b}L${a-6} ${b+5}" fill="none" stroke="${c}" stroke-width="2"/>`;
const chip=(x,y,w,h,label,z=25,fill=N,color=FG)=>box(x,y,w,h,fill,10)+(fill===N?frame(x,y,w,h,EDGE):'')+tx(x+w/2,y+h*.66,label,z,color,700,'middle');
const flatIcon=(name,x,y,size,roles=ON_DARK)=>`<g transform="translate(${x} ${y}) scale(${size/64})">${icons[name].replace(/\{\{(\w+)\}\}/g,(_,key)=>palette[roles[key]||key])}</g>`;
function evidencePanel(index,local,t){
 let s='';
 if(index===1){
  s+=tx(859,271,'流量進入同一條事件鏈',26,FG,700);
  s+=chip(859,299,144,62,'正常流量',25)+chip(1048,299,144,62,'異常流量',25);
  s+=`<path d="M931 361V382H1120V361M1027 382V397" fill="none" stroke="${FLOW}" stroke-width="2"/>`;
  s+=chip(901,399,252,64,'同一事件識別碼',26,B);
  s+=tx(859,505,'判定與證據持續綁定',24,SUB);
 }else if(index===2){
  s+=tx(859,269,'三種線索，共同表徵',26,FG,700);
  ['內容','時間差','方向'].forEach((label,k)=>{
   const y=293+k*64;
   s+=chip(859,y,104,44,label,24);
   const amount=ease((local-k*.18)/.6);
   for(let j=0;j<5;j++)s+=box(984+j*39,y+9,27*amount,26,j===k?G:FLOW,4);
  });
  s+=tx(859,510,'欄位遮罩 → 流量切窗',24,SUB);
 }else if(index===4){
  s+=chip(859,254,158,49,'512 維表徵',23)+chip(1035,254,157,49,'17 維機率',23);
  s+=tx(1026,288,'＋',23,FLOW,700,'middle');
  s+=chip(901,325,252,53,'529 維任務向量',26,B);
  s+=`<path d="M1027 305V322M1027 378V402" stroke="${FLOW}" stroke-width="3"/>`;
  for(let k=0;k<5;k++){
   const u=ease((local-.4-k*.12)/.55),x=859+k*68;
   s+=`<g opacity="${u}" transform="translate(0 ${(1-u)*24})">${chip(x,410,60,63,String(k+1),28,k===0?G:N,k===0?N:FG)}</g>`;
  }
  s+=tx(859,509,'Top-5：只檢索訓練案例',24,SUB);
 }else if(index===5){
  s+=chip(859,254,158,49,'正式判定',24)+chip(1035,254,157,49,'案例證據',24);
  s+=chip(901,330,252,56,'本機 AI 稽核',27,B);
  s+=`<path d="M938 303V315H1114V303M1026 315V329M1026 386V403H912V417M1026 403V417M1026 403H1140V417" fill="none" stroke="${FLOW}" stroke-width="2"/>`;
  ['支持','複核','不確定'].forEach((label,k)=>s+=chip(859+k*114,417,106,49,label,24,k===0?T:N));
  s+=tx(859,510,'附加稽核，保留正式分類',24,SUB);
 }else if(index===6){
  s+=tx(859,269,'先檢查策略，再執行',26,FG,700);
  const labels=['套用','讀回','回復'];
  const active=t>=controlTimeline.expiry?2:t>=controlTimeline.readback?1:t>=controlTimeline.apply?0:-1;
  labels.forEach((label,k)=>{
   const x=859+k*114;
   s+=chip(x,310,106,64,label,27,k===active?G:k<active?T:N,k===active?N:FG);
   if(k<2)s+=arrow(x+106,342,x+112,342);
  });
  const u=Math.max(0,Math.min(1,(t-controlTimeline.apply)/(controlTimeline.expiry-controlTimeline.apply)));
  s+=`<circle cx="891" cy="430" r="23" fill="${N}" stroke="${FLOW}" stroke-width="3"/><path d="M891 430L${891+17*Math.sin(u*2*Math.PI)} ${430-17*Math.cos(u*2*Math.PI)}" stroke="${G}" stroke-width="3" stroke-linecap="round"/>`;
  s+=tx(929,440,t>=controlTimeline.expiry?'到期撤銷規則':'期限隨策略管理',25,FG,700);
  s+=tx(859,504,'同次回條，確認服務恢復',24,SUB);
 }
 return s;
}
function node(x,y,label,kind='pc'){
 return box(x-54,y-38,108,76,N,12)+frame(x-54,y-38,108,76,EDGE,12)+flatIcon(kind,x-36,y-36,72)+tx(x,y+72,label,24,FG,700,'middle');
}
function packet(x,y,c=G){return box(x-11,y-8,22,16,c,3)+`<path d="M${x-11} ${y-8}L${x} ${y+1}L${x+11} ${y-8}" fill="none" stroke="${N}" stroke-width="1.5"/>`;}
function topology(t){
 let s=box(60,175,718,410,PANEL,16);const nodes=[[110,245,'正常使用者','pc'],[110,455,'異常來源','pc'],[310,350,'核心交換器','switch'],[515,350,'策略閘道','fw'],[715,350,'應用服務','server']];
 [[110,245,310,350],[110,455,310,350],[310,350,515,350],[515,350,715,350]].forEach(v=>s+=line(...v));
 [[310,350,515,350],[515,350,715,350]].forEach((v,k)=>{
  const u=ease(((t*.32+k*.5)%1));
  s+=line(v[0],v[1],v[0]+(v[2]-v[0])*u,v[3],FLOW);
 });
 nodes.forEach(v=>s+=node(...v));
 // A separate branch makes the inference/evidence chain visible.
 s+=line(362,350,390,350)+line(390,350,390,530)+line(390,530,363,530)+line(310,530,715,530);
 [['IDS',310],['Top-5',515],['AI Judge',715]].forEach(([name,x],k)=>{
  const active=t>=[12,30,38][k];
  s+=box(x-73,505,146,64,active?T:N,12)+(active?'':frame(x-73,505,146,64,EDGE,12))+tx(x,547,name,29,active?FG:SUB,700,'middle');
 });
 if(t>=12&&t<30){const d=260*((t*.24)%1),x=390-(d-180);if(d<180)s+=packet(390,350+d);else if(x>377)s+=packet(x,530);}
 if(t>=30){const x=310+(t>=38?405:205)*((t*.24)%1);if((x>395&&x<430)||(x>600&&x<630))s+=packet(x,530);}
 if(t>=controlTimeline.start)s+=`<path d="M715 505V480H585V350H567" fill="none" stroke="${FLOW}" stroke-width="3" stroke-dasharray="7 5"/>`+tx(620,465,'策略檢查',24,SUB,700);
 const p=(t*.38)%1;
 s+=packet(110+200*p,245+105*p,FLOW)+packet(310+405*((t*.28)%1),350,FLOW);
 if(t<controlTimeline.apply||t>=controlTimeline.expiry)s+=packet(110+200*((t*.5)%1),455-105*((t*.5)%1),G);
 if(t>=controlTimeline.apply&&t<controlTimeline.expiry)s+=box(450,260,136,42,G,21)+tx(518,289,'規則生效',25,N,700,'middle');
 if(t>=controlTimeline.expiry)s+=box(450,260,136,42,T,21)+tx(518,289,'到期回復',25,FG,700,'middle');
 return s;
}
const messages=[
 [],['封包流動','正常／異常流量|進入同一事件鏈'],
 ['流量表徵','封包內容·時間差·方向','識別欄位先遮罩|再切分流量'],
 ['17 類判定','CTBM＋PBCNN|校準 → OOF Gate','正式類別＋校準信心|模型表徵'],
 ['任務導向檢索','512＋17 → 529 維','訓練案例庫|Top-5 相似案例'],
 ['本機 AI 稽核','支持／複核／不確定','依案例核對|保留正式分類'],
 ['受控處置與回復','策略檢查 → 套用 → 讀回','到期撤銷，保留事件回條']
];
const emblem=(x,y,size)=>flatIcon('framework',x,y,size,{white:'navy',blue_tint:'night_panel',line:'night_line',blue:'cyan',gray:'night_line'});
export function frameSvg(t){
 const i=chapterAt(t),local=t-chapters[i].at;
 let s=box(0,0,1280,720,N,0);
 if(i>0&&i<7){const labels=['流量','表徵','判定','檢索','稽核','回復'];labels.forEach((label,k)=>{const x=650+k*94,now=k===i-1,done=k<i-1;s+=box(x,39,84,40,now?G:done?T:PANEL,20)+tx(x+42,67,label,24,now?N:done?FG:SUB,700,'middle');});}
 if(i===0){
  s+=box(64,66,10,10,G,2)+tx(84,77,'AI SECURITY FRAMEWORK',18,FLOW,700);
  ['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架'].forEach((v,k)=>s+=`<g opacity="${ease((local-.25*k)/.9)}" transform="translate(0 ${(1-ease((local-.25*k)/.9))*30})">${tx(64,230+k*72,v,46,FG,700)}</g>`);
  s+=`<g opacity="${ease(local/.8)}" transform="translate(0 ${(1-ease(local/.8))*18})">${emblem(930,160,290)}</g>`;
  s+=box(64,436,56,4,G,2)+tx(64,500,'從流量判定，走到有證據的處置。',28,SUB);
 }else if(i===8){
  s+=box(64,78,10,10,G,2)+tx(84,89,'AI SECURITY FRAMEWORK',18,FLOW,700);
  s+=tx(64,232,'偵測有依據',50,FG,700)+tx(64,312,'稽核有證據',50,FG,700)+tx(64,392,'處置可回復',50,FLOW,700);
  s+=emblem(930,160,290);
  s+=box(64,467,1152,80,PANEL,16)+tx(96,518,'判定 → 證據 → 稽核 → 處置與回復回條',28,FG,700);
  s+=tx(64,625,'展示結束 · 接續架構與實測成果說明',24,SUB);
 }else if(i===7){
  s+=box(64,52,10,10,G,2)+tx(84,63,'MEASURED RESULTS',18,FLOW,700)+tx(64,124,'實測成果',44,FG,700);
  [[percent(m.accuracy),'17類偵測 Accuracy'],[percent(m.top5),'Top-5 命中率'],[`${m.rollback} / ${m.network_cases}`,'隔離情境完整回復']].forEach(([v,l],k)=>{const x=64+k*400,u=ease((local-k*.12)/.6);s+=`<g opacity="${u}" transform="translate(0 ${(1-u)*16})">${box(x-16,206,368,244,PANEL,18)}${flatIcon(['model','retrieval','shield'][k],x+274,229,48)}${tx(x,320,v,64,FLOW,700)}${box(x,344,56,4,G,2)}${tx(x,392,l,24,FG,700)}</g>`;});
  s+=tx(64,525,'偵測有依據，稽核有證據，處置可回復。',32,FG,700)+tx(64,606,`${count(m.detection_n)}筆偵測測試／${m.queries}筆檢索稽核／${m.network_cases}種隔離情境`,24,SUB);
 }else{
  s+=tx(64,66,`0${i} / 06`,24,FLOW,700)+tx(64,128,messages[i][0],44,FG,700);
  const scale=.96+.04*ease(local/.9);
  s+=`<g transform="translate(${(1-scale)*400} ${(1-scale)*350}) scale(${scale})">${topology(t)}</g>`;
  s+=box(835,225,381,300,PANEL,16)+frame(835,225,381,300,EDGE,16)+box(835,249,5,252,G,2);
  if(i===3){
   s+=tx(859,264,'同一流量輸入',26,FG,700);
   s+=`<path d="M1025 276V285H930V292 M1025 285H1120V292 M930 342V377H1025V410 M1120 342V377H1025" fill="none" stroke="${FLOW}" stroke-width="3"/>`;
   s+=`<path d="M925 286L930 292L935 286 M1115 286L1120 292L1125 286 M1020 404L1025 410L1030 404" fill="none" stroke="${FLOW}" stroke-width="2"/>`;
   s+=box(860,292,140,50,B,10)+tx(930,325,'CTBM',27,FG,700,'middle');
   s+=box(1050,292,140,50,B,10)+tx(1120,325,'PBCNN',27,FG,700,'middle');
   s+=box(899,410,252,58,T,10)+tx(1025,447,'校準＋OOF Gate',26,FG,700,'middle');
   s+=tx(859,505,'17類＋信心＋模型表徵',25,SUB);
  }else{
   const u=ease(local/.42);
   s+=`<g opacity="${u}" transform="translate(${(1-u)*24} 0)">${evidencePanel(i,local,t)}</g>`;
  }
  s+=box(64,593,1152,60,PANEL,14)+`<circle cx="94" cy="623" r="6" fill="${G}"/>`+tx(112,631,'同一事件 ID：判定 → 案例 → 稽核 → 處置回條',23,FG,700);
 }
 s+=tx(64,694,'方法流程示意 · 隔離TCP交易實測',20,SUB);
 s+=box(0,714,1280,6,PANEL,0)+box(0,714,1280*t/duration,6,G,0);
 return resolveColors(`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="${FONT}">${s}</svg>`);
}
