// Packet Tracer–style simulation film. Pure time -> SVG; shared by the browser player and the MP4 renderer.
// Every figure shown comes from results/ or the overview document; packet contents stay de-identified.
export const TITLE_ZH=['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架'];
export const TITLE_EN='An AI Security Framework Integrating Novel Content Dependent Temporal Directional Intrusion Detection and Task Oriented Retrieval Augmented';
export const duration=60;
export const chapters=[
 {at:0,title:'作品名稱'},
 {at:4,title:'建立網路拓樸'},
 {at:9,title:'流量擷取與前處理'},
 {at:17,title:'17 類偵測'},
 {at:25,title:'Top-5 證據檢索'},
 {at:32,title:'AI 證據稽核'},
 {at:39,title:'受控處置與回復'},
 {at:50,title:'事件輸出'},
 {at:56,title:'結語'}
];
export function chapterAt(t){let i=chapters.length-1;while(i>0&&t<chapters[i].at)i--;return i}

const C={bg:'#F4F7FB',grid:'#E3EAF4',panel:'#FFFFFF',ink:'#0B1B33',muted:'#5B6B82',faint:'#94A3B8',line:'#C9D3E3',
 blue:'#1D4ED8',teal:'#0F766E',violet:'#6D28D9',amber:'#B45309',orange:'#C2410C',red:'#DC2626',green:'#16A34A'};
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const io=v=>{v=clamp(v);return v<.5?4*v*v*v:1-Math.pow(-2*v+2,3)/2};
const out=v=>1-Math.pow(1-clamp(v),3);
const spring=v=>{v=clamp(v,0,4);return v<=0?0:1-Math.exp(-7*v)*Math.cos(11*v)};
const win=(t,a,b,f=.35)=>Math.min(out((t-a)/f),out((b-t)/f));
const lerp=(a,b,k)=>a+(b-a)*k;
const xesc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const T=(x,y,s,size=16,fill=C.ink,w=400,anchor='start',extra='')=>`<text x="${x}" y="${y}" font-size="${size}" fill="${fill}" font-weight="${w}" text-anchor="${anchor}"${extra}>${xesc(s)}</text>`;
const M=(x,y,s,size=12,fill=C.ink,w=400,anchor='start')=>T(x,y,s,size,fill,w,anchor,' font-family="Cascadia Mono, Consolas, monospace"');
const R=(x,y,w,h,fill=C.panel,stroke=C.line,r=10,extra='')=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}"${extra}/>`;
const L=(x1,y1,x2,y2,c=C.line,w=2,extra='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" stroke-linecap="round"${extra}/>`;
const G=(o,inner,tf='')=>o<=0.001?'':`<g opacity="${clamp(o).toFixed(3)}"${tf?` transform="${tf}"`:''}>${inner}</g>`;
const hash=n=>{const x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x)};

/* ---------------- topology (world coordinates) ---------------- */
const D={
 user:{x:90,y:230,k:'pc',name:'User-PC',sub:'正常使用者',c:C.green,at:4.2},
 bot:{x:90,y:430,k:'pc',name:'Bot-PC',sub:'異常來源',c:C.red,at:4.4},
 sw:{x:240,y:330,k:'switch',name:'Switch-0',sub:'核心交換器',c:C.blue,at:4.6},
 tap:{x:240,y:510,k:'tap',name:'Mirror-TAP',sub:'鏡像擷取',c:C.blue,at:4.8},
 rt:{x:390,y:330,k:'router',name:'Router-0',sub:'邊界路由',c:C.blue,at:5.0},
 fw:{x:540,y:330,k:'fw',name:'Policy-Guard',sub:'策略閘道',c:C.orange,at:5.2},
 web:{x:690,y:330,k:'server',name:'Web-Server',sub:'應用服務',c:C.blue,at:5.4},
 ids:{x:390,y:510,k:'server',name:'IDS-Server',sub:'CTBM＋PBCNN',c:C.teal,at:5.6},
 rag:{x:540,y:510,k:'db',name:'RAG-Store',sub:'train-only 案例庫',c:C.violet,at:5.8},
 llm:{x:690,y:510,k:'ai',name:'LLM-Judge',sub:'本機 Llama 3 8B',c:C.amber,at:6.0},
};
const LINKS=[['user','sw'],['bot','sw'],['sw','rt'],['rt','fw'],['fw','web'],['sw','tap'],['tap','ids'],['ids','rag'],['rag','llm'],['llm','fw']];
const P=n=>[D[n].x,D[n].y];

