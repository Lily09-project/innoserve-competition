// Pure time -> SVG scene. Shared by the browser player and offline MP4 renderer.
// Every figure on screen comes from results/ (measured runs); per-event values are not invented.
export const TITLE_ZH=['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架'];
export const TITLE_EN='An AI Security Framework Integrating Novel Content Dependent Temporal Directional Intrusion Detection and Task Oriented Retrieval Augmented';
const BASE=96;
export const SPEED=1.6; // 96 s storyboard played at 1.6x -> 60 s for the 5-minute finals slot
export const duration=BASE/SPEED;
const BASE_CHAPTERS=[
 {at:0,title:'作品名稱',card:'open'},
 {at:6,title:'資料輸入與前處理',stage:0,caption:'原始流量整理為雙向連線並移除 IP 與 Port，轉成內容位元組、時間差與方向三種模型輸入。'},
 {at:20,title:'內容相依時序方向偵測',stage:1,caption:'CTBM 與 PBCNN 雙分支判讀，經溫度校準與 OOF Gate 融合，輸出固定 17 類正式機率。'},
 {at:36,title:'任務導向證據檢索',stage:2,caption:'512 維表徵串接 17 維機率形成任務向量，於訓練案例庫以餘弦相似度取回前五筆證據。'},
 {at:50,title:'AI 證據稽核',stage:3,caption:'本機大語言模型依證據回傳支持、複核或不確定，以結構化 JSON 留下理由，不覆寫正式分類。'},
 {at:63,title:'受控處置與回復驗證',stage:4,caption:'Policy Guard 通過後套用白名單規則並讀回，30 秒到期自動撤銷，背景服務全程保持連線。'},
 {at:80,title:'事件輸出與整體成效',stage:5,caption:'同一事件識別碼串起判定、證據、稽核與處置回條，完整紀錄可匯出供稽核追溯。'},
 {at:90,title:'結語',card:'close'}
];
const C={bg:'#F5F8FC',panel:'#FFFFFF',soft:'#F1F5FB',ink:'#0B1B33',muted:'#5B6B82',faint:'#94A3B8',line:'#DCE3EE',
 s:['#1D4ED8','#0F766E','#6D28D9','#B45309','#C2410C','#0B1B33'],green:'#0F766E',red:'#B42318',amber:'#B45309',blue:'#1D4ED8'};
