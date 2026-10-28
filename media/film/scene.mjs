// Deterministic method animation. Recorded aggregate data; topology illustrates the method.
export const duration=60;
export const playbackSpeed=2;
export const presentationDuration=duration/playbackSpeed;
export const maxDuration=40;
export const chapters=[{at:0,title:'作品名稱'},{at:5,title:'網路拓樸'},{at:13,title:'流量表徵'},{at:22,title:'17類判定'},{at:31,title:'證據檢索'},{at:40,title:'本機AI稽核'},{at:48,title:'受控處置'},{at:55,title:'實測成果'}];
export const chapterAt=t=>Math.max(0,chapters.findLastIndex(c=>t>=c.at));
const B='#0070D1',FONT='Microsoft JhengHei, Arial';
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const ease=v=>1-Math.pow(1-Math.max(0,Math.min(1,v)),3);
const tx=(x,y,s,z=24,c='#000000',w=400)=>`<text x="${x}" y="${y}" font-size="${z}" font-family="${/^[\x00-\x7F]+$/.test(String(s))?'Arial':'Microsoft JhengHei'}" fill="${c}" font-weight="${w}">${esc(s)}</text>`;
const box=(x,y,w,h,c,r=8)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${c}"/>`;
const line=(x,y,a,b,c='#CCCCCC')=>`<path d="M${x} ${y}L${a} ${b}" fill="none" stroke="${c}" stroke-width="3"/>`;
function node(x,y,label,kind='pc',dark=false){
 const ink=dark?'#FFFFFF':'#000000',fill=dark?'#181818':'#F5F7FA';
 let s=box(x-52,y-34,104,68,fill)+`<rect x="${x-35}" y="${y-22}" width="70" height="43" rx="4" fill="none" stroke="${B}" stroke-width="3"/>`;
 if(kind==='pc')s+=line(x,y+22,x,y+38,B)+line(x-22,y+38,x+22,y+38,B);
 else for(let k=0;k<3;k++)s+=line(x-23,y-12+k*12,x+23,y-12+k*12,B);
 return s+tx(x-55,y+72,label,22,ink);
}
function packet(x,y,c=B){return box(x-11,y-8,22,16,c,2)+`<path d="M${x-11} ${y-8}L${x} ${y+1}L${x+11} ${y-8}" fill="none" stroke="#FFFFFF" stroke-width="1.5"/>`;}
function topology(t,dark){
 let s='';const nodes=[[110,245,'正常使用者','pc'],[110,455,'異常來源','pc'],[310,350,'核心交換器','switch'],[515,350,'策略閘道','fw'],[715,350,'應用服務','server']];
 [[110,245,310,350],[110,455,310,350],[310,350,515,350],[515,350,715,350]].forEach(v=>s+=line(...v));
 nodes.forEach(v=>s+=node(...v,dark));
 // A separate branch makes the inference/evidence chain visible.
 s+=line(362,350,390,350)+line(390,350,390,530)+line(390,530,363,530)+line(310,530,715,530);
 [['IDS',310],['Top-5',515],['AI Judge',715]].forEach(([name,x],k)=>{
  const active=t>=[13,31,40][k];
  s+=box(x-53,505,106,54,active?B:(dark?'#181818':'#F5F7FA'))+tx(x-40,539,name,22,active?'#FFFFFF':(dark?'#CCCCCC':'#6B6B6B'));
 });
 if(t>=13&&t<31){const d=260*((t*.24)%1),x=390-(d-180);if(d<180)s+=packet(390,350+d);else if(x>377)s+=packet(x,530);}
 if(t>=31){const x=310+(t>=40?405:205)*((t*.24)%1);if((x>376&&x<447)||(x>581&&x<649))s+=packet(x,530);}
 if(t>=48)s+=`<path d="M715 505V480H585V350H567" fill="none" stroke="${B}" stroke-width="3" stroke-dasharray="7 5"/>`+tx(620,465,'策略檢查',22,dark?'#CCCCCC':'#6B6B6B');
 const p=(t*.38)%1;
 s+=packet(110+200*p,245+105*p)+packet(310+405*((t*.28)%1),350);
 if(t<49||t>53)s+=packet(110+200*((t*.5)%1),455-105*((t*.5)%1),dark?'#CCCCCC':'#6B6B6B');
 if(t>=49&&t<=53)s+=box(460,260,116,38,B,19)+tx(478,286,'規則生效',22,'#FFFFFF');
 if(t>53)s+=box(460,260,116,38,B,19)+tx(478,286,'到期回復',22,'#FFFFFF');
 return s;
}
const messages=[
 [],['封包流動','正常／異常流量|進入同一事件鏈'],
 ['流量表徵','封包內容・時間差・方向','遮罩識別欄位，再切分流量'],
 ['17 類判定','CTBM＋PBCNN|校準 → OOF Gate','正式類別＋校準信心|模型表徵'],
 ['任務導向檢索','512＋17 → 529 維','訓練案例庫|Top-5 相似案例'],
 ['本機 AI 稽核','支持／複核／不確定','依案例核對，保留正式分類'],
 ['受控處置與回復','策略檢查 → 套用 → 讀回','到期撤銷，保留事件回條']
];
export function frameSvg(t){
 const i=chapterAt(t),local=t-chapters[i].at,dark=false,bg=i===7?'#F2F7FC':'#FFFFFF',ink=dark?'#FFFFFF':'#000000',muted=dark?'#CCCCCC':'#6B6B6B';
 let s=box(0,0,1280,720,bg,0);
 if(i===0){
  s+=tx(64,78,'AI SECURITY FRAMEWORK',18,B,600);
  ['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架'].forEach((v,k)=>s+=`<g opacity="${ease((local-.25*k)/.9)}" transform="translate(0 ${(1-ease((local-.25*k)/.9))*30})">${tx(64,230+k*76,v,45,'#121314',300)}</g>`);
  s+=tx(64,556,'從流量判定，走到有證據的處置。',30,'#6B6B6B');
 }else if(i===7){
  s+=tx(64,94,'實測成果',44,'#121314',300);
  [['98.08%','17類偵測 Accuracy'],['97.62%','Top-5 命中率'],['6 / 6','隔離情境完整回復']].forEach(([v,l],k)=>{const x=64+k*400;s+=tx(x,310,v,56,B,300)+tx(x,375,l,24,'#121314');});
  s+=tx(64,525,'偵測有依據，稽核有證據，處置可回復。',34,'#121314',300)+tx(64,610,'18,998筆偵測測試／463筆檢索稽核／6種隔離情境',23,'#6B6B6B');
 }else{
  s+=tx(64,65,`0${i} / 06`,18,dark?'#53B1FF':B,600)+tx(64,128,messages[i][0],44,ink,300);
  const scale=.96+.04*ease(local/.9);
  s+=`<g transform="translate(${(1-scale)*400} ${(1-scale)*350}) scale(${scale})">${topology(t,dark)}</g>`;
  s+=box(835,225,381,300,dark?'#181818':'#F5F7FA');
  if(i===3){
   s+=tx(859,264,'同一流量輸入',22,ink);
   s+=`<path d="M1025 276V285H930V292 M1025 285H1120V292 M930 342V377H1025V410 M1120 342V377H1025" fill="none" stroke="${B}" stroke-width="3"/>`;
   s+=`<path d="M925 286L930 292L935 286 M1115 286L1120 292L1125 286 M1020 404L1025 410L1030 404" fill="none" stroke="${B}" stroke-width="2"/>`;
   s+=box(860,292,140,50,B)+tx(886,325,'CTBM',24,'#FFFFFF',600);
   s+=box(1050,292,140,50,B)+tx(1064,325,'PBCNN',24,'#FFFFFF',600);
   s+=box(902,410,252,58,B)+tx(922,447,'校準＋OOF Gate',24,'#FFFFFF');
   s+=tx(859,505,'17類＋信心＋模型表徵',22,ink);
  }else messages[i].slice(1).forEach((v,k)=>{
   // Keep Chinese strings readable by explicit semantic line breaks.
   const split=v.split('|');
   split.forEach((l,j)=>s+=tx(859,294+k*105+j*36,l,24,k===0?ink:muted));
  });
  s+=tx(64,625,'同一事件 ID：判定 → 案例 → 稽核 → 處置回條',25,ink);
 }
 s+=tx(64,688,'方法流程示意 · 隔離TCP交易實測',22,muted);
 s+=box(0,714,1280*t/duration,6,B,0);
 return `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="${FONT}">${s}</svg>`;
}