function icon(d,t){
 const {x,y,k,c}=d,s=spring((t-d.at)/0.9);if(s<=0)return '';
 let g='';
 const sh=`<ellipse cx="0" cy="34" rx="34" ry="7" fill="#0B1B33" opacity=".07"/>`;
 if(k==='pc')g=`${sh}<rect x="-26" y="-24" width="52" height="36" rx="4" fill="#fff" stroke="${c}" stroke-width="2.5"/><rect x="-21" y="-19" width="42" height="26" rx="2" fill="${c}" opacity=".14"/><path d="M-10 22h20M0 12v10" stroke="${c}" stroke-width="2.5"/>`;
 else if(k==='switch')g=`${sh}<rect x="-34" y="-14" width="68" height="28" rx="6" fill="#EEF4FF" stroke="${c}" stroke-width="2.5"/><path d="M-22-4h16m-5-4 5 4-5 4M22 4H6m5-4-5 4 5 4" stroke="${c}" stroke-width="2.2" fill="none"/>`;
 else if(k==='router')g=`${sh}<path d="M-32-10v18a32 12 0 0 0 64 0v-18" fill="#EEF4FF" stroke="${c}" stroke-width="2.5"/><ellipse cx="0" cy="-10" rx="32" ry="12" fill="#fff" stroke="${c}" stroke-width="2.5"/><path d="M-14-12l8-2-2 6M14-8l-8 2 2-6" stroke="${c}" stroke-width="2" fill="none"/>`;
 else if(k==='fw')g=`${sh}<rect x="-30" y="-24" width="60" height="48" rx="4" fill="#FFF1E8" stroke="${c}" stroke-width="2.5"/><path d="M-30-8h60M-30 8h60M-10-24v16M10-8v16M-10 8v16M20-24v16M-20-8v16" stroke="${c}" stroke-width="2"/>`;
 else if(k==='server')g=`${sh}<rect x="-22" y="-30" width="44" height="60" rx="5" fill="#fff" stroke="${c}" stroke-width="2.5"/><path d="M-14-16h28M-14-4h28M-14 8h28" stroke="${c}" stroke-width="2.2"/><circle cx="12" cy="20" r="3" fill="${c}"/>`;
 else if(k==='db')g=`${sh}<path d="M-24-20v40c0 8 48 8 48 0v-40" fill="#fff" stroke="${c}" stroke-width="2.5"/><ellipse cx="0" cy="-20" rx="24" ry="8" fill="#F3EEFF" stroke="${c}" stroke-width="2.5"/><path d="M-24 0c0 8 48 8 48 0" stroke="${c}" stroke-width="2" fill="none"/>`;
 else if(k==='ai')g=`${sh}<rect x="-26" y="-22" width="52" height="42" rx="10" fill="#fff" stroke="${c}" stroke-width="2.5"/><circle cx="-10" cy="-3" r="5" fill="${c}"/><circle cx="10" cy="-3" r="5" fill="${c}"/><path d="M-8 10h16M0-22v-8" stroke="${c}" stroke-width="2.5"/><circle cx="0" cy="-32" r="4" fill="${c}"/>`;
 else g=`${sh}<rect x="-26" y="-18" width="52" height="36" rx="18" fill="#EEF4FF" stroke="${c}" stroke-width="2.5"/><circle r="9" fill="none" stroke="${c}" stroke-width="2.5"/><circle r="3" fill="${c}"/>`;
 return `<g transform="translate(${x} ${y}) scale(${s.toFixed(3)})">${g}</g>`+G(out((t-d.at-.3)/.5),T(x,y+56,d.name,13,C.ink,700,'middle')+T(x,y+73,d.sub,11,C.muted,400,'middle'));
}
function links(t){
 return LINKS.map(([a,b],k)=>{const [x1,y1]=P(a),[x2,y2]=P(b),p=io((t-4.3-k*.12)/.6);if(p<=0)return '';
  const ctrl=a==='llm';return L(x1,y1,lerp(x1,x2,p),lerp(y1,y2,p),ctrl?C.amber:C.line,ctrl?2:3,ctrl?' stroke-dasharray="6 6"':'')}).join('');
}
function env(x,y,color,s=1,blocked=false){
 return `<g transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) scale(${s.toFixed(3)})"><rect x="-13" y="-9" width="26" height="18" rx="2" fill="${color}" stroke="#fff" stroke-width="1.5"/><path d="M-13-9 0 2 13-9" stroke="#fff" stroke-width="1.5" fill="none"/>${blocked?'<path d="M-9-9 9 9M9-9-9 9" stroke="#fff" stroke-width="3"/>':''}</g>`;
}
function along(path,p){
 const pts=path.map(P);let tot=0;const seg=[];
 for(let i=1;i<pts.length;i++){const d=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);seg.push(d);tot+=d}
 let dist=clamp(p)*tot;for(let i=0;i<seg.length;i++){if(dist<=seg[i]||i===seg.length-1){const k=seg[i]?clamp(dist/seg[i]):0;return [lerp(pts[i][0],pts[i+1][0],k),lerp(pts[i][1],pts[i+1][1],k)]}dist-=seg[i]}
}
function pdu(path,t,t0,dur,color,opts={}){
 const p=(t-t0)/dur;if(p<0||p>1)return '';
 const [x,y]=along(path,io(p));const pop=Math.min(spring(p*dur/0.4),1.15);
 return env(x,y,color,pop*(opts.s||1),opts.blocked&&p>0.9);
}
// ambient traffic keeps the scene alive; Bot traffic stops at the gateway while the ACL is active
function ambient(t){
 let s='';const blockOn=st=>st>=41.4&&st<46.2;
 for(let k=0;k<6;k++)for(let r=0;r<9;r++)s+=pdu(['user','sw','rt','fw','web'],t,6.4+k*1.7+r*10.2,2.2,C.green,{s:.8});
 for(let k=0;k<5;k++)for(let r=0;r<12;r++){const st=6.8+k*1.1+r*5.5;
  s+=blockOn(st+1.2)?pdu(['bot','sw','rt','fw'],t,st,1.6,C.red,{s:.8,blocked:true}):pdu(['bot','sw','rt','fw','web'],t,st,2.1,C.red,{s:.8})}
 return s;
}