const STAGES=['資料輸入','17 類偵測','Top-5 檢索','AI 稽核','受控處置','事件輸出'];
const xesc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const ease=v=>{v=clamp(v);return v<.5?2*v*v:1-Math.pow(-2*v+2,2)/2};
const txt=(x,y,s,size=18,fill=C.ink,weight=400,anchor='start',extra='')=>`<text x="${x}" y="${y}" font-size="${size}" fill="${fill}" font-weight="${weight}" text-anchor="${anchor}"${extra}>${xesc(s)}</text>`;
const mono=(x,y,s,size=14,fill=C.ink,weight=400,anchor='start')=>txt(x,y,s,size,fill,weight,anchor,' font-family="Cascadia Mono, Consolas, monospace"');
const rect=(x,y,w,h,fill=C.panel,stroke=C.line,r=12,extra='')=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}"${extra}/>`;
const line=(x1,y1,x2,y2,color=C.line,w=2,dash='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${w}" stroke-linecap="round"${dash?` stroke-dasharray="${dash}"`:''}/>`;
const fade=(o,inner)=>`<g opacity="${clamp(o).toFixed(3)}">${inner}</g>`;
const arrowR=(x,y,c)=>`<path d="M${x-14} ${y}H${x}M${x-7} ${y-7}L${x} ${y}L${x-7} ${y+7}" stroke="${c}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
const chip=(x,y,s,c,w=null)=>{const ww=w??(s.length*13+26);return rect(x,y,ww,28,c+'14',c,14)+txt(x+ww/2,y+19,s,13,c,700,'middle')};
// Deterministic pseudo-random for decorative textures (heatmap/vector cells), never shown as values.
const hash=n=>{const x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x)};

export const chapters=BASE_CHAPTERS.map(c=>({...c,at:c.at/SPEED}));
const baseAt=t=>{let i=BASE_CHAPTERS.length-1;while(i>0&&t<BASE_CHAPTERS[i].at)i--;return i};
export function chapterAt(t){return baseAt(t*SPEED)}

function panel(x,y,w,h,label,c,o=1){return fade(o,rect(x,y,w,h)+rect(x,y,w,36,c+'12','none',12)+`<rect x="${x}" y="${y+24}" width="${w}" height="12" fill="${c}12"/>`+line(x,y+36,x+w,y+36,C.line,1)+txt(x+16,y+24,label,14,c,700))}
function tracker(stage){
 let s='';const x0=150,w=980,gap=w/5;
 s+=line(x0,92,x0+w,92,C.line,3);if(stage>0)s+=line(x0,92,x0+gap*Math.min(stage,5),92,C.blue,3);
 STAGES.forEach((l,k)=>{const cx=x0+gap*k,on=k<=stage,cur=k===stage;
  s+=`<circle cx="${cx}" cy="92" r="${cur?10:7}" fill="${on?C.s[k]:C.panel}" stroke="${on?C.s[k]:C.faint}" stroke-width="2.5"/>`;
  if(cur)s+=`<circle cx="${cx}" cy="92" r="16" fill="none" stroke="${C.s[k]}" stroke-opacity=".25" stroke-width="5"/>`;
  s+=txt(cx,124,l,14,cur?C.s[k]:on?C.ink:C.faint,cur?700:400,'middle')});
 return s;
}

function titleCard(local,closing){
 const a=k=>ease((local-k)/1.0);let s='';
 s+=`<rect x="0" y="0" width="1280" height="8" fill="${C.blue}"/>`;
 s+=fade(a(.1),txt(110,150,closing?'CONCLUSION':'2026 第 31 屆大專校院資訊應用服務創新競賽　·　資安技術組',15,C.blue,700,'start',' letter-spacing="1.5"'));
 if(closing){
  s+=fade(a(.3),txt(110,250,'偵測有依據　稽核有證據',54,C.ink,700)+txt(110,330,'處置可回復',54,C.blue,700));
  s+=fade(a(1.0),txt(110,392,'同一事件識別碼，串起從原始流量到回復驗證的完整證據鏈。',22,C.muted));
  const kp=[['98.08%','17 類偵測 Accuracy'],['96.76%','任務檢索 Top-5'],['95.83%','改良 RAG 錯誤攔截率'],['6 / 6','隔離情境回復驗證']];
  kp.forEach(([v,l],k)=>{s+=fade(a(1.4+k*.25),rect(110+k*270,450,250,110,C.panel,C.line,14)+txt(132+k*270,507,v,38,C.s[k===3?1:k===2?2:0],700)+txt(132+k*270,538,l,15,C.muted))});
 }else{
  TITLE_ZH.forEach((l,k)=>{const o=a(.3+k*.3);s+=fade(o,`<g transform="translate(0 ${(1-o)*12})">${txt(110,240+k*70,l,50,k===2?C.blue:C.ink,700)}</g>`)});
  s+=fade(a(.8),`<rect x="110" y="448" width="${120*a(1.2)}" height="4" rx="2" fill="${C.blue}"/>`);
  const cut=TITLE_EN.lastIndexOf(' ',86);
  s+=fade(a(1.4),txt(110,494,TITLE_EN.slice(0,cut),17,C.muted)+txt(110,520,TITLE_EN.slice(cut+1),17,C.muted));
  s+=fade(a(2.0),STAGES.map((l,k)=>chip(110+k*178,590,l,C.s[k],160)).join(''));
 }
 return s;
}

/* ---------- chapter bodies: each is INPUT | PROCESS | OUTPUT ---------- */
const COL=[[40,160,330,440],[400,160,480,440],[910,160,330,440]];
function frame3(i,local,c){
 const o=k=>ease((local-k)/0.8);
 return panel(...COL[0],'輸入 INPUT',c,o(0))+panel(...COL[1],'處理 PROCESS',c,o(.4))+panel(...COL[2],'輸出 OUTPUT',c,o(.8))+fade(o(.6),arrowR(392,380,c))+fade(o(1),arrowR(902,380,c));
}

function ch1(local){ // data input
 const c=C.s[0];let s=frame3(1,local,c);const [ix,iy]=COL[0],[px,py]=COL[1],[ox,oy]=COL[2];
 s+=txt(ix+16,iy+66,'原始封包（PCAP／鏡像埠）',15,C.ink,700);
 s+=mono(ix+16,iy+92,'封包  方向  內容 bytes（已去識別化）',12,C.muted);
 const n=Math.min(9,Math.floor(local*2.2));
 for(let k=0;k<n;k++){const y=iy+118+k*30,up=[1,0,1,1,0,1,0,0,1][k],w=40+hash(k+9)*150;
  s+=rect(ix+12,y-19,306,26,k%2?C.panel:C.soft,'none',5)+mono(ix+20,y,`#${String(k+1).padStart(2,'0')}`,12,C.muted)+mono(ix+78,y,up?'→':'←',14,up?c:C.green,700)+`<rect x="${ix+112}" y="${y-11}" width="${w.toFixed(0)}" height="10" rx="3" fill="${up?c:C.green}" fill-opacity=".28"/>`}
 s+=txt(ix+16,iy+420,'來源：CICIDS2017 · CSE-CIC-IDS2018',12,C.muted);
 const p=ease((local-2)/3);
 s+=fade(p,txt(px+20,py+70,'① 雙向 Flow 組裝',17,C.ink,700)+txt(px+20,py+96,'5-tuple 分組、依時間排序、標記傳輸方向',13,C.muted));
 s+=fade(ease((local-3.5)/2),txt(px+20,py+150,'② 去識別化',17,C.ink,700)+rect(px+20,py+164,440,40,C.soft,'none',8)+mono(px+34,py+190,'IP 192.168.●.●  Port ●●●●  →  已移除',14,c,700));
 s+=fade(ease((local-5)/2),txt(px+20,py+252,'③ 三種模型輸入',17,C.ink,700)+[['內容 bytes','前 20 封包位元組'],['時間差 Δt','封包間隔序列'],['傳輸方向','用戶端↔服務端']].map(([a,b],k)=>rect(px+20+k*150,py+268,140,92,C.panel,c,10)+txt(px+90+k*150,py+306,a,15,c,700,'middle')+txt(px+90+k*150,py+334,b,12,C.muted,400,'middle')).join(''));
 s+=fade(ease((local-5)/2),txt(px+20,py+408,'兩個資料集輸出相同事件格式，方便跨資料集比對',13,C.muted));
 const q=ease((local-7)/3);
 s+=fade(q,txt(ox+16,oy+66,'模型輸入張量',15,C.ink,700)+txt(ox+16,oy+88,'20 封包 × bytes',12,C.muted));
 for(let r=0;r<10;r++)for(let k=0;k<16;k++){const v=hash(r*31+k)**1.6;s+=fade(q*clamp((local-7-r*.15)/.5),`<rect x="${ox+16+k*18.5}" y="${oy+102+r*15}" width="17" height="14" fill="${c}" fill-opacity="${(0.08+v*.85).toFixed(2)}"/>`)}
 s+=fade(ease((local-9)/2),txt(ox+16,oy+290,'Δt × 方向序列',15,C.ink,700)+Array.from({length:20},(_,k)=>{const up=hash(k+50)>.45,h=10+hash(k+70)*36;return `<rect x="${ox+18+k*15}" y="${up?oy+352-h:oy+352}" width="10" height="${h}" fill="${up?c:'#93C5FD'}"/>`}).join('')+line(ox+16,oy+352,ox+316,oy+352,C.muted,1));
 s+=fade(ease((local-10)/2),txt(ox+16,oy+425,'→ 送入雙分支偵測模型',13,c,700));
 return s;
}

