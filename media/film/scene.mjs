// Deterministic method animation. Recorded aggregate data; topology illustrates the method.
import fs from 'node:fs';
const palette=JSON.parse(fs.readFileSync(new URL('../../design-system/palette.json',import.meta.url),'utf8'));
const typography=JSON.parse(fs.readFileSync(new URL('../../design-system/typography.json',import.meta.url),'utf8'));
const icons=JSON.parse(fs.readFileSync(new URL('../../design-system/icons.json',import.meta.url),'utf8'));
const cjkRuns=new RegExp('('+typography.cjk_pattern+'+)','u');
const isCjk=new RegExp('^'+typography.cjk_pattern+'+$','u');
export const duration=60;
export const playbackSpeed=2;
export const presentationDuration=duration/playbackSpeed;
export const maxDuration=40;
export const chapters=[{at:0,title:'作品名稱'},{at:5,title:'網路拓樸'},{at:13,title:'流量表徵'},{at:22,title:'17類判定'},{at:31,title:'證據檢索'},{at:40,title:'本機AI稽核'},{at:47,title:'受控處置'},{at:52,title:'實測成果'},{at:57,title:'展示結束'}];
export const chapterAt=t=>Math.max(0,chapters.findLastIndex(c=>t>=c.at));
const B=palette.blue,G=palette.gold,N=palette.navy,FONT=typography.latin+', '+typography.cjk;
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const ease=v=>1-Math.pow(1-Math.max(0,Math.min(1,v)),3);
const tx=(x,y,s,z=24,c='#171C1D',w=400,anchor='start')=>{
 const runs=String(s).split(cjkRuns).filter(Boolean).map(part=>`<tspan font-family="${isCjk.test(part)?typography.cjk:typography.latin}">${esc(part)}</tspan>`).join('');
 return `<text x="${x}" y="${y}" text-anchor="${anchor}" font-size="${z}" fill="${c}" font-weight="${w}">${runs}</text>`;
};
const box=(x,y,w,h,c,r=8)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${c}"/>`;
const line=(x,y,a,b,c='#D6DDE0')=>`<path d="M${x} ${y}L${a} ${b}" fill="none" stroke="${c}" stroke-width="3"/>`;
function node(x,y,label,kind='pc',dark=false){
 const body=icons[kind].replace(/\{\{(\w+)\}\}/g,(_,key)=>palette[key]);
 return box(x-54,y-38,108,76,palette.gray,8)+`<g transform="translate(${x-36} ${y-36}) scale(1.125)">${body}</g>`+tx(x,y+72,label,25,palette.ink,400,'middle');
}
function packet(x,y,c=G){return box(x-11,y-8,22,16,c,2)+`<path d="M${x-11} ${y-8}L${x} ${y+1}L${x+11} ${y-8}" fill="none" stroke="${c===G?N:'#FFFFFF'}" stroke-width="1.5"/>`;}
function topology(t,dark){
 let s=box(60,175,718,410,'#FFFFFF',12);const nodes=[[110,245,'正常使用者','pc'],[110,455,'異常來源','pc'],[310,350,'核心交換器','switch'],[515,350,'策略閘道','fw'],[715,350,'應用服務','server']];
 [[110,245,310,350],[110,455,310,350],[310,350,515,350],[515,350,715,350]].forEach(v=>s+=line(...v));
 nodes.forEach(v=>s+=node(...v,dark));
 // A separate branch makes the inference/evidence chain visible.
 s+=line(362,350,390,350)+line(390,350,390,530)+line(390,530,363,530)+line(310,530,715,530);
 [['IDS',310],['Top-5',515],['AI Judge',715]].forEach(([name,x],k)=>{
  const active=t>=[13,31,40][k];
  s+=box(x-53,505,106,54,active?G:(dark?'#171C1D':'#F0F2F3'))+tx(x,539,name,22,active?N:(dark?'#D6DDE0':'#53666E'),400,'middle');
 });
 if(t>=13&&t<31){const d=260*((t*.24)%1),x=390-(d-180);if(d<180)s+=packet(390,350+d);else if(x>377)s+=packet(x,530);}
 if(t>=31){const x=310+(t>=40?405:205)*((t*.24)%1);if((x>376&&x<447)||(x>581&&x<649))s+=packet(x,530);}
 if(t>=47)s+=`<path d="M715 505V480H585V350H567" fill="none" stroke="${B}" stroke-width="3" stroke-dasharray="7 5"/>`+tx(620,465,'策略檢查',25,dark?'#D6DDE0':'#53666E');
 const p=(t*.38)%1;
 s+=packet(110+200*p,245+105*p)+packet(310+405*((t*.28)%1),350);
 if(t<48||t>=50.8)s+=packet(110+200*((t*.5)%1),455-105*((t*.5)%1),dark?'#D6DDE0':'#53666E');
 if(t>=48&&t<50.8)s+=box(450,260,136,42,G,21)+tx(518,289,'規則生效',26,N,400,'middle');
 if(t>=50.8)s+=box(450,260,136,42,G,21)+tx(518,289,'到期回復',26,N,400,'middle');
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
export function frameSvg(t){
 const i=chapterAt(t),local=t-chapters[i].at,dark=false,bg=i>=7?'#F0F2F3':'#FFFFFF',ink=dark?'#FFFFFF':'#171C1D',muted=dark?'#D6DDE0':'#53666E';
 let s=box(0,0,1280,720,bg,0);
 if(i>0&&i<7){const labels=['流量','表徵','判定','檢索','稽核','回復'];labels.forEach((label,k)=>{const x=650+k*94;s+=box(x,39,84,40,k===i-1?G:'#F0F2F3',20)+tx(x+42,68,label,28,k===i-1?N:'#53666E',k===i-1?600:400,'middle');});}
 if(i===0){
  s+=tx(64,78,'AI SECURITY FRAMEWORK',18,B,600);
  ['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架'].forEach((v,k)=>s+=`<g opacity="${ease((local-.25*k)/.9)}" transform="translate(0 ${(1-ease((local-.25*k)/.9))*30})">${tx(64,230+k*76,v,45,N,300)}</g>`);
  s+=tx(64,556,'從流量判定，走到有證據的處置。',30,'#53666E');
 }else if(i===8){
  s+=tx(64,88,'AI SECURITY FRAMEWORK',22,B,600);
  s+=tx(64,232,'偵測有依據',48,N,400)+tx(64,312,'稽核有證據',48,N,400)+tx(64,392,'處置可回復',48,N,400);
  s+=box(64,467,1152,80,palette.gold_tint)+tx(88,518,'判定 → 證據 → 稽核 → 處置與回復回條',30,N,600);
  s+=tx(64,625,'展示結束 · 接續架構與實測成果說明',26,'#53666E');
 }else if(i===7){
  s+=tx(64,94,'實測成果',44,N,300);
  [['98.08%','17類偵測 Accuracy'],['97.62%','Top-5 命中率'],['6 / 6','隔離情境完整回復']].forEach(([v,l],k)=>{const x=64+k*400;s+=tx(x,310,v,56,N,300)+box(x,328,210,6,G,0)+tx(x,375,l,24,'#171C1D');});
  s+=tx(64,525,'偵測有依據，稽核有證據，處置可回復。',34,'#171C1D',300)+tx(64,610,'18,998筆偵測測試／463筆檢索稽核／6種隔離情境',26,'#53666E');
 }else{
  s+=tx(64,65,`0${i} / 06`,32,dark?'#53B1FF':B,600)+tx(64,128,messages[i][0],44,N,300);
  const scale=.96+.04*ease(local/.9);
  s+=`<g transform="translate(${(1-scale)*400} ${(1-scale)*350}) scale(${scale})">${topology(t,dark)}</g>`;
  s+=box(835,225,381,300,'#F0F2F3')+box(835,225,5,300,G,2);
  if(i===3){
   s+=tx(859,264,'同一流量輸入',28,ink);
   s+=`<path d="M1025 276V285H930V292 M1025 285H1120V292 M930 342V377H1025V410 M1120 342V377H1025" fill="none" stroke="${B}" stroke-width="3"/>`;
   s+=`<path d="M925 286L930 292L935 286 M1115 286L1120 292L1125 286 M1020 404L1025 410L1030 404" fill="none" stroke="${B}" stroke-width="2"/>`;
   s+=box(860,292,140,50,B)+tx(930,325,'CTBM',28,'#FFFFFF',600,'middle');
   s+=box(1050,292,140,50,B)+tx(1120,325,'PBCNN',28,'#FFFFFF',600,'middle');
   s+=box(899,410,252,58,B)+tx(1025,447,'校準＋OOF Gate',28,'#FFFFFF',400,'middle');
   s+=tx(859,505,'17類＋信心＋模型表徵',27,ink);
  }else messages[i].slice(1).forEach((v,k)=>{
   // Keep Chinese strings readable by explicit semantic line breaks.
   const split=v.split('|');
   split.forEach((l,j)=>s+=tx(859,294+k*105+j*38,l,28,k===0?ink:muted));
  });
  s+=box(64,593,1152,60,'#F0F2F3')+tx(88,632,'同一事件 ID：判定 → 案例 → 稽核 → 處置回條',25,ink);
 }
 s+=tx(64,688,'方法流程示意 · 隔離TCP交易實測',26,muted);
 s+=box(0,714,1280*t/duration,6,B,0);
 return `<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="${FONT}">${s}</svg>`;
}