/* ---------------- camera ---------------- */
const CAM=[[0,390,380,1],[8.6,390,380,1],[9.8,240,470,1.35],[16.4,240,470,1.35],[17.4,390,470,1.4],[24.4,390,470,1.4],
 [25.4,540,480,1.4],[31.4,540,480,1.4],[32.4,690,480,1.4],[38.4,690,480,1.4],[39.4,540,330,1.35],[49.2,540,330,1.35],[50.4,390,380,1]];
function camera(t){
 let i=0;while(i<CAM.length-1&&t>CAM[i+1][0])i++;
 const a=CAM[i],b=CAM[Math.min(i+1,CAM.length-1)],k=b[0]===a[0]?0:io((t-a[0])/(b[0]-a[0]));
 const fx=lerp(a[1],b[1],k),fy=lerp(a[2],b[2],k),z=lerp(a[3],b[3],k),sx=lerp(400,360,clamp((z-1)/.4)),sy=360;
 return `translate(${(sx-fx*z).toFixed(1)} ${(sy-fy*z).toFixed(1)}) scale(${z.toFixed(3)})`;
}

/* ---------------- PT-style PDU windows ---------------- */
function ptWindow(t,a,b,title,device,color,body){
 const o=win(t,a,b,.4);if(o<=0)return '';const s=spring((t-a)/0.8),x=770,y=86,w=474,h=470;
 return `<g opacity="${o.toFixed(3)}" transform="translate(${x+w/2} ${y+h/2}) scale(${(0.9+0.1*Math.min(s,1.05)).toFixed(3)}) translate(${-x-w/2} ${-y-h/2})">`
  +R(x+4,y+8,w,h,'#0B1B33','none',12,' opacity=".06"')+R(x,y,w,h,C.panel,C.line,12)
  +`<path d="M${x} ${y+12}a12 12 0 0 1 12-12h${w-24}a12 12 0 0 1 12 12v22h-${w}z" fill="${color}"/>`
  +T(x+16,y+23,`PDU Information at Device: ${device}`,13,'#fff',700)+T(x+w-16,y+23,'✕',13,'#fff',700,'end')
  +R(x+14,y+44,96,24,color+'18',color,6)+T(x+62,y+61,'OSI Model',12,color,700,'middle')+R(x+116,y+44,104,24,C.panel,C.line,6)+T(x+168,y+61,'Inbound PDU',12,C.muted,400,'middle')+R(x+226,y+44,112,24,C.panel,C.line,6)+T(x+282,y+61,'Outbound PDU',12,C.muted,400,'middle')
  +T(x+16,y+96,title,16,C.ink,700)+body(x,y+8,w,h)+'</g>';
}
const lbl=(x,y,s,c)=>R(x,y-15,s.length*7.6+22,22,c+'14','none',11)+T(x+11,y,s,12,c,700);