function ch2(local){ // detection
 const c=C.s[1];let s=frame3(2,local,c);const [ix,iy]=COL[0],[px,py]=COL[1],[ox,oy]=COL[2];
 s+=txt(ix+16,iy+66,'模型輸入張量',15,C.ink,700);
 for(let r=0;r<8;r++)for(let k=0;k<16;k++){const v=hash(r*31+k)**1.6;s+=`<rect x="${ix+16+k*18.5}" y="${iy+84+r*15}" width="17" height="14" fill="${C.s[0]}" fill-opacity="${(0.08+v*.85).toFixed(2)}"/>`}
 s+=txt(ix+16,iy+240,'內容 bytes ＋ Δt ＋ 方向',13,C.muted);
 s+=txt(ix+16,iy+300,'18,998 筆封存測試',22,C.ink,700)+txt(ix+16,iy+326,'CICIDS2017 ＋ CSE-CIC-IDS2018',13,C.muted);
 const step=k=>ease((local-1-k*2.2)/1.2);
 const blocks=[['CTBM','內容・時間差・方向 → Blue Heat',20,70],['PBCNN','短窗位元組卷積特徵',250,70],['溫度校準','降低過度自信',20,190],['OOF Gate','59 項證據 ＋ class-F1 guard',250,190]];
 blocks.forEach(([a,b,dx,dy],k)=>{const o=step(k);s+=fade(.25+.75*o,rect(px+dx,py+dy,210,92,o>.95?c+'10':C.panel,o>.5?c:C.line,12)+txt(px+dx+16,py+dy+36,a,18,o>.5?c:C.muted,700)+txt(px+dx+16,py+dy+66,b,12.5,C.muted))});
 s+=fade(step(1),line(px+125,py+164,px+125,py+188,c,2)+line(px+355,py+164,px+355,py+188,c,2));
 s+=fade(step(3),rect(px+20,py+310,440,108,C.soft,'none',10)+txt(px+36,py+342,'雙分支互補',15,C.ink,700)+txt(px+36,py+368,'長程脈絡（CTBM）＋ 短窗位元組（PBCNN）',13,C.muted)+txt(px+36,py+394,'保留 512 維表徵，交給下游檢索',13,c,700));
 const q=ease((local-9)/3);
 s+=fade(q,txt(ox+16,oy+66,'17 類正式機率',15,C.ink,700));
 for(let k=0;k<17;k++){const h=k===13?150:10+hash(k+3)*18;s+=fade(q,`<rect x="${ox+20+k*17.5}" y="${oy+250-h*q}" width="12" height="${h*q}" rx="2" fill="${k===13?c:'#A7DCD3'}"/>`)}
 s+=fade(q,line(ox+16,oy+250,ox+318,oy+250,C.muted,1)+txt(ox+20+13*17.5+6,oy+90,'Bot',13,c,700,'middle')+txt(ox+16,oy+272,'0 BENIGN',11,C.faint)+txt(ox+318,oy+272,'16 Heartbleed',11,C.faint,400,'end'));
 s+=fade(ease((local-11)/2),rect(ox+16,oy+296,298,128,C.soft,'none',10)+txt(ox+30,oy+330,'整體 Accuracy',13,C.muted)+txt(ox+300,oy+330,'98.08%',20,c,700,'end')+txt(ox+30,oy+366,'Macro-F1',13,C.muted)+txt(ox+300,oy+366,'93.05%',20,c,700,'end')+txt(ox+30,oy+402,'Bot 類 Recall',13,C.muted)+txt(ox+300,oy+402,'98.40%',20,c,700,'end'));
 return s;
}

