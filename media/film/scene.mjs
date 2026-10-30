// Deterministic promo-style method film. Recorded aggregate data; topology, tiles and cards illustrate the method.
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
// Night canvas shared with the deck cover so slide 1 -> 2 reads as one scene.
const B=palette.blue,G=palette.gold,T=palette.teal,N=palette.navy,FONT=typography.latin+', '+typography.cjk;
const PANEL=palette.night_panel,EDGE=palette.night_line,FG=palette.white,SUB=palette.on_dark_muted,FLOW=palette.cyan;
const ON_DARK={white:'navy',blue:'cyan',gray:'night_line',blue_tint:'night_panel',line:'night_line'};
const resolveColors=source=>source.replace(/#[0-9a-fA-F]{6}\b/g,hex=>palette[palette.legacy_roles[hex.slice(1).toUpperCase()]]||hex);
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
// Motion curves; rnd is a fixed hash so every frame is reproducible.
const clamp=v=>Math.max(0,Math.min(1,v));
const ease=v=>1-Math.pow(1-clamp(v),3);
const inout=v=>{v=clamp(v);return v<.5?4*v*v*v:1-Math.pow(2-2*v,3)/2;};
const back=v=>{v=clamp(v);return 1+2.70158*Math.pow(v-1,3)+1.70158*Math.pow(v-1,2);};
const rnd=k=>{const x=Math.sin(k*127.1+311.7)*43758.5453;return x-Math.floor(x);};
const f=v=>Math.round(v*100)/100;
const tx=(x,y,s,z=24,c=FG,w=400,anchor='start',extra='')=>{
 const runs=String(s).split(cjkRuns).filter(Boolean).map(part=>`<tspan font-family="${isCjk.test(part)?typography.cjk:typography.latin}">${esc(part)}</tspan>`).join('');
 return `<text x="${f(x)}" y="${f(y)}" text-anchor="${anchor}" font-size="${z}" fill="${c}" font-weight="${w}"${extra}>${runs}</text>`;
};
const box=(x,y,w,h,c,r=10,extra='')=>`<rect x="${f(x)}" y="${f(y)}" width="${f(Math.max(0,w))}" height="${f(Math.max(0,h))}" rx="${r}" fill="${c}"${extra}/>`;
const frame=(x,y,w,h,c,r=10,width=1.5)=>`<rect x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" rx="${r}" fill="none" stroke="${c}" stroke-width="${width}"/>`;
const seg=(x,y,a,b,c=EDGE,w=3,extra='')=>`<path d="M${f(x)} ${f(y)}L${f(a)} ${f(b)}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round"${extra}/>`;
const grp=(body,{x=0,y=0,s=1,o=1,cx=0,cy=0}={})=>`<g opacity="${f(clamp(o))}" transform="translate(${f(x+cx)} ${f(y+cy)}) scale(${s.toFixed(4)}) translate(${-cx} ${-cy})">${body}</g>`;
const pop=(body,cx,cy,v)=>grp(body,{s:back(v),o:v*3,cx,cy});
const flatIcon=(name,x,y,size,roles=ON_DARK)=>`<g transform="translate(${f(x)} ${f(y)}) scale(${size/64})">${icons[name].replace(/\{\{(\w+)\}\}/g,(_,key)=>palette[roles[key]||key])}</g>`;
const emblem=(x,y,size)=>flatIcon('framework',x,y,size,{white:'navy',blue_tint:'night_panel',line:'night_line',blue:'cyan',gray:'night_line'});
const chip=(cx,cy,w,h,label,z,fill,color=FG)=>box(cx-w/2,cy-h/2,w,h,fill,h/2)+tx(cx,cy+z*.36,label,z,color,700,'middle');
function arc(cx,cy,r1,r2,a0,a1){
 const p=(r,a)=>`${f(cx+r*Math.cos(a))} ${f(cy+r*Math.sin(a))}`;
 return `M${p(r2,a0)}A${r2} ${r2} 0 0 1 ${p(r2,a1)}L${p(r1,a1)}A${r1} ${r1} 0 0 0 ${p(r1,a0)}Z`;
}
function headline(lines,local,x,y,size){
 return lines.map(([text,color],k)=>{const v=ease((local-.1-k*.16)/.5);return `<g opacity="${f(v)}" transform="translate(${f((1-v)*-48)} 0)">${tx(x,y+k*size*1.18,text,size,color,700)}</g>`;}).join('')+box(x,y+(lines.length-1)*size*1.18+22,96*ease((local-.4)/.5),5,G,2);
}
const tag=(i,local)=>tx(64,62,'0'+i,20,FLOW,700)+box(96,55,48*ease(local/.5),2,FLOW,1)+tx(156,62,chapters[i].title,19,SUB,700);
// Oversized outline word drifting behind each chapter.
const ghost=(word,t,y=430)=>`<text x="${f(1240-t*6%40)}" y="${y}" text-anchor="end" font-size="190" fill="none" stroke="${EDGE}" stroke-width="2" font-weight="700" font-family="${typography.latin}" opacity=".55">${word}</text>`;
// Packets: glowing envelopes with a fading trail along a polyline.
function along(points,u){
 const lengths=points.slice(1).map((p,k)=>Math.hypot(p[0]-points[k][0],p[1]-points[k][1]));
 let d=clamp(u)*lengths.reduce((a,b)=>a+b,0);
 for(let k=0;k<lengths.length;k++){
  if(d<=lengths[k]||k===lengths.length-1){const r=lengths[k]?Math.min(1,d/lengths[k]):0;return [points[k][0]+(points[k+1][0]-points[k][0])*r,points[k][1]+(points[k+1][1]-points[k][1])*r];}
  d-=lengths[k];
 }
}
function envelope(x,y,c,size=1){
 const w=22*size,h=15*size;
 return box(x-w/2,y-h/2,w,h,c,2.5)+`<path d="M${f(x-w/2)} ${f(y-h/2)}L${f(x)} ${f(y+h*.12)}L${f(x+w/2)} ${f(y-h/2)}" fill="none" stroke="${N}" stroke-width="1.6" stroke-linejoin="round"/>`;
}
function packet(points,u,c,size=1,trail=.03){
 let s='';
 for(let k=6;k>=1;k--){const p=along(points,u-k*trail);if(u-k*trail>0)s+=`<circle cx="${f(p[0])}" cy="${f(p[1])}" r="${f(size*(5.5-k*.6))}" fill="${c}" opacity="${f(.55-k*.08)}"/>`;}
 const p=along(points,u);
 return s+`<g filter="url(#glow)">${envelope(p[0],p[1],c,size)}</g>`;
}
function burst(x,y,q,c=G){
 let s=`<circle cx="${f(x)}" cy="${f(y)}" r="${f(10+50*ease(q))}" fill="none" stroke="${c}" stroke-width="${f(4*(1-q))}" opacity="${f(1-q)}"/>`;
 for(let k=0;k<8;k++){const a=k*Math.PI/4+rnd(k)*.4,d=12+46*ease(q);s+=box(x+Math.cos(a)*d-3,y+Math.sin(a)*d-3,6,6,c,1,` opacity="${f(1-q)}"`);}
 const v=back(q*2.2);
 return s+`<g transform="translate(${f(x)} ${f(y)}) scale(${f(v)})"><path d="M-12 -12L12 12M12 -12L-12 12" stroke="${N}" stroke-width="9" stroke-linecap="round"/><path d="M-12 -12L12 12M12 -12L-12 12" stroke="${G}" stroke-width="5" stroke-linecap="round"/></g>`;
}
// Isometric Packet Tracer workspace: blocks on a floor grid, cables with link lights.
const ISO=(gx,gy)=>[700+(gx-gy)*60.6,360+(gx+gy)*35];
// Device anchors are screen positions on the isometric floor, spaced so floating icons never meet labels.
const NET={user:[250,340,'正常使用者','pc'],attack:[250,580,'異常來源','pc'],core:[520,460,'核心交換器','switch'],gate:[790,460,'策略閘道','fw'],app:[1060,460,'應用服務','server'],ids:[655,620,'IDS','model']};
const at=key=>NET[key].slice(0,2);
const STOP=[712,446],WALL=[[740,410],[690,505]];
const up=([x,y])=>[x,y-14];
const LINKS=[['user','core'],['attack','core'],['core','gate'],['gate','app']];
function floor(o){
 let s='';
 for(let k=-6;k<=6;k++){const a=ISO(k,-4),b=ISO(k,5);s+=`M${f(a[0])} ${f(a[1])}L${f(b[0])} ${f(b[1])}`;}
 for(let k=-4;k<=5;k++){const a=ISO(-6,k),b=ISO(6,k);s+=`M${f(a[0])} ${f(a[1])}L${f(b[0])} ${f(b[1])}`;}
 return `<path d="${s}" stroke="${EDGE}" stroke-width="1" fill="none" opacity="${f(o)}"/>`;
}
function block(X,Y,accent){
 const q=46,h=26,P=list=>list.map(p=>p.map(f).join(' ')).join('L');
 return `<ellipse cx="${f(X)}" cy="${f(Y+30)}" rx="64" ry="20" fill="${accent}" opacity=".12"/>`
  +`<path d="M${P([[X-q*.866,Y-h],[X,Y-h+q*.5],[X,Y+q*.5],[X-q*.866,Y]])}Z" fill="${PANEL}" stroke="${EDGE}"/>`
  +`<path d="M${P([[X,Y-h+q*.5],[X+q*.866,Y-h],[X+q*.866,Y],[X,Y+q*.5]])}Z" fill="${N}" stroke="${EDGE}"/>`
  +`<path d="M${P([[X,Y-h-q*.5],[X+q*.866,Y-h],[X,Y-h+q*.5],[X-q*.866,Y-h]])}Z" fill="${EDGE}" stroke="${accent}" stroke-width="2"/>`;
}
function device(key,t,v,accent=FLOW){
 const [X,Y]=at(key),bob=Math.sin(t*2.4+X/90)*4;
 const s=block(X,Y,accent)+`<ellipse cx="${f(X)}" cy="${f(Y-26)}" rx="26" ry="13" fill="${accent}" opacity=".3"/>`+flatIcon(NET[key][3],X-28,Y-98+bob,56)+tx(X,Y+56,NET[key][2],22,FG,700,'middle');
 return pop(s,X,Y,v);
}
function cable(a,b,p,lit){
 const L=Math.hypot(b[0]-a[0],b[1]-a[1]);
 let s=seg(a[0],a[1],b[0],b[1],EDGE,4,` stroke-dasharray="${f(L)} ${f(L)}" stroke-dashoffset="${f(L*(1-clamp(p)))}"`);
 if(p>=1)[.24,.76].forEach(r=>s+=`<circle cx="${f(a[0]+(b[0]-a[0])*r)}" cy="${f(a[1]+(b[1]-a[1])*r)}" r="5" fill="${lit?FLOW:G}"${lit?' filter="url(#glow)"':''}/>`);
 return s;
}
function network(t,{build,cables,lit,traffic,mirror=false,ruled=false,quiet=false,wall=0}){
 let s=floor(.55*clamp(build*2));
 LINKS.forEach(([a,b],k)=>s+=cable(at(a),at(b),cables-k*.12,lit));
 const [cx,cy]=at('core'),[ix,iy]=at('ids');
 s+=seg(cx,cy,ix,iy,EDGE,3,` stroke-dasharray="8 7" opacity="${f(clamp(cables))}"`)+tx((cx+ix)/2-14,(cy+iy)/2+8,'鏡像',17,SUB,700,'end');
 ['user','attack','core','gate','app','ids'].forEach((key,k)=>s+=device(key,t,(build*1.8-k*.14)/.5,key==='gate'&&ruled?G:key==='ids'?T:FLOW));
 if(traffic>0){
  const normal=['user','core','gate','app'].map(k=>up(at(k)));
  for(let j=0;j<3;j++)s+=`<g opacity="${f(traffic)}">${packet(normal,(t*.15+j/3)%1,FLOW)}</g>`;
  const attack=['attack','core','gate','app'].map(k=>up(at(k))),u=(t*.13+.4)%1;
  if(ruled){
   const stop=STOP,path=[attack[0],attack[1],stop],v=Math.min(1,u*1.35);
   if(v<1)s+=packet(path,v,G);
   else s+=burst(stop[0],stop[1],(u*1.35-1)/.35);
  }else if(!quiet){
   const p=along(attack,u),r=(t*1.6)%1;
   s+=`<g opacity="${f(traffic)}"><circle cx="${f(p[0])}" cy="${f(p[1])}" r="${f(14+18*r)}" fill="none" stroke="${G}" stroke-width="2" opacity="${f(1-r)}"/>${packet(attack,u,G)}</g>`;
  }
  if(mirror)s+=packet([up([cx,cy]),up([ix,iy])],(t*.35)%1,G,.8);
 }
 if(wall>0){
  const [a,b]=WALL,h=110*ease(wall);
  s+=`<path d="M${f(a[0])} ${f(a[1])}L${f(b[0])} ${f(b[1])}L${f(b[0])} ${f(b[1]-h)}L${f(a[0])} ${f(a[1]-h)}Z" fill="${G}" fill-opacity=".16" stroke="${G}" stroke-width="2.5" opacity="${f(clamp(wall))}"/>`;
  for(let k=1;k<5;k++)s+=seg(a[0],a[1]-h*k/5,b[0],b[1]-h*k/5,G,1,` opacity="${f(.45*clamp(wall))}"`);
 }
 return s;
}
// Chapter scenes. Each receives the chapter-local time.
function titleScene(t,local){
 let s=floor(.35*ease(local/1.2));
 const u=inout(local/1.1),hx=-80+(1075+80)*u,hy=305;
 if(local<1.15)s+=`<path d="M${f(hx-360)} ${hy}L${f(hx)} ${hy}" stroke="url(#streak)" stroke-width="5" stroke-linecap="round"/><g filter="url(#glow)">${envelope(hx,hy,FLOW,1.4)}</g>`;
 const q=clamp((local-1.1)/.9);
 if(q>0&&q<1){s+=`<circle cx="1075" cy="305" r="${f(40+330*ease(q))}" fill="none" stroke="${FLOW}" stroke-width="${f(6*(1-q))}" opacity="${f(1-q)}"/>`;for(let k=0;k<20;k++){const a=k*Math.PI/10,r1=60+260*ease(q),r2=r1+30*(1-q);s+=seg(1075+Math.cos(a)*r1,305+Math.sin(a)*r1,1075+Math.cos(a)*r2,305+Math.sin(a)*r2,k%3?FLOW:G,2,` opacity="${f(1-q)}"`);}}
 const e=back((local-1.1)/.6),spin=t*18;
 s+=`<circle cx="1075" cy="305" r="190" fill="url(#spot)" opacity="${f(clamp(e))}"/>`;
 s+=grp(`<circle cx="1075" cy="305" r="168" fill="none" stroke="${FLOW}" stroke-width="1.5" stroke-dasharray="4 10" transform="rotate(${f(spin)} 1075 305)" opacity=".6"/>`+emblem(930,160,290),{s:e,o:e*2,cx:1075,cy:305});
 s+=grp(box(64,128,10,10,G,2)+tx(84,139,'AI SECURITY FRAMEWORK',18,FLOW,700,'start',' letter-spacing="3"'),{o:ease((local-1)/.5)});
 ['融合新型內容相依時序方向模型','入侵偵測與任務導向檢索增強稽核','之 AI 資安框架'].forEach((v,k)=>{const r=ease((local-1.25-.16*k)/.6);s+=`<g opacity="${f(r)}" transform="translate(0 ${f((1-r)*40)})">${tx(64,232+k*72,v,46,k===2?FLOW:FG,700)}</g>`;});
 const r=ease((local-2)/.6);
 return s+box(64,436,96*r,5,G,2)+`<g opacity="${f(r)}">${tx(64,500,'從流量判定，走到有證據的處置。',28,SUB)}</g>`;
}
function topologyScene(t,local){
 const z=1+.05*inout(local/7);
 let s=grp(network(t,{build:local/1.6,cables:(local-.7)/.9,lit:local>2.3,traffic:clamp((local-1.8)/.4),mirror:local>3.4}),{s:z,cx:655,cy:470});
 return s+headline([['看見每一個封包',FG],['走進同一條事件鏈',FLOW]],local,64,130,48);
}
function featureScene(t,local){
 let s=headline([['拆開封包',FG],['三種線索',FLOW]],local,64,150,54);
 const e=back(local/.5),open=ease((local-.5)/.4);
 s+=`<circle cx="220" cy="420" r="120" fill="url(#spot)"/>`;
 s+=grp(`<g filter="url(#glow)">${box(140,365,160,110,G,10)}</g><path d="M140 365L220 ${f(365+60-110*open)}L300 365" fill="${G}" stroke="${N}" stroke-width="4" stroke-linejoin="round"/><path d="M140 365L220 425L300 365" fill="none" stroke="${N}" stroke-width="4" stroke-linejoin="round"/>`,{s:e,o:e*2,cx:220,cy:420});
 const lanes=[['內容',FLOW],['時間差',B],['方向',G]];
 let tiles='';
 lanes.forEach(([label,c],L)=>{
  const y=310+L*100,start=.9+L*.35,front=520+(local-start)*520;
  if(local<start)return;
  s+=grp(chip(395,y,120,46,label,22,PANEL)+frame(335,y-23,120,46,c,23,2),{o:(local-start)*3});
  s+=seg(300,420,335,y,c,2,` opacity="${f(clamp(local-start))}"`);
  for(let k=0;k<26;k++){
   const x=520+((k*30+local*95)%780);
   if(x>front)continue;
   const v=rnd(k*7+L*31);
   if(L===0)tiles+=box(x,y+14-(10+v*30),20,10+v*30,c,3);
   else if(L===1)tiles+=`<circle cx="${f(x+10)}" cy="${y}" r="${f(4+v*9)}" fill="${c}"/>`;
   else tiles+=`<path d="${v>.45?`M${f(x)} ${y-11}L${f(x+20)} ${y}L${f(x)} ${y+11}Z`:`M${f(x+20)} ${y-11}L${f(x)} ${y}L${f(x+20)} ${y+11}Z`}" fill="${c}"/>`;
  }
 });
 s+=`<g clip-path="url(#lanes)">${tiles}</g>`;
 const mask=ease((local-3.4)/.6);
 if(mask>0)s+=`<rect x="520" y="270" width="${f(130*mask)}" height="80" fill="url(#hatch)" stroke="${G}" stroke-width="2"/>`+grp(chip(585,248,170,36,'識別欄位遮罩',18,G,N),{o:mask});
 const win=back((local-5.2)/.5);
 if(local>5.2){
  const k=(x,y,dx,dy)=>`<path d="M${x} ${y+dy*26}V${y}H${x+dx*26}" fill="none" stroke="${FLOW}" stroke-width="5" stroke-linecap="round"/>`;
  s+=grp(`<g filter="url(#glow)">${k(760,262,1,1)+k(1080,262,-1,1)+k(760,560,1,-1)+k(1080,560,-1,-1)}</g>`+box(760,262,320,298,FLOW,8,' fill-opacity=".07"')+chip(920,232,150,40,'流量切窗',20,FLOW,N),{s:win,o:win*2,cx:920,cy:411});
 }
 return ghost('FEATURE',t)+s;
}
function detectScene(t,local){
 let s=ghost('DETECT',t,460)+headline([['雙模型融合',FG],['17 類判定',FLOW]],local,64,150,54);
 const engines=[['CTBM',290,'內容・時間・方向'],['PBCNN',480,'短窗位元組']];
 s+=seg(64,385,210,385,EDGE,3);
 engines.forEach(([name,y,sub],k)=>{
  const v=(local-.3-k*.2)/.45;
  s+=seg(210,385,310,y,EDGE,3)+seg(530,y,640,385,EDGE,3);
  s+=pop(`<ellipse cx="420" cy="${y}" rx="138" ry="62" fill="none" stroke="${FLOW}" stroke-width="2" stroke-dasharray="6 9" stroke-dashoffset="${f(-t*40)}"/><g filter="url(#glow)">${box(310,y-40,220,80,B,14)}</g>`+tx(420,y+10,name,30,FG,700,'middle')+tx(420,y+88,sub,16,SUB,400,'middle'),420,y,v);
 });
 if(local>.8){
  s+=packet([[64,385],[210,385],[310,290]],(t*.5)%1,FLOW,.8)+packet([[64,385],[210,385],[310,480]],(t*.5+.5)%1,FLOW,.8);
  s+=packet([[530,290],[640,385]],(t*.7)%1,FLOW,.7)+packet([[530,480],[640,385]],(t*.7+.5)%1,FLOW,.7);
 }
 s+=pop(`<g filter="url(#glow)">${box(640,345,240,80,T,14)}</g>`+tx(760,395,'校準＋OOF Gate',24,FG,700,'middle'),760,385,(local-1.1)/.45);
 s+=seg(880,385,935,385,EDGE,3);
 const dv=back((local-1.7)/.5),spin=clamp((local-2.2)/3),lock=local>5.4;
 let dial='';
 for(let k=0;k<17;k++){
  const a0=-Math.PI/2+k*2*Math.PI/17+.025,a1=a0+2*Math.PI/17-.05,head=Math.floor(spin*17*3)%17;
  const c=lock?(k===4?G:T):(k===head?G:Math.abs(k-head)<=2?T:EDGE);
  dial+=`<path d="${arc(1060,385,92,124,a0,a1)}" fill="${c}"${lock&&k===4||!lock&&k===head?' filter="url(#glow)"':''}/>`;
 }
 s+=grp(dial+tx(1060,398,'17',52,FG,700,'middle')+tx(1060,428,'類',18,SUB,700,'middle'),{s:dv,o:dv*2,cx:1060,cy:385});
 if(lock){const r=back((local-5.4)/.4);s+=grp(chip(1060,555,250,46,'正式類別＋校準信心',20,G,N),{s:r,o:r*2,cx:1060,cy:555});}
 return s;
}
function retrievalScene(t,local){
 let s=ghost('RETRIEVE',t,500)+headline([['任務導向檢索',FG],['找出相似案例',FLOW]],local,64,140,50);
 const merge=ease((local-1.3)/.5),a=ease((local-.2)/.5),b=ease((local-.5)/.5);
 let bars='';
 for(let k=0;k<44;k++)bars+=box(80+k*7.5,268-rnd(k)*26,4.5,8+rnd(k)*26,FLOW,1);
 let prob='';
 for(let k=0;k<17;k++)prob+=box(80+k*7.5,268-rnd(k+90)*22,4.5,6+rnd(k+90)*22,G,1);
 s+=grp(bars,{x:(1-a)*-300+0,o:a})+grp(prob,{x:330+(1-b)*300-merge*0,o:b});
 s+=grp(tx(80,300,'512 維表徵',16,SUB),{o:a*(1-merge)})+grp(tx(410,300,'17 維機率',16,SUB),{o:b*(1-merge)});
 if(merge>0)s+=grp(`<g filter="url(#glow)">${box(76,276,468,4,FLOW,2)}</g>`+tx(80,300,'529 維任務向量',18,FLOW,700),{o:merge});
 const picks=[13,27,8,44,36],cols=10;
 const card=k=>[600+(k%cols)*56,170+Math.floor(k/cols)*70];
 const scan=clamp((local-1.9)/1.6),sx=600+scan*570;
 for(let k=0;k<60;k++){
  if(picks.includes(k)&&local>3.7)continue;
  const [x,y]=card(k),v=back((local-.3-((k%cols)+Math.floor(k/cols))*.04)/.4),lit=x<sx&&local<4.6?.35+rnd(k)*.65:0;
  s+=pop(box(x,y,46,60,PANEL,6)+frame(x,y,46,60,lit?FLOW:EDGE,6,lit?2:1)+box(x+8,y+12,30,4,lit?FLOW:EDGE,2)+box(x+8,y+22,20,4,EDGE,2),x+23,y+30,v);
 }
 if(scan>0&&scan<1)s+=`<g filter="url(#glow)">${box(sx-2,155,4,450,FLOW,2)}</g>`+box(sx-60,155,60,450,FLOW,0,' fill-opacity=".08"');
 s+=grp(tx(270,352,'Top-5',26,G,700,'middle'),{o:ease((local-3.6)/.4)});
 picks.forEach((pick,k)=>{
  const [x0,y0]=card(pick),v=inout((local-3.7-k*.14)/.7),x=x0+(80-x0)*v,y=y0+(372+k*46-y0)*v,w=46+334*v,h=60-22*v;
  s+=`<g${k===0?' filter="url(#glow)"':''}>${box(x,y,w,h,k===0?G:PANEL,6)}</g>`+frame(x,y,w,h,k===0?G:FLOW,6,2);
  if(v>.85)s+=grp(tx(x+18,y+26,String(k+1),20,k===0?N:FLOW,700)+tx(x+50,y+26,'相似訓練案例',18,k===0?N:FG,700),{o:(v-.85)*6.6});
 });
 return s+grp(tx(64,640,'只檢索訓練案例庫',20,SUB),{o:ease((local-4.6)/.5)});
}
function auditScene(t,local){
 let s=ghost('AUDIT',t,520)+headline([['本機 AI 稽核',FG],['附加證據，不改寫分類',FLOW]],local,64,130,46);
 const core=back((local-.3)/.5);
 const inputs=[['正式判定',300,B],['Top-5 案例證據',470,G]];
 inputs.forEach(([label,y,c],k)=>{
  const v=ease((local-.5-k*.2)/.5);
  s+=grp(box(90,y-30,250,60,PANEL,12)+frame(90,y-30,250,60,c,12,2)+box(90,y-30,8,60,c,3)+tx(220,y+8,label,22,FG,700,'middle'),{x:(1-v)*-280,o:v});
  if(local>1.2)s+=seg(340,y,560,390,EDGE,3)+packet([[340,y],[560,390]],(t*.6+k*.5)%1,c,.8);
 });
 s+=grp(`<circle cx="640" cy="390" r="150" fill="url(#spot)"/>`
  +`<ellipse cx="640" cy="390" rx="132" ry="46" fill="none" stroke="${FLOW}" stroke-width="2" stroke-dasharray="5 8" transform="rotate(${f(t*30)} 640 390)"/>`
  +`<ellipse cx="640" cy="390" rx="132" ry="46" fill="none" stroke="${T}" stroke-width="2" stroke-dasharray="14 10" transform="rotate(${f(-t*22+60)} 640 390)"/>`
  +`<g filter="url(#glow)"><circle cx="640" cy="390" r="84" fill="${PANEL}" stroke="${FLOW}" stroke-width="3"/></g>`
  +tx(640,370,'本機',18,SUB,700,'middle')+tx(640,404,'AI Judge',30,FG,700,'middle'),{s:core,o:core*2,cx:640,cy:390});
 const outs=[['支持',280,T],['複核',390,B],['不確定',500,EDGE]];
 outs.forEach(([label,y,c],k)=>{
  const v=back((local-2.1-k*.22)/.45);
  if(local>2.1+k*.22)s+=seg(724,390,930,y,EDGE,3)+packet([[724,390],[930,y]],clamp((local-2.1-k*.22)/.6),c,.8,.02);
  s+=grp(`<g filter="url(#glow)">${box(930,y-32,220,64,c,32)}</g>`+tx(1040,y+9,label,26,FG,700,'middle'),{s:v,o:v*2,cx:1040,cy:y});
 });
 return s+grp(tx(930,580,'三種結果，皆附案例依據',20,SUB),{o:ease((local-3.2)/.5)});
}
function controlScene(t,local){
 const ruled=t>=controlTimeline.apply&&t<controlTimeline.expiry,gone=t>=controlTimeline.expiry;
 const wall=ruled?clamp((t-controlTimeline.apply)/.4):gone?1-clamp((t-controlTimeline.expiry)/.5):0;
 let world=network(t,{build:1,cables:1,lit:true,traffic:1,ruled,quiet:gone,wall});
 const [gx,gy]=at('gate');
 if(t<controlTimeline.apply+.2){const v=inout(local/1),y=-40+(gy-80+40)*v;world+=seg(gx,y-140,gx,y,FLOW,4,` opacity="${f(.6*(1-v))}"`)+`<g filter="url(#glow)">${envelope(gx,y,B,1.3)}</g>`;}
 const flash=clamp((t-controlTimeline.apply)/.5);
 if(flash>0&&flash<1)world+=`<circle cx="${gx}" cy="${gy-20}" r="${f(30+160*ease(flash))}" fill="none" stroke="${G}" stroke-width="${f(8*(1-flash))}" opacity="${f(1-flash)}"/>`;
 if(ruled){const v=back((t-controlTimeline.apply)/.4);world+=grp(`<g filter="url(#glow)">${box(gx-74,240,148,46,G,23)}</g>`+tx(gx,271,'規則生效',24,N,700,'middle'),{s:v,o:v*2,cx:gx,cy:263});}
 if(gone){const v=back((t-controlTimeline.expiry)/.4);world+=grp(`<g filter="url(#glow)">${box(gx-74,240,148,46,T,23)}</g>`+tx(gx,271,'到期回復',24,FG,700,'middle'),{s:v,o:v*2,cx:gx,cy:263});}
 const shake=ruled&&((t*.13+.4)%1)*1.35>1&&((t*.13+.4)%1)*1.35<1.12?Math.sin(t*90)*3:0;
 let s=grp(world,{s:1.06-.04*inout(local/7),x:shake,cx:640,cy:440});
 s+=headline([['受控處置',FG],['到期自動回復',FLOW]],local,64,130,48);
 const steps=[['套用規則',controlTimeline.apply],['讀回確認',controlTimeline.readback],['到期撤銷',controlTimeline.expiry]];
 let card=box(930,92,286,190,PANEL,16,' fill-opacity=".92"')+frame(930,92,286,190,EDGE,16)+tx(954,128,'策略回條',20,FLOW,700);
 steps.forEach(([label,when],k)=>{
  const y=172+k*42,done=t>=(steps[k+1]?.[1]??controlTimeline.expiry+.6),now=t>=when&&!done;
  card+=`<circle cx="966" cy="${y-7}" r="12" fill="${done?T:now?G:'none'}" stroke="${done?T:now?G:EDGE}" stroke-width="2"/>`+(done?`<path d="M960 ${y-7}L965 ${y-2}L973 ${y-12}" fill="none" stroke="${FG}" stroke-width="2.5"/>`:'');
  card+=tx(990,y,label,20,done||now?FG:SUB,700);
 });
 const p=clamp((t-controlTimeline.apply)/(controlTimeline.expiry-controlTimeline.apply)),C=2*Math.PI*16;
 card+=`<circle cx="1180" cy="249" r="16" fill="none" stroke="${EDGE}" stroke-width="4"/><circle cx="1180" cy="249" r="16" fill="none" stroke="${G}" stroke-width="4" stroke-dasharray="${f(C*p)} ${f(C)}" transform="rotate(-90 1180 249)"/>`;
 const v=ease((local-.8)/.5);
 return s+grp(card,{x:(1-v)*320,o:v});
}
function resultScene(t,local){
 let s=ghost('RESULTS',t,640)+headline([['實測成果',FG]],local,64,124,48);
 const counted=ease(local/1.6),done=local>=1.6;
 const values=[done?percent(m.accuracy):(m.accuracy*counted*100).toFixed(2)+'%',done?percent(m.top5):(m.top5*counted*100).toFixed(2)+'%',`${done?m.rollback:Math.round(m.rollback*counted)} / ${m.network_cases}`];
 ['17類偵測 Accuracy','Top-5 命中率','隔離情境完整回復'].forEach((label,k)=>{
  const x=64+k*400,v=ease((local-k*.12)/.5),q=clamp((local-1.6)/.8);
  let c=box(x-16,206,368,244,PANEL,18)+frame(x-16,206,368,244,EDGE,18)+flatIcon(['model','retrieval','shield'][k],x+274,229,48);
  if(q>0&&q<1)c+=`<circle cx="${x+120}" cy="300" r="${f(30+140*ease(q))}" fill="none" stroke="${FLOW}" stroke-width="${f(4*(1-q))}" opacity="${f(1-q)}"/>`;
  c+=`<g${done?' filter="url(#glow)"':''}>${tx(x,320,values[k],64,FLOW,700)}</g>`+box(x,344,56*ease((local-1.4)/.4),4,G,2)+tx(x,392,label,24,FG,700);
  s+=`<g opacity="${f(v)}" transform="translate(0 ${f((1-v)*30)})">${c}</g>`;
 });
 const r=ease((local-1.8)/.5);
 return s+`<g opacity="${f(r)}">${tx(64,525,'偵測有依據，稽核有證據，處置可回復。',32,FG,700)+tx(64,606,`${count(m.detection_n)}筆偵測測試／${m.queries}筆檢索稽核／${m.network_cases}種隔離情境`,24,SUB)}</g>`;
}
function endScene(t,local){
 let s=floor(.3)+box(64,78,10,10,G,2)+tx(84,89,'AI SECURITY FRAMEWORK',18,FLOW,700,'start',' letter-spacing="3"');
 [['偵測有依據',FG],['稽核有證據',FG],['處置可回復',FLOW]].forEach(([text,c],k)=>{const v=clamp((local-.1-k*.22)/.35);s+=grp(tx(64,232+k*80,text,54,c,700),{s:1.25-.25*ease(v),o:v,cx:64,cy:212+k*80});});
 s+=`<circle cx="1075" cy="305" r="190" fill="url(#spot)"/><circle cx="1075" cy="305" r="168" fill="none" stroke="${FLOW}" stroke-width="1.5" stroke-dasharray="4 10" transform="rotate(${f(t*18)} 1075 305)" opacity=".6"/>`+emblem(930,160,290);
 const v=ease((local-.8)/.5);
 return s+`<g opacity="${f(v)}">${box(64,467,1152,80,PANEL,16)+tx(96,518,'判定 → 證據 → 稽核 → 處置與回復回條',28,FG,700)+tx(64,625,'展示結束 · 接續架構與實測成果說明',24,SUB)}</g>`;
}
const scenes=[titleScene,topologyScene,featureScene,detectScene,retrievalScene,auditScene,controlScene,resultScene,endScene];
function backdrop(t,i){
 const [sx,sy]=[[1075,305],[655,460],[220,420],[760,385],[860,380],[640,390],[790,440],[640,330],[1075,305]][i];
 let s=box(0,0,1280,720,N,0)+`<circle cx="${sx}" cy="${sy}" r="560" fill="url(#spot)"/>`;
 for(let k=0;k<44;k++){
  const x=(rnd(k)*1280+t*(6+rnd(k+50)*16))%1280,y=((rnd(k+100)*720-t*(3+rnd(k+150)*6))%720+720)%720;
  s+=`<circle cx="${f(x)}" cy="${f(y)}" r="${f(.8+rnd(k+200)*1.6)}" fill="${FLOW}" opacity="${f(.1+rnd(k+250)*.3)}"/>`;
 }
 return s;
}
export function frameSvg(t){
 const i=chapterAt(t),local=t-chapters[i].at,left=(chapters[i+1]?.at??duration)-t;
 const exit=i<chapters.length-1?clamp((.35-left)/.35):0,enter=i?ease(local/.3):1;
 let s=backdrop(t,i);
 s+=grp(scenes[i](t,local)+(i>0&&i<8?tag(i,local):''),{s:1+.04*(1-enter)+.05*exit,o:enter*(1-exit*.9),cx:640,cy:360});
 // Slanted light wipe marks every cut.
 const w=clamp(local/.5);
 if(i>0&&w<1){const x=-260+1800*inout(w);s+=`<path d="M${f(x)} 0H${f(x+120)}L${f(x-80)} 720H${f(x-200)}Z" fill="${FLOW}" opacity=".85"/><path d="M${f(x-150)} 0H${f(x-130)}L${f(x-330)} 720H${f(x-350)}Z" fill="${G}" opacity=".8"/>`;}
 s+=`<rect x="0" y="0" width="1280" height="720" fill="url(#vignette)"/>`;
 s+=tx(64,700,'方法流程示意 · 隔離TCP交易實測',18,SUB);
 s+=box(0,714,1280,6,PANEL,0)+box(0,714,1280*t/duration,6,G,0);
 const defs=`<defs><radialGradient id="spot"><stop offset="0" stop-color="${FLOW}" stop-opacity=".16"/><stop offset="1" stop-color="${FLOW}" stop-opacity="0"/></radialGradient>`
  +`<radialGradient id="vignette" cx=".5" cy=".5" r=".75"><stop offset=".6" stop-color="${N}" stop-opacity="0"/><stop offset="1" stop-color="${N}" stop-opacity=".8"/></radialGradient>`
  +`<linearGradient id="streak" x1="0" x2="1"><stop offset="0" stop-color="${FLOW}" stop-opacity="0"/><stop offset="1" stop-color="${FLOW}" stop-opacity="1"/></linearGradient>`
  +`<pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="10" height="10" fill="${N}"/><rect width="4" height="10" fill="${G}"/></pattern>`
  +`<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`
  +`<clipPath id="lanes"><rect x="520" y="240" width="720" height="300"/></clipPath></defs>`;
 return resolveColors(`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="${FONT}">${defs}${s}</svg>`);
}