function stage1(t){return ptWindow(t,9.6,16.8,'輸入：鏡像流量　→　輸出：模型張量','Mirror-TAP',C.blue,(x,y)=>{
 let s=lbl(x+16,y+124,'Inbound · 原始封包（去識別化）',C.blue);
 for(let k=0;k<6;k++){const o=out((t-10.2-k*.25)/.3),up=[1,0,1,1,0,1][k],w=60+hash(k+9)*110;
  s+=G(o,R(x+16,y+136+k*25,210,21,k%2?C.panel:'#F1F5FB','none',4)+M(x+24,y+151+k*25,`#${String(k+1).padStart(2,'0')}`,11,C.muted)+M(x+60,y+151+k*25,up?'→':'←',12,up?C.blue:C.green,700)+`<rect x="${x+84}" y="${y+142+k*25}" width="${w.toFixed(0)}" height="9" rx="3" fill="${up?C.blue:C.green}" fill-opacity=".3"/>`)}
 s+=G(out((t-12)/.6),lbl(x+246,y+124,'Process',C.blue)+['雙向 Flow 組裝','IP／Port 去識別化','三種模型輸入'].map((l,k)=>G(out((t-12.2-k*.45)/.4),R(x+246,y+136+k*44,212,36,'#F1F5FB','none',8)+T(x+260,y+159+k*44,`${k+1}  ${l}`,13,C.ink,700))).join(''));
 const q=out((t-13.6)/.6);
 s+=G(q,lbl(x+16,y+312,'Outbound · 內容 bytes',C.blue));
 for(let r=0;r<5;r++)for(let k=0;k<20;k++){const v=hash(r*31+k)**1.6;s+=G(q*out((t-13.8-k*.03)/.3),`<rect x="${x+16+k*10.5}" y="${y+324+r*11}" width="9.5" height="10" fill="${C.blue}" fill-opacity="${(.1+v*.85).toFixed(2)}"/>`)}
 s+=G(out((t-14.4)/.5),lbl(x+246,y+312,'Δt × 方向序列',C.blue)+Array.from({length:18},(_,k)=>{const up=hash(k+50)>.45,hh=(6+hash(k+70)*22)*out((t-14.6-k*.04)/.3);return `<rect x="${x+248+k*11.5}" y="${(up?y+356-hh:y+356).toFixed(1)}" width="8" height="${hh.toFixed(1)}" fill="${up?C.blue:'#93C5FD'}"/>`}).join('')+L(x+246,y+356,x+458,y+356,C.muted,1));
 s+=G(out((t-15)/.5),T(x+16,y+418,'資料集：CICIDS2017 · CSE-CIC-IDS2018（同一事件格式）',12,C.muted));
 return s;})}

function stage2(t){return ptWindow(t,17.6,24.8,'輸入：模型張量　→　輸出：17 類正式機率','IDS-Server',C.teal,(x,y)=>{
 let s=lbl(x+16,y+124,'Process · 雙分支融合',C.teal);
 [['CTBM','內容・時間差・方向'],['PBCNN','短窗位元組'],['溫度校準','降低過度自信'],['OOF Gate','59 項證據融合']].forEach(([a,b],k)=>{const o=spring((t-18.1-k*.35)/.7),xx=x+16+(k%2)*222,yy=y+136+Math.floor(k/2)*58;
  s+=G(clamp(o*1.5),`<g transform="translate(${xx+107} ${yy+25}) scale(${Math.min(o,1.06).toFixed(3)}) translate(${-xx-107} ${-yy-25})">`+R(xx,yy,214,50,'#F0FAF7',C.teal+'66',8)+T(xx+14,yy+22,a,14,C.teal,700)+T(xx+14,yy+41,b,11.5,C.muted)+'</g>')});
 s+=G(out((t-19.8)/.8),lbl(x+16,y+278,'Outbound · 17 類機率',C.teal));
 for(let k=0;k<17;k++){const h=(k===13?92:6+hash(k+3)*12)*out((t-20-k*.05)/.6);if(h>0)s+=`<rect x="${x+20+k*15}" y="${(y+388-h).toFixed(1)}" width="10" height="${h.toFixed(1)}" rx="2" fill="${k===13?C.teal:'#A7DCD3'}"/>`}
 s+=G(out((t-21.2)/.4),L(x+16,y+388,x+272,y+388,C.muted,1)+T(x+20+13*15+5,y+290,'Bot',12,C.teal,700,'middle')+M(x+16,y+404,'0 BENIGN',10,C.faint)+M(x+272,y+404,'16 Heartbleed',10,C.faint,400,'end'));
 [['Accuracy','98.08%'],['Macro-F1','93.05%'],['Bot Recall','98.40%']].forEach(([a,b],k)=>{s+=G(out((t-21.6-k*.3)/.4),R(x+292,y+296+k*44,166,36,'#F0FAF7','none',8)+T(x+304,y+319+k*44,a,12,C.muted)+T(x+448,y+320+k*44,b,15,C.teal,700,'end'))});
 s+=G(out((t-22.6)/.4),T(x+16,y+432,'18,998 筆封存測試 · 固定 17 類順序',12,C.muted));
 return s;})}