function ch3(local){ // retrieval
 const c=C.s[2];let s=frame3(3,local,c);const [ix,iy]=COL[0],[px,py]=COL[1],[ox,oy]=COL[2];
 s+=txt(ix+16,iy+66,'529 維任務向量',15,C.ink,700);
 for(let k=0;k<26;k++)s+=`<rect x="${ix+16+k*10.6}" y="${iy+84}" width="9" height="46" fill="${c}" fill-opacity="${(.2+hash(k)*.7).toFixed(2)}"/>`;
 for(let k=0;k<4;k++)s+=`<rect x="${ix+16+(26+k)*10.6}" y="${iy+84}" width="9" height="46" fill="#EA580C" fill-opacity="${(.3+hash(k+40)*.6).toFixed(2)}"/>`;
 s+=txt(ix+16,iy+152,'512 維 CTBM 表徵',12,c,700)+txt(ix+314,iy+152,'17 維機率',12,'#EA580C',700,'end');
 s+=rect(ix+16,iy+180,298,72,C.soft,'none',10)+txt(ix+30,iy+210,'L2 正規化',15,C.ink,700)+txt(ix+30,iy+236,'表徵與分類結果一起決定「找什麼」',12.5,C.muted);
 s+=txt(ix+16,iy+300,'表徵版本',13,C.muted)+mono(ix+16,iy+324,'ctbm512_plus_frozen_',12,C.ink)+mono(ix+16,iy+344,'gate17_concat_l2.v1',12,C.ink);
 // process: case bank scatter with query and nearest neighbours
 const p=ease((local-1.5)/2),cx=px+240,cy=py+215;
 s+=fade(p,txt(px+20,py+66,'訓練案例庫（train-only）· 1,550 筆',15,C.ink,700));
 for(let k=0;k<120;k++){const a=hash(k)*6.283,r=40+hash(k+200)*150,x=cx+Math.cos(a)*r*1.2,y=cy+Math.sin(a)*r*.75;s+=fade(p*clamp((local-1.5-k*.01)/.4),`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4" fill="${C.faint}" fill-opacity=".45"/>`)}
 const nn=[[-30,-18],[24,-26],[34,16],[-18,30],[-44,8]];const q=ease((local-4)/1.5);
 nn.forEach(([dx,dy],k)=>{const o=clamp((local-4.5-k*.5)/.5);s+=fade(o,line(cx,cy,cx+dx*1.6,cy+dy*1.6,c,1.5,'4 4')+`<circle cx="${cx+dx*1.6}" cy="${cy+dy*1.6}" r="7" fill="${c}"/>`)});
 s+=fade(q,`<circle cx="${cx}" cy="${cy}" r="11" fill="#EA580C" stroke="#fff" stroke-width="3"/>`+txt(cx+18,cy-14,'查詢事件',13,'#EA580C',700));
 s+=fade(ease((local-6)/1.5),rect(px+20,py+370,440,50,C.soft,'none',10)+txt(px+36,py+401,'餘弦相似度排序　·　檢索中位數 1.01 ms（CUDA）',14,C.ink,700));
 const r=ease((local-7)/2);
 s+=fade(r,txt(ox+16,oy+66,'Top-5 相似案例證據',15,C.ink,700)+mono(ox+16,oy+92,'排名 案例來源      相似度',12,C.muted));
 for(let k=0;k<5;k++){const o=clamp((local-7.5-k*.35)/.5),y=oy+108+k*42,w=190-k*18;s+=fade(o,rect(ox+16,y,298,34,C.soft,'none',6)+mono(ox+28,y+22,`#${k+1}`,13,c,700)+txt(ox+64,y+22,'train',12,C.muted)+`<rect x="${ox+110}" y="${y+12}" width="${w*o}" height="10" rx="5" fill="${c}" fill-opacity="${1-k*.12}"/>`)}
 s+=fade(ease((local-10)/2),rect(ox+16,oy+330,298,96,C.soft,'none',10)+txt(ox+30,oy+362,'Top-5 命中率',13,C.muted)+txt(ox+300,oy+362,'96.76%',20,c,700,'end')+txt(ox+30,oy+400,'MRR@5',13,C.muted)+txt(ox+300,oy+400,'94.25%',20,c,700,'end'));
 return s;
}

