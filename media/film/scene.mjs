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
// Packet Tracer simulation mode: devices on a logical workspace, envelope PDUs hop link by link.
const inout=v=>{v=Math.max(0,Math.min(1,v));return v<.5?4*v*v*v:1-Math.pow(2-2*v,3)/2;};
const DEVICES={user:[110,245],attack:[110,455],core:[310,350],gate:[515,350],app:[715,350],ids:[310,519],top5:[515,519],judge:[715,519]};
const NORMAL=['user','core','gate','app'].map(k=>DEVICES[k]),ATTACK=['attack','core','gate','app'].map(k=>DEVICES[k]);
const MIRROR=[DEVICES.core,[390,350],[390,519],DEVICES.ids];
// Chapter focus device, the inspector heading and the event-list row it adds.
const focus=[null,['core','核心交換器'],['ids','IDS'],['ids','IDS'],['top5','Top-5'],['judge','AI Judge'],['gate','策略閘道']];
const events=[null,['異常來源','核心交換器','TCP',G],['核心交換器','IDS','鏡像副本',G],['IDS','IDS','17 類判定',B],['IDS','Top-5','證據查詢',B],['Top-5','AI Judge','稽核請求',T],['AI Judge','策略閘道','策略套用',G]];
function hop(points,u){
 const n=points.length-1,k=Math.min(n-1,Math.floor(u*n)),f=inout((u*n-k)/.72),a=points[k],b=points[k+1];
 return [a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f];
}
function envelope(x,y,c,open=0){
 const flap=open?`<path d="M${x-15} ${y-11}L${x} ${y-11-13*open}L${x+15} ${y-11}" fill="${c}" stroke="${N}" stroke-width="1.8" stroke-linejoin="round"/>`:'';
 return flap+box(x-15,y-11,30,22,c,3)+`<path d="M${x-15} ${y-11}L${x} ${y+1}L${x+15} ${y-11}" fill="none" stroke="${N}" stroke-width="1.8" stroke-linejoin="round"/>`;
}
const dropped=(x,y)=>`<path d="M${x-13} ${y-13}L${x+13} ${y+13}M${x+13} ${y-13}L${x-13} ${y+13}" stroke="${N}" stroke-width="8" stroke-linecap="round"/><path d="M${x-13} ${y-13}L${x+13} ${y+13}M${x+13} ${y-13}L${x-13} ${y+13}" stroke="${G}" stroke-width="4.5" stroke-linecap="round"/>`;
const rule=(x,y,a,b)=>`<path d="M${x} ${y}L${a} ${b}" stroke="${EDGE}" stroke-width="1.5"/>`;
function node(x,y,label,kind='pc'){
 return box(x-54,y-38,108,76,PANEL,12)+frame(x-54,y-38,108,76,EDGE,12)+flatIcon(kind,x-36,y-36,72)+tx(x,y+72,label,24,FG,700,'middle');
}
function linkLights(a,b,c1=FLOW,c2=FLOW){
 const d=Math.hypot(b[0]-a[0],b[1]-a[1]),ux=(b[0]-a[0])/d,uy=(b[1]-a[1])/d,o=Math.abs(ux)>Math.abs(uy)?66:58;
 return `<circle cx="${a[0]+ux*o}" cy="${a[1]+uy*o}" r="5" fill="${c1}"/><circle cx="${b[0]-ux*o}" cy="${b[1]-uy*o}" r="5" fill="${c2}"/>`;
}
function topology(t,i,local){
 const ruled=t>=controlTimeline.apply&&t<controlTimeline.expiry;
 let s=`<rect x="64" y="190" width="736" height="412" fill="url(#grid)"/>`;
 [[DEVICES.user,DEVICES.core],[DEVICES.attack,DEVICES.core],[DEVICES.core,DEVICES.gate],[DEVICES.gate,DEVICES.app]].forEach(([a,b])=>s+=line(a[0],a[1],b[0],b[1]));
 s+=line(362,350,390,350)+line(390,350,390,519)+line(390,519,383,519)+line(310,519,715,519)+tx(402,446,'鏡像',18,SUB);
 s+=linkLights(DEVICES.user,DEVICES.core)+linkLights(DEVICES.attack,DEVICES.core)+linkLights(DEVICES.core,DEVICES.gate)+linkLights(DEVICES.gate,DEVICES.app,ruled?G:FLOW);
 if(t>=controlTimeline.start)s+=`<path d="M715 483V462H585V350H569" fill="none" stroke="${FLOW}" stroke-width="3" stroke-dasharray="7 5"/>`+tx(620,449,'策略檢查',22,SUB,700);
 [[110,245,'正常使用者','pc'],[110,455,'異常來源','pc'],[310,350,'核心交換器','switch'],[515,350,'策略閘道','fw'],[715,350,'應用服務','server']].forEach(v=>s+=node(...v));
 [['IDS',310,12],['Top-5',515,30],['AI Judge',715,38]].forEach(([name,x,at])=>{
  const active=t>=at;
  s+=box(x-73,483,146,72,active?T:PANEL,12)+(active?'':frame(x-73,483,146,72,EDGE,12))+`<circle cx="${x+58}" cy="496" r="5" fill="${active?FLOW:SUB}"/>`+tx(x,541,name,28,active?FG:SUB,700,'middle');
 });
 // Selection ring on the device being inspected, as when a PDU is clicked in simulation mode.
 const [fx,fy]=DEVICES[focus[i][0]],wide=fy>400,w=wide?166:128,h=wide?92:96;
 s+=`<rect x="${fx-w/2}" y="${fy-h/2}" width="${w}" height="${h}" rx="16" fill="none" stroke="${G}" stroke-width="2.5" stroke-dasharray="8 6" stroke-dashoffset="${(-t*24).toFixed(2)}" opacity="${ease(local/.5)}"/>`;
 // Traffic: normal PDUs always reach the service; the anomalous PDU is dropped while the rule is live.
 s+=envelope(...hop(NORMAL,((t-5)*.3)%1),FLOW);
 const u=((t-5)*.27+.45)%1;
 if(ruled){const p=hop(ATTACK.slice(0,3),Math.min(u*1.5,1));s+=envelope(...p,G);if(u*1.5>=.86)s+=dropped(p[0],p[1]);}
 else s+=envelope(...hop(ATTACK,u),G);
 if(i===2)s+=envelope(...hop(MIRROR,(local*.32)%1),G);
 if(i===3)s+=envelope(310,505,G,ease((local%2.4)/.8));
 if(i===4)s+=envelope(...hop([DEVICES.ids,DEVICES.top5],(local*.36)%1),B);
 if(i===5)s+=envelope(...hop([DEVICES.top5,DEVICES.judge],(local*.4)%1),T);
 if(i===6&&t<controlTimeline.apply+.4)s+=envelope(...hop([[715,483],[715,462],[585,462],[585,350],[569,350]],Math.min(1,local/1.3)),G);
 if(ruled)s+=box(450,248,136,42,G,21)+tx(518,277,'規則生效',25,N,700,'middle');
 if(t>=controlTimeline.expiry)s+=box(450,248,136,42,T,21)+tx(518,277,'到期回復',25,FG,700,'middle');
 // Gentle push toward the inspected device; the workspace stays clipped to its window.
 const z=1+.03*ease(local/1.6);
 return `<g clip-path="url(#ws)"><g transform="translate(432 396) scale(.86) translate(-432 -396)"><g transform="translate(${fx} ${fy}) scale(${z.toFixed(4)}) translate(${-fx} ${-fy})">${s}</g></g></g>`;
}
function simulationWindow(t,i,local){
 let s=box(64,150,1152,452,PANEL,16)+box(64,150,1152,40,EDGE,16)+box(64,170,1152,20,EDGE,0);
 [[88,G],[106,FLOW],[124,SUB]].forEach(([x,c])=>s+=`<circle cx="${x}" cy="170" r="5" fill="${c}"/>`);
 s+=tx(144,177,'Packet Tracer 式模擬 · 事件鏈',18,FG,700)+tx(1066,177,'Realtime',17,SUB,400,'end');
 s+=box(1080,158,124,24,FLOW,12)+tx(1142,176,'Simulation',17,N,700,'middle');
 s+=`<rect x="64" y="190" width="736" height="412" fill="${N}"/>`+topology(t,i,local)+rule(800,190,800,602);
 s+=tx(824,226,'PDU 資訊',22,FG,700)+tx(1192,226,'在 '+focus[i][1],20,FLOW,700,'end')+rule(824,244,1192,244);
 const e=events[i];
 s+=rule(824,548,1192,548)+envelope(840,575,e[3])+tx(866,582,'類型：'+eventType(t,i),20,FG,700);
 return s+frame(64,150,1152,452,EDGE,16);
}
const eventType=(t,i)=>i===6&&t>=controlTimeline.expiry?'規則到期撤銷':events[i][2];
function eventList(t,i){
 const row=k=>{const e=events[k];return e[0]===e[1]?`在 ${e[1]}`:`${e[0]}→${e[1]}`;};
 let s=box(64,612,1152,64,PANEL,14);
 s+=`<circle cx="100" cy="644" r="19" fill="none" stroke="${FLOW}" stroke-width="2.5"/>`+box(92,634,5,20,FLOW,1)+box(103,634,5,20,FLOW,1);
 s+=`<path d="M136 634V654M154 634L140 644L154 654Z M176 634L190 644L176 654Z M194 634V654" fill="${SUB}" stroke="${SUB}" stroke-width="2.5" stroke-linejoin="round"/>`;
 s+=tx(214,651,'事件清單',19,FLOW,700)+rule(320,624,320,664);
 if(i>1)s+=envelope(352,634,events[i-1][3])+tx(380,641,row(i-1),18,SUB)+tx(760,641,events[i-1][2],18,SUB);
 const e=events[i];
 s+=`<circle cx="334" cy="661" r="4" fill="${G}"/>`+envelope(358,661,e[3])+tx(386,668,row(i),20,FG,700)+tx(760,668,eventType(t,i),20,FG,700);
 return s+tx(1192,651,'同一事件 ID 貫穿全程',19,SUB,400,'end');
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
  s+=simulationWindow(t,i,local);
  const u=ease(local/.42);
  s+=`<g opacity="${u}" transform="translate(${-18+(1-u)*24} 14)">`;
  if(i===3){
   s+=tx(859,264,'同一流量輸入',26,FG,700);
   s+=`<path d="M1025 276V285H930V292 M1025 285H1120V292 M930 342V377H1025V410 M1120 342V377H1025" fill="none" stroke="${FLOW}" stroke-width="3"/>`;
   s+=`<path d="M925 286L930 292L935 286 M1115 286L1120 292L1125 286 M1020 404L1025 410L1030 404" fill="none" stroke="${FLOW}" stroke-width="2"/>`;
   s+=box(860,292,140,50,B,10)+tx(930,325,'CTBM',27,FG,700,'middle');
   s+=box(1050,292,140,50,B,10)+tx(1120,325,'PBCNN',27,FG,700,'middle');
   s+=box(899,410,252,58,T,10)+tx(1025,447,'校準＋OOF Gate',26,FG,700,'middle');
   s+=tx(859,505,'17類＋信心＋模型表徵',25,SUB);
  }else s+=evidencePanel(i,local,t);
  s+='</g>'+eventList(t,i);
 }
 s+=tx(64,700,'方法流程示意 · 隔離TCP交易實測',18,SUB);
 s+=box(0,714,1280,6,PANEL,0)+box(0,714,1280*t/duration,6,G,0);
 const defs=`<defs><pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="14" cy="14" r="1.3" fill="${EDGE}"/></pattern><clipPath id="ws"><rect x="64" y="190" width="736" height="412"/></clipPath></defs>`;
 return resolveColors(`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="${FONT}">${defs}${s}</svg>`);
}