function stage3(t){return ptWindow(t,25.6,31.8,'輸入：529 維任務向量　→　輸出：Top-5 案例證據','RAG-Store',C.violet,(x,y)=>{
 let s=lbl(x+16,y+124,'Inbound · 512 維表徵 ∥ 17 維機率',C.violet);
 for(let k=0;k<40;k++)s+=G(out((t-25.9-k*.02)/.3),`<rect x="${x+16+k*10.8}" y="${y+136}" width="9" height="30" fill="${k<36?C.violet:'#EA580C'}" fill-opacity="${(.2+hash(k)*.7).toFixed(2)}"/>`);
 const cx=x+130,cy=y+290;s+=G(out((t-26.6)/.5),lbl(x+16,y+196,'Process · 餘弦相似度',C.violet));
 for(let k=0;k<70;k++){const a=hash(k)*6.283,r=22+hash(k+200)*80;s+=G(out((t-26.8-k*.008)/.3),`<circle cx="${(cx+Math.cos(a)*r*1.25).toFixed(1)}" cy="${(cy+Math.sin(a)*r*.75).toFixed(1)}" r="3" fill="${C.faint}" fill-opacity=".5"/>`)}
 const sweep=out((t-27.6)/1.2);
 s+=G(sweep,`<circle cx="${cx}" cy="${cy}" r="${(10+sweep*36).toFixed(1)}" fill="${C.violet}" fill-opacity=".07" stroke="${C.violet}" stroke-dasharray="4 4"/>`);
 [[-20,-12],[16,-18],[24,10],[-12,20],[-30,4]].forEach(([dx,dy],k)=>{s+=G(out((t-28-k*.2)/.3),L(cx,cy,cx+dx*1.4,cy+dy*1.4,C.violet,1.5)+`<circle cx="${cx+dx*1.4}" cy="${cy+dy*1.4}" r="5" fill="${C.violet}"/>`)});
 s+=G(out((t-27.4)/.3),`<circle cx="${cx}" cy="${cy}" r="7" fill="#EA580C" stroke="#fff" stroke-width="2"/>`);
 s+=G(out((t-28.4)/.4),lbl(x+262,y+196,'Outbound · Top-5',C.violet));
 for(let k=0;k<5;k++){const o=out((t-28.6-k*.18)/.35);s+=G(o,M(x+262,y+228+k*30,`#${k+1}`,12,C.violet,700)+`<rect x="${x+292}" y="${y+218+k*30}" width="${((150-k*14)*o).toFixed(1)}" height="12" rx="6" fill="${C.violet}" fill-opacity="${(1-k*.13).toFixed(2)}"/>`)}
 [['Top-5','96.76%'],['MRR@5','94.25%']].forEach(([a,b],k)=>{s+=G(out((t-29.6-k*.3)/.4),R(x+262+k*100,y+384,92,48,'#F5F1FE','none',8)+T(x+272+k*100,y+402,a,11,C.muted)+T(x+272+k*100,y+424,b,15,C.violet,700))});
 s+=G(out((t-29.8)/.4),T(x+16,y+424,'案例庫 1,550 筆 · 檢索中位數 1.01 ms',12,C.muted));
 return s;})}

function stage4(t){return ptWindow(t,32.6,38.8,'輸入：類別＋信心＋Top-5　→　輸出：稽核 JSON','LLM-Judge',C.amber,(x,y)=>{
 let s=lbl(x+16,y+124,'Inbound · 稽核提示',C.amber);
 ['正式類別與信心','CTBM／PBCNN 分支觀察','Top-5 標籤與相似度'].forEach((l,k)=>{s+=G(out((t-32.9-k*.25)/.35),R(x+16,y+136+k*34,200,28,'#FFF7ED','none',6)+T(x+28,y+155+k*34,l,12.5,C.ink,700))});
 s+=G(out((t-33.8)/.35),R(x+16,y+238,200,28,'#FEF2F2','none',6)+T(x+28,y+257,'測試答案不進入提示',12.5,C.red,700));
 s+=G(out((t-34)/.5),lbl(x+234,y+124,'Outbound · 結構化回覆',C.amber)+R(x+234,y+136,224,134,'#0B1B33','none',8));
 const lines=['{','  "assessment": "support",','  "reason": "Top-5 證據一致",','  "classification_changed":','      false','}'];
 const typed=Math.floor(clamp((t-34.3)/2.2)*lines.join('').length);let used=0;
 lines.forEach((l,k)=>{const n=clamp(typed-used,0,l.length);used+=l.length;if(n>0)s+=M(x+246,y+158+k*19,l.slice(0,n),11.5,k===1?'#6EE7B7':'#CFE0F7')});
 [['支持','415',C.teal],['複核','13',C.amber],['不確定','35',C.amber]].forEach(([a,n,c],k)=>{const p=spring((t-35.4-k*.25)/.7);if(p>0)s+=`<g transform="translate(${x+51+k*76} ${y+316}) scale(${Math.min(p,1.1).toFixed(3)})">`+R(-35,-22,70,44,c+'14',c,10)+T(0,-3,a,12,c,700,'middle')+T(0,14,`${n} 筆`,11,C.muted,400,'middle')+'</g>'});
 [['有效 JSON','463 / 463'],['分類被改寫','0 筆'],['外部 API','0 次']].forEach(([a,b],k)=>{s+=G(out((t-36.2-k*.3)/.4),R(x+250,y+290+k*42,208,34,'#FFF7ED','none',8)+T(x+262,y+312+k*42,a,12,C.muted)+T(x+448,y+313+k*42,b,14,C.amber,700,'end'))});
 s+=G(out((t-37)/.4),T(x+16,y+374,'463 筆整合查詢 · 只有「支持」可進入處置',12,C.muted));
 return s;})}