function ch4(local){ // audit
 const c=C.s[3];let s=frame3(4,local,c);const [ix,iy]=COL[0],[px,py]=COL[1],[ox,oy]=COL[2];
 s+=txt(ix+16,iy+66,'稽核提示內容',15,C.ink,700);
 [['正式類別與信心','偵測輸出'],['CTBM／PBCNN 分支觀察','是否一致'],['Top-5 標籤與相似度','檢索證據'],['測試答案','不進入提示']].forEach(([a,b],k)=>{const o=clamp((local-.5-k*.5)/.5),y=iy+84+k*70;s+=fade(o,rect(ix+16,y,298,58,k===3?'#FEF2F2':C.soft,'none',10)+txt(ix+30,y+26,a,14,k===3?C.red:C.ink,700)+txt(ix+30,y+46,b,12,C.muted))});
 s+=txt(ix+16,iy+410,'外部 API 呼叫：0 次（本機推論）',13,C.green,700);
 const p=ease((local-2.5)/1.5);
 s+=fade(p,rect(px+170,py+70,140,110,c+'10',c,18)+`<circle cx="${px+215}" cy="${py+120}" r="9" fill="${c}"/><circle cx="${px+265}" cy="${py+120}" r="9" fill="${c}"/>`+line(px+215,py+152,px+265,py+152,c,3)+line(px+240,py+70,px+240,py+52,c,3)+`<circle cx="${px+240}" cy="${py+48}" r="6" fill="${c}"/>`);
 s+=fade(p,txt(px+240,py+210,'Meta-Llama-3-8B-Instruct',16,C.ink,700,'middle')+txt(px+240,py+234,'本機 GPU 推論 · 固定提示雜湊',13,C.muted,400,'middle'));
 [['支持 support',C.green,'415'],['複核 review',C.amber,'13'],['不確定 uncertain',C.amber,'35']].forEach(([a,col,n],k)=>{const o=clamp((local-4-k*.5)/.5);s+=fade(o,rect(px+40+k*140,py+270,130,64,col+'12',col,12)+txt(px+105+k*140,py+298,a,13,col,700,'middle')+txt(px+105+k*140,py+322,`${n} 筆`,13,C.muted,400,'middle'))});
 s+=fade(ease((local-6)/1),txt(px+240,py+372,'463 筆整合查詢的稽核分佈',13,C.muted,400,'middle')+txt(px+240,py+404,'只有「支持」可進入可干預處置',14,c,700,'middle'));
 const q=ease((local-6.5)/1.5);
 s+=fade(q,txt(ox+16,oy+66,'結構化稽核回覆（JSON）',15,C.ink,700)+rect(ox+16,oy+80,298,190,'#0B1B33','none',10));
 const js=['{','  "assessment": "support",','  "reason": "Top-5 證據一致",','  "classification_changed":','      false,','  "model": "Llama-3-8B"','}'];
 js.forEach((l,k)=>{s+=fade(q*clamp((local-7-k*.25)/.3),mono(ox+30,oy+108+k*24,l,12.5,k===1?'#6EE7B7':'#CFE0F7'))});
 s+=fade(ease((local-9)/1.5),rect(ox+16,oy+290,298,136,C.soft,'none',10)+txt(ox+30,oy+322,'有效 JSON',13,C.muted)+txt(ox+300,oy+322,'463 / 463',18,c,700,'end')+txt(ox+30,oy+358,'分類被改寫',13,C.muted)+txt(ox+300,oy+358,'0 筆',18,c,700,'end')+txt(ox+30,oy+394,'支持精確率',13,C.muted)+txt(ox+300,oy+394,'97.11%',18,c,700,'end'));
 return s;
}

