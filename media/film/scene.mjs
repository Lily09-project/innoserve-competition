// Deterministic method animation. Recorded aggregate data; topology illustrates the method.
export const duration=60;
export const chapters=[{at:0,title:'作品名稱'},{at:5,title:'網路拓樸'},{at:13,title:'流量表徵'},{at:22,title:'17類判定'},{at:31,title:'證據檢索'},{at:40,title:'本機AI稽核'},{at:48,title:'受控處置'},{at:55,title:'實測成果'}];
export const chapterAt=t=>Math.max(0,chapters.findLastIndex(c=>t>=c.at));
const B='#0070D1',FONT='Microsoft JhengHei, Arial';
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const ease=v=>1-Math.pow(1-Math.max(0,Math.min(1,v)),3);
const tx=(x,y,s,z=24,c='#000000',w=400)=>`<text x="${x}" y="${y}" font-size="${z}" fill="${c}" font-weight="${w}">${esc(s)}</text>`;
const box=(x,y,w,h,c,r=8)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${c}"/>`;
const line=(x,y,a,b,c='#CCCCCC')=>`<path d="M${x} ${y}L${a} ${b}" fill="none" stroke="${c}" stroke-width="3"/>`;
function node(x,y,label,kind='pc',dark=false){
 const ink=dark?'#FFFFFF':'#000000',fill=dark?'#181818':'#F5F7FA';
 let s=box(x-52,y-34,104,68,fill)+`<rect x="${x-35}" y="${y-22}" width="70" height="43" rx="4" fill="none" stroke="${B}" stroke-width="3"/>`;
 if(kind==='pc')s+=line(x,y+22,x,y+38,B)+line(x-22,y+38,x+22,y+38,B);
 else for(let k=0;k<3;k++)s+=line(x-23,y-12+k*12,x+23,y-12+k*12,B);
 return s+tx(x-55,y+72,label,18,ink);
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
  s+=box(x-53,505,106,54,active?B:(dark?'#181818':'#F5F7FA'))+tx(x-40,539,name,18,active?'#FFFFFF':(dark?'#CCCCCC':'#6B6B6B'));
 });
 if(t>=13&&t<31){const d=260*((t*.24)%1);s+=d<180?packet(390,350+d):packet(390-(d-180),530);}
 if(t>=31)s+=packet(310+(t>=40?405:205)*((t*.24)%1),530);
 if(t>=48)s+=`<path d="M715 505V480H585V350H567" fill="none" stroke="${B}" stroke-width="3" stroke-dasharray="7 5"/>`+tx(620,465,'策略檢查',17,dark?'#CCCCCC':'#6B6B6B');
 const p=(t*.38)%1;
 s+=packet(110+200*p,245+105*p)+packet(310+405*((t*.28)%1),350);
 if(t<49||t>53)s+=packet(110+200*((t*.5)%1),455-105*((t*.5)%1),dark?'#CCCCCC':'#6B6B6B');
 if(t>=49&&t<=53)s+=box(460,260,116,38,B,19)+tx(478,286,'規則生效',19,'#FFFFFF');
 if(t>53)s+=box(460,260,116,38,B,19)+tx(478,286,'到期回復',19,'#FFFFFF');
 return s;
}
const messages=[
 [],['封包流動','正常與異常流量，進入事件鏈'],
 ['流量表徵','封包內容・時間差・方向','遮罩識別欄位，再切分流量'],
 ['17 類判定','CTBM＋PBCNN → OOF Gate','正式類別＋校準信心＋模型表徵'],
 ['任務導向檢索','512＋17 → 529 維','訓練案例庫 → Top-5 相似案例'],
 ['本機 AI 稽核','支持／複核／不確定','依案例核對，保留正式分類'],
 ['受控處置與回復','策略檢查 → 套用 → 讀回','到期撤銷，保留事件回條']
];
export function frameSvg(t){
 const i=chapterAt(t),local=t-chapters[i].at,dark=[0,3,5].includes(i),bg=i===7?B:dark?'#000000':'#FFFFFF',ink=dark?'#FFFFFF':'#000000',muted=dark?'#CCCCCC':'#6B6B6B';
 let s=box(0,0,1280,720,bg,0);
 if(i===0){
  s+=tx(64,78,'AI SECURITY FRAMEWORK',18,'#53B1FF',600);
  ['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架'].forEach((v,k)=>s+=`<g opacity="${ease((local-.25*k)/.9)}" transform="translate(0 ${(1-ease((local-.25*k)/.9))*30})">${tx(64,230+k*76,v,45,'#FFFFFF',300)}</g>`);
  s+=tx(64,556,'從流量判定，走到有證據的處置。',30,'#CCCCCC');
 }else if(i===7){
  s+=tx(64,94,'實測成果',44,'#FFFFFF',300);
  [['98.08%','17類偵測 Accuracy'],['97.62%','Top-5 命中率'],['6 / 6','隔離情境完整回復']].forEach(([v,l],k)=>{const x=64+k*400;s+=tx(x,310,v,62,'#FFFFFF',300)+tx(x,375,l,25,'#FFFFFF');});
  s+=tx(64,525,'偵測有依據，稽核有證據，處置可回復。',34,'#FFFFFF',300)+tx(64,610,'18,998筆偵測測試／463筆檢索稽核／6種隔離情境',23,'#FFFFFF');
 }else{
  s+=tx(64,65,`0${i} / 06`,18,dark?'#53B1FF':B,600)+tx(64,128,messages[i][0],44,ink,300);
  const scale=.96+.04*ease(local/.9);
  s+=`<g transform="translate(${(1-scale)*400} ${(1-scale)*350}) scale(${scale})">${topology(t,dark)}</g>`;
  s+=box(835,225,381,300,dark?'#181818':'#F5F7FA');
  messages[i].slice(1).forEach((v,k)=>{
   // Keep Chinese strings readable by explicit semantic line breaks.
   const split=[];let row='',units=0;for(const ch of v){const u=ch.charCodeAt(0)<128?.55:1;if(units+u>15.4){split.push(row);row='';units=0;}row+=ch;units+=u;}if(row)split.push(row);
   split.forEach((l,j)=>s+=tx(859,294+k*105+j*36,l,21,k===0?ink:muted));
  });
  s+=tx(64,625,'同一事件 ID：判定 → 案例 → 稽核 → 處置回條',25,ink);
 }
 s+=tx(64,688,'方法流程示意 · 隔離TCP交易實測',16,i===7?'#FFFFFF':muted);
 s+=box(0,714,1280*t/duration,6,i===7?'#FFFFFF':B,0);
 return `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="${FONT}">${s}</svg>`;
}