function stage5(t){return ptWindow(t,39.6,49.4,'輸入：支持事件　→　輸出：處置回條（Bot 實測）','Policy-Guard',C.orange,(x,y)=>{
 let s=lbl(x+16,y+124,'Process · 處置門檻與動作',C.orange);
 [['稽核結果 = 支持',39.9],['分類信心 ≥ 0.80',40.2],['Top-5 同類 ≥ 4',40.5],['套用 block_c2_destination（1 條）',41.2],['規則讀回一致',41.8],['TTL 30 秒到期撤銷',46.2]].forEach(([l,at],k)=>{const o=spring((t-at)/.6);
  if(o>0)s+=`<g transform="translate(${x+28} ${y+150+k*30}) scale(${Math.min(o,1.15).toFixed(3)})"><circle r="9" fill="${k<3?C.teal:C.orange}"/><path d="M-4 0l3 3 6-6" stroke="#fff" stroke-width="2.2" fill="none"/></g>`+G(clamp(o),T(x+46,y+155+k*30,l,13,C.ink,k>=3?700:400))});
 const ttl=clamp((t-42)/4.2),done=t>46.2;
 s+=G(out((t-41.8)/.4),`<circle cx="${x+400}" cy="${y+190}" r="44" fill="none" stroke="#FDE7D9" stroke-width="9"/><circle cx="${x+400}" cy="${y+190}" r="44" fill="none" stroke="${C.orange}" stroke-width="9" stroke-linecap="round" stroke-dasharray="${(276.5*ttl).toFixed(1)} 400" transform="rotate(-90 ${x+400} ${y+190})"/>`+T(x+400,y+188,done?'已撤銷':'TTL',done?15:17,C.orange,700,'middle')+T(x+400,y+208,done?'30.12 秒':'30 秒',12,C.muted,400,'middle'));
 s+=G(out((t-42.4)/.5),lbl(x+16,y+344,'Outbound · 交易成功率',C.orange));
 [['攻擊型 套用前',1,C.muted,42.6],['攻擊型 套用後',0,C.red,43.4],['背景服務',1,C.green,44.2],['回復後',1,C.green,46.8]].forEach(([l,v,c,at],k)=>{const o=out((t-at)/.6),xx=x+16,yy=y+356+k*24;
  s+=G(clamp((t-at)/.2),T(xx,yy+13,l,12,C.ink)+R(xx+120,yy+3,260,12,'#F1F5FB','none',6)+`<rect x="${xx+120}" y="${yy+3}" width="${Math.max(3,260*v*o).toFixed(1)}" height="12" rx="6" fill="${c}"/>`+T(xx+442,yy+14,`${Math.round(v*100*o)}%`,13,c,700,'end'))});
 return s;})}

function stage6(t){
 const o=win(t,50.4,55.8,.4);if(o<=0)return '';
 const x=770,y=86;let s=R(x,y,474,470,C.panel,C.line,12)+`<path d="M${x} ${y+12}a12 12 0 0 1 12-12h450a12 12 0 0 1 12 12v22h-474z" fill="${C.ink}"/>`+T(x+16,y+23,'Event Record · 同一事件識別碼',13,'#fff',700);
 ['DetectionEvent','Evidence Top-5','Judge JSON','Policy Receipt','Network Receipt'].forEach((l,k)=>{const p=spring((t-50.8-k*.3)/.7);if(p>0)s+=`<g transform="translate(${x+150} ${y+84+k*62}) scale(${Math.min(p,1.08).toFixed(3)})">`+R(-120,-20,240,40,'#F1F5FB','none',8)+M(-104,5,l,13,C.ink,700)+M(104,5,'sha256 ✓',11,C.green,700,'end')+'</g>';if(k<4)s+=G(out((t-51.1-k*.3)/.3),L(x+150,y+104+k*62,x+150,y+126+k*62,C.muted,2))});
 [['17 / 17','即時重跑'],['6 / 6','背景服務保留'],['6 / 6','完整回復'],['0','分類被改寫']].forEach(([v,l],k)=>{s+=G(out((t-52.4-k*.25)/.4),R(x+300,y+56+k*96,158,82,'#F1F5FB','none',10)+T(x+314,y+98+k*96,v,26,[C.blue,C.teal,C.teal,C.amber][k],700)+T(x+314,y+124+k*96,l,12,C.muted))});
 s+=G(out((t-53.4)/.4),T(x+16,y+452,'事件 ID 與執行 ID 綁定 · 可匯出完整稽核紀錄',12,C.muted));
 return G(o,s);
}