function ch5(local){ // response, Bot case from results/framework_validation.json
 const c=C.s[4];let s=frame3(5,local,c);const [ix,iy]=COL[0],[px,py]=COL[1],[ox,oy]=COL[2];
 s+=txt(ix+16,iy+66,'通過稽核的事件',15,C.ink,700);
 s+=rect(ix+16,iy+82,298,150,C.soft,'none',10)+txt(ix+30,iy+112,'類別',13,C.muted)+txt(ix+300,iy+112,'Bot',15,C.ink,700,'end')+txt(ix+30,iy+146,'稽核',13,C.muted)+txt(ix+300,iy+146,'support',15,C.green,700,'end')+txt(ix+30,iy+180,'策略',13,C.muted)+mono(ix+300,iy+180,'block_c2_destination',12,C.ink,700,'end')+txt(ix+30,iy+214,'範圍',13,C.muted)+txt(ix+300,iy+214,'隔離網路 · Mininet',13,C.ink,700,'end');
 s+=txt(ix+16,iy+280,'處置門檻',15,C.ink,700);
 ['稽核結果為「支持」','分類信心 ≥ 0.80','Top-5 同類 ≥ 4 筆'].forEach((l,k)=>{const o=clamp((local-1-k*.5)/.4);s+=fade(o,`<circle cx="${ix+30}" cy="${iy+306+k*34}" r="10" fill="${C.green}"/><path d="M${ix+25} ${iy+306+k*34}l4 4 7-8" stroke="#fff" stroke-width="2.5" fill="none"/>`+txt(ix+50,iy+311+k*34,l,14,C.ink))});
 // process timeline
 const steps=[['Policy Guard','白名單・範圍・有效期',2.5],['套用規則','iptables · 1 條',4.5],['讀回驗證','規則與設定一致',6.5],['到期撤銷','TTL 30 秒',8.5],['回復驗證','連線恢復',11.5]];
 steps.forEach(([a,b,at],k)=>{const o=ease((local-at)/0.8),y=py+66+k*72;s+=fade(.25+.75*o,`<circle cx="${px+40}" cy="${y+22}" r="14" fill="${o>.5?c:C.panel}" stroke="${o>.5?c:C.line}" stroke-width="2.5"/>`+txt(px+40,y+27,String(k+1),13,o>.5?'#fff':C.faint,700,'middle')+txt(px+70,y+20,a,16,o>.5?C.ink:C.muted,700)+txt(px+70,y+42,b,12.5,C.muted));if(k<4)s+=line(px+40,y+38,px+40,y+72,o>.9?c:C.line,2)});
 const ttl=clamp((local-8.5)/3);
 s+=fade(ease((local-8.5)/.5),`<circle cx="${px+390}" cy="${py+300}" r="58" fill="none" stroke="${C.line}" stroke-width="10"/><circle cx="${px+390}" cy="${py+300}" r="58" fill="none" stroke="${c}" stroke-width="10" stroke-dasharray="${(364.4*ttl).toFixed(1)} 400" transform="rotate(-90 ${px+390} ${py+300})"/>`+txt(px+390,py+298,ttl<1?'TTL':'已撤銷',ttl<1?18:16,c,700,'middle')+txt(px+390,py+322,'30 秒',13,C.muted,400,'middle'));
 // output: measured transaction success rates
 const q=ease((local-5)/1);
 s+=fade(q,txt(ox+16,oy+66,'隔離網路實測回條',15,C.ink,700)+txt(ox+16,oy+90,'交易成功率',12,C.muted));
 const bars=[['攻擊型測試交易　套用前',1,C.muted],['攻擊型測試交易　套用後',0,c],['背景服務　處置期間',1,C.green],['回復後測試交易',1,C.green]];
 bars.forEach(([l,v,col],k)=>{const o=clamp((local-5.5-k*1.4)/.6),y=oy+108+k*62;s+=fade(o,txt(ox+16,y+16,l,13,C.ink)+rect(ox+16,y+26,230,14,C.soft,'none',7)+`<rect x="${ox+16}" y="${y+26}" width="${Math.max(4,230*v*o)}" height="14" rx="7" fill="${col}"/>`+txt(ox+314,y+38,`${Math.round(v*100)}%`,15,col,700,'end'))});
 s+=fade(ease((local-12)/1),rect(ox+16,oy+366,298,60,C.green+'12',C.green,10)+txt(ox+30,oy+392,'到期撤銷實測 30.12 秒',14,C.green,700)+txt(ox+30,oy+414,'規則與連線完整回復',12.5,C.muted));
 return s;
}

function ch6(local){ // output
 const c=C.s[5];let s=frame3(6,local,c);const [ix,iy]=COL[0],[px,py]=COL[1],[ox,oy]=COL[2];
 s+=txt(ix+16,iy+66,'各階段結果',15,C.ink,700);
 [['偵測',C.s[1],'類別・信心・表徵'],['檢索',C.s[2],'Top-5・相似度'],['稽核',C.s[3],'三態・理由'],['處置',C.s[4],'規則・回條']].forEach(([a,col,b],k)=>{const y=iy+84+k*78;s+=rect(ix+16,y,298,64,C.panel,col,10)+`<rect x="${ix+16}" y="${y}" width="6" height="64" rx="3" fill="${col}"/>`+txt(ix+36,y+28,a,16,col,700)+txt(ix+36,y+50,b,12.5,C.muted)});
 const p=ease((local-1)/1);
 s+=fade(p,txt(px+20,py+66,'事件鏈與雜湊綁定',15,C.ink,700));
 ['DetectionEvent','Evidence Top-5','Judge JSON','Policy Receipt','Network Receipt'].forEach((l,k)=>{const o=clamp((local-1.5-k*.4)/.4),y=py+86+k*62;s+=fade(o,rect(px+40,y,400,46,C.soft,'none',10)+mono(px+60,y+29,l,14,C.ink,700)+mono(px+420,y+29,'sha256 ✓',12,C.green,700,'end'));if(k<4)s+=fade(o,line(px+240,y+46,px+240,y+62,C.muted,2))});
 s+=fade(ease((local-4)/1),txt(px+240,py+418,'事件 ID ＋ 執行 ID 綁定 · 過期批次自動拒絕',13,C.muted,400,'middle'));
 const q=ease((local-4)/1);
 s+=fade(q,txt(ox+16,oy+66,'整合驗證成果',15,C.ink,700));
 [['17 / 17','類別即時重跑偵測＋稽核'],['6 / 6','隔離情境背景服務保留'],['6 / 6','隔離情境完整回復'],['0','分類被 AI 改寫']].forEach(([v,l],k)=>{const o=clamp((local-4.5-k*.4)/.4),y=oy+84+k*84;s+=fade(o,rect(ox+16,y,298,70,C.soft,'none',10)+txt(ox+32,y+44,v,28,C.s[k%2?1:0],700)+txt(ox+140,y+42,l,13,C.ink))});
 return s;
}