/* ---------------- PT simulation panel (event list) ---------------- */
const EVENTS=[[9.4,'Bot-PC','Mirror-TAP','TCP',C.red],[12.4,'Mirror-TAP','Mirror-TAP','FLOW',C.blue],[17.3,'Mirror-TAP','IDS-Server','TENSOR',C.blue],[21,'IDS-Server','IDS-Server','DETECT',C.teal],
 [25.3,'IDS-Server','RAG-Store','VEC529',C.teal],[28.6,'RAG-Store','RAG-Store','TOP-5',C.violet],[32.3,'RAG-Store','LLM-Judge','PROMPT',C.violet],[35.6,'LLM-Judge','LLM-Judge','JUDGE',C.amber],
 [39.3,'LLM-Judge','Policy-Guard','POLICY',C.amber],[41.4,'Policy-Guard','Policy-Guard','APPLY',C.orange],[43.4,'Bot-PC','Policy-Guard','TCP ✕',C.red],[46.2,'Policy-Guard','Policy-Guard','ROLLBACK',C.green],[50.6,'Policy-Guard','Event-Log','RECEIPT',C.ink]];
function simPanel(t){
 const o=out((t-6.2)/.6);if(o<=0)return '';const x=36,y=586,w=720,h=112;
 let s=R(x,y,w,h,C.panel,C.line,10)+R(x,y,w,26,'#EEF2F8','none',10)+`<rect x="${x}" y="${y+14}" width="${w}" height="12" fill="#EEF2F8"/>`;
 s+=T(x+14,y+18,'Simulation Panel · Event List',12,C.ink,700)+`<circle cx="${x+w-20}" cy="${y+13}" r="5" fill="${C.green}"/>`+T(x+w-32,y+18,'Simulation ▶',11,C.muted,400,'end');
 const cx=[x+14,x+58,x+160,x+330,x+500];['Vis.','Time(sec)','Last Device','At Device','Type'].forEach((hh,k)=>s+=T(cx[k],y+44,hh,11,C.muted,700));
 const shown=EVENTS.filter(e=>t>=e[0]).slice(-3);
 shown.forEach((e,k)=>{const yy=y+64+k*20,a=out((t-e[0])/.35);s+=G(a,`<g transform="translate(${((1-a)*-14).toFixed(1)} 0)">`+(k===shown.length-1?R(x+6,yy-14,w-12,19,'#EAF0FE','none',4):'')+`<rect x="${cx[0]+2}" y="${yy-11}" width="16" height="11" rx="1.5" fill="${e[4]}"/>`+M(cx[1],yy,(e[0]-9.4).toFixed(3),11.5,C.ink)+M(cx[2],yy,e[1],11.5,C.ink)+M(cx[3],yy,e[2],11.5,C.ink)+M(cx[4],yy,e[3],11.5,e[4],700)+'</g>')});
 return G(o,s);
}

function storyPackets(t){
 return pdu(['bot','sw','tap'],t,8.6,1.2,C.red,{s:1.25})+pdu(['tap','ids'],t,16.6,1.0,C.blue,{s:1.25})+pdu(['ids','rag'],t,24.6,1.0,C.teal,{s:1.25})
  +pdu(['rag','llm'],t,31.6,1.0,C.violet,{s:1.25})+pdu(['llm','fw'],t,38.4,1.2,C.amber,{s:1.25});
}
function deviceStatus(t){
 const ring=(n,c,a,b)=>{const o=win(t,a,b,.3);if(o<=0)return '';const [x,y]=P(n),pulse=(t*1.6)%1;
  return G(o,`<circle cx="${x}" cy="${y}" r="${(46+pulse*14).toFixed(1)}" fill="none" stroke="${c}" stroke-width="2" opacity="${(1-pulse).toFixed(2)}"/><circle cx="${x}" cy="${y}" r="44" fill="${c}" fill-opacity=".07" stroke="${c}" stroke-width="2"/>`)};
 let s=ring('tap',C.blue,9.6,16.8)+ring('ids',C.teal,17.6,24.8)+ring('rag',C.violet,25.6,31.8)+ring('llm',C.amber,32.6,38.8)+ring('fw',C.orange,39.6,49.4);
 const [x,y]=P('fw'),on=win(t,41.4,46.2,.3),off=win(t,46.2,49.4,.3);
 if(on>0)s+=G(on,R(x-46,y-80,92,24,C.red,'none',12)+T(x,y-63,'ACL 套用中',12,'#fff',700,'middle'));
 if(off>0)s+=G(off,R(x-46,y-80,92,24,C.green,'none',12)+T(x,y-63,'已回復',12,'#fff',700,'middle'));
 return s;
}

function titleCard(t,closing){
 const a=k=>out((t-k)/.6);let s='';
 if(!closing){
  s+=G(a(.1),T(110,170,'2026 第 31 屆大專校院資訊應用服務創新競賽　·　資安技術組',15,C.blue,700));
  TITLE_ZH.forEach((l,k)=>{const p=spring((t-.3-k*.25)/.8);s+=G(clamp(p*1.2),`<g transform="translate(0 ${((1-Math.min(p,1))*30).toFixed(1)})">${T(110,260+k*68,l,48,k===2?C.blue:C.ink,700)}</g>`)});
  s+=`<rect x="110" y="452" width="${(140*out((t-1.2)/.8)).toFixed(1)}" height="5" rx="2.5" fill="${C.blue}"/>`;
  const cut=TITLE_EN.lastIndexOf(' ',86);s+=G(a(1.5),T(110,496,TITLE_EN.slice(0,cut),16,C.muted)+T(110,520,TITLE_EN.slice(cut+1),16,C.muted));
 }else{
  s+=G(a(.1),T(110,190,'CONCLUSION',15,C.blue,700,'start',' letter-spacing="2"'));
  ['偵測有依據','稽核有證據','處置可回復'].forEach((l,k)=>{const p=spring((t-.3-k*.3)/.8);s+=G(clamp(p*1.2),`<g transform="translate(${110+k*360} ${(300+(1-Math.min(p,1))*30).toFixed(1)})">${T(0,0,l,46,[C.blue,C.violet,C.teal][k],700)}</g>`)});
  [['98.08%','17 類偵測 Accuracy'],['96.76%','任務檢索 Top-5'],['95.83%','改良 RAG 錯誤攔截率'],['6 / 6','隔離情境完整回復']].forEach(([v,l],k)=>{s+=G(a(1.2+k*.2),R(110+k*270,380,250,104,C.panel,C.line,14)+T(130+k*270,436,v,36,[C.blue,C.violet,C.violet,C.teal][k],700)+T(130+k*270,464,l,14,C.muted))});
  s+=G(a(2.2),T(110,560,'融合新型內容相依時序方向模型入侵偵測與任務導向檢索增強稽核之 AI 資安框架',18,C.ink,700));
 }
 return s;
}

export function frameSvg(time){
 const t=clamp(time,0,duration);
 let s=`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="Microsoft JhengHei, Noto Sans TC, Segoe UI, Arial, sans-serif">`;
 s+=`<defs><pattern id="g" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="${C.grid}"/></pattern></defs><rect width="1280" height="720" fill="${C.bg}"/><rect width="1280" height="720" fill="url(#g)"/>`;
 const titleO=1-out((t-3.4)/.6),closeO=out((t-56)/.6),work=Math.min(1-titleO,1-closeO);
 if(work>0){
  const world=links(t)+ambient(t)+storyPackets(t)+deviceStatus(t)+Object.values(D).map(d=>icon(d,t)).join('');
  s+=G(work,`<g transform="${camera(t)}">${world}</g>`);
  const i=chapterAt(t),ch=chapters[i],ci=out((t-ch.at)/.5);
  s+=G(work,R(0,0,1280,64,C.panel,'none',0)+L(0,64,1280,64,C.line,1)+T(28,40,'AI 資安框架',16,C.ink,700)+T(132,40,'· Packet Tracer 模擬模式',14,C.muted)
   +`<g transform="translate(${((1-ci)*16).toFixed(1)} 0)" opacity="${ci.toFixed(3)}">${T(1252,40,`${String(Math.max(1,i)).padStart(2,'0')} / 07　${ch.title}`,16,C.blue,700,'end')}</g>`);
  s+=G(work,simPanel(t))+stage1(t)+stage2(t)+stage3(t)+stage4(t)+stage5(t)+stage6(t);
  s+=G(work,`<rect x="0" y="714" width="${(1280*t/duration).toFixed(1)}" height="6" fill="${C.blue}"/>`);
 }
 if(titleO>0)s+=G(titleO,`<rect width="1280" height="720" fill="${C.bg}"/>`+titleCard(t,false));
 if(closeO>0)s+=G(closeO,`<rect width="1280" height="720" fill="${C.bg}"/>`+titleCard(t-56,true));
 return s+'</svg>';
}