export function frameSvg(time){
 const t=clamp(time*SPEED,0,BASE),i=baseAt(t),ch=BASE_CHAPTERS[i],local=t-ch.at,next=BASE_CHAPTERS[i+1]?.at??BASE;
 const out=clamp((next-t)/0.45),inn=clamp(local/0.45),o=Math.min(out,inn);
 let s=`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="Microsoft JhengHei, Noto Sans TC, Segoe UI, Arial, sans-serif"><rect width="1280" height="720" fill="${C.bg}"/>`;
 if(ch.card){s+=fade(i===0?out:inn,titleCard(local,ch.card==='close'))+`<rect x="0" y="714" width="${1280*(t/BASE)}" height="6" fill="${C.blue}"/></svg>`;return s}
 const c=C.s[ch.stage];
 s+=`<rect x="0" y="0" width="1280" height="6" fill="${c}"/>`;
 s+=txt(40,46,'AI 資安框架',15,C.ink,700)+txt(132,46,'· 端到端事件處理流程',15,C.muted)+txt(1240,46,`${String(ch.stage+1).padStart(2,'0')} / 06　${ch.title}`,15,c,700,'end');
 s+=tracker(ch.stage);
 s+=fade(o,[ch1,ch2,ch3,ch4,ch5,ch6][ch.stage](local));
 s+=fade(o,rect(40,620,1200,64,C.panel,C.line,12)+`<rect x="40" y="620" width="6" height="64" rx="3" fill="${c}"/>`+txt(640,659,ch.caption,18,C.ink,500,'middle'));
 s+=`<rect x="0" y="714" width="${1280*(t/BASE)}" height="6" fill="${c}"/></svg>`;return s;
}
