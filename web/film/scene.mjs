// Pure time -> SVG scene. Shared by the browser player and offline MP4 renderer.
export const duration=150;
export const chapters=[
 {at:0,title:'每筆告警，都有下一步',sub:'從網路流量到可追溯的 AI 資安事件',caption:'面對持續進入的網路流量，系統需要的不只是告警，更是有依據的下一步。'},
 {at:12,title:'先理解流量，再判斷威脅',sub:'正常服務與異常行為，共用同一條網路',caption:'正常使用者與異常來源同時連入服務。框架讀取準備好的真實流量輸入，展開事件判定。'},
 {at:30,title:'內容 × 時間 × 傳輸方向',sub:'CTBM 與 PBCNN 的互補判斷',caption:'CTBM 分析封包內容、時間與方向；PBCNN 補充短窗位元組模式，再由凍結 Gate 融合。'},
 {at:50,title:'讓判定帶著任務，找到證據',sub:'512 維表徵 ＋ 17 維機率 → 529 維任務向量',caption:'系統把模型表徵與正式分類機率組成任務向量，從真實訓練案例庫找出前五筆相似證據。'},
 {at:72,title:'AI 稽核，根據案例回答',sub:'支持、複核、不確定，留下結構化理由',caption:'本機 AI 比對預測與案例證據，輸出稽核狀態。正式分類保持可追溯，交由策略閘門檢核。'},
 {at:92,title:'檢核通過，才進入隔離驗證',sub:'同事件、同執行批次，銜接策略與回條',caption:'通過策略檢核的 Bot 事件進入隔離網路，套用測試規則並讀回，確認背景服務仍能連線。'},
 {at:114,title:'規則有期限，回復有紀錄',sub:'30 秒到期撤銷，重新驗證連線',caption:'測試規則在三十秒到期後撤銷。系統讀回規則、驗證交易恢復，並將結果接續到原事件。'},
 {at:130,title:'方法有數據，流程有實測',sub:'各項結果保留各自的驗證範圍',caption:'同測試集 Macro-F1 為百分之九十三點零五，檢索 Top-5 命中率為百分之九十七點六二。六種隔離情境的背景與回復驗證通過。'},
 {at:142,title:'看得懂判定，驗得到回復',sub:'AI 資安閉環框架',caption:'從偵測、證據、稽核到回復，用同一事件把 AI 判斷與資安應變接起來。'}
];
const C={bg:'#F4F7FB',ink:'#192B46',blue:'#1558D6',green:'#087963',muted:'#5D6C80',line:'#DCE4EF',red:'#C93C4B',soft:'#EDF3FF'};
const xesc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const txt=(x,y,s,size=22,fill=C.ink,weight=400,anchor='start')=>`<text x="${x}" y="${y}" font-size="${size}" fill="${fill}" font-weight="${weight}" text-anchor="${anchor}">${xesc(s)}</text>`;
const rect=(x,y,w,h,fill='#FFFFFF',stroke=C.line,r=12)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}"/>`;
const line=(x1,y1,x2,y2,color=C.line,w=3,dash='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${w}"${dash?` stroke-dasharray="${dash}"`:''}/>`;
function icon(x,y,kind,color=C.blue){
 let d=kind==='pc'?'<rect x="-23" y="-19" width="46" height="31" rx="3"/><path d="M-12 23h24M0 12v11"/>':kind==='server'?'<rect x="-22" y="-28" width="44" height="56" rx="4"/><path d="M-14-13h28M-14 0h28M-14 13h28"/>':kind==='router'?'<ellipse rx="29" ry="20"/><path d="m-17-5 10-1-2 7M17 5l-10 1 2-7M-2-13v26"/>':kind==='firewall'?'<path d="M-25-24h50v48h-50zM-25-8h50M-25 8h50M0-24v16M-12-8V8M12-8V8M0 8v16"/>':kind==='bank'?'<ellipse cy="-19" rx="26" ry="10"/><path d="M-26-19v38c0 14 52 14 52 0v-38M-26 0c0 14 52 14 52 0"/>':'<rect x="-23" y="-23" width="46" height="46" rx="7"/><path d="M-12-5h24M-12 5h24M-6-12v24M6-12v24"/>';
 return `<g transform="translate(${x} ${y})" stroke="${color}" stroke-width="2.4" fill="none" stroke-linecap="round" stroke-linejoin="round">${d}</g>`;
}
function device(x,y,kind,title,sub,color=C.blue){return rect(x-62,y-52,124,130)+icon(x,y-6,kind,color)+txt(x,y+44,title,17,C.ink,600,'middle')+txt(x,y+66,sub,12,C.muted,400,'middle')}
function packet(a,b,p,color=C.blue){const x=a[0]+(b[0]-a[0])*p,y=a[1]+(b[1]-a[1])*p;return `<g transform="translate(${x} ${y})"><rect x="-9" y="-6" width="18" height="12" rx="2" fill="white" stroke="${color}" stroke-width="2"/><path d="m-8-5 8 6 8-6" fill="none" stroke="${color}" stroke-width="1.5"/></g>`}
function flow(a,b,t,color=C.blue,count=3){let v=line(...a,...b,C.line,3);for(let i=0;i<count;i++)v+=packet(a,b,((t*.21+i/count)%1+1)%1,color);return v}
export function chapterAt(t){let i=chapters.length-1;while(i>0&&t<chapters[i].at)i--;return i}
export function frameSvg(time){
 const t=Math.max(0,Math.min(duration,time)),i=chapterAt(t),ch=chapters[i],local=t-ch.at;
 let s=`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" font-family="Microsoft JhengHei, Arial, sans-serif">${rect(0,0,1280,720,C.bg,C.bg,0)}`;
 s+=txt(44,38,'AI SECURITY FRAMEWORK',13,C.blue,700)+txt(1236,38,'產品流程動畫 · 拓樸示意',13,C.muted,400,'end')+line(44,56,1236,56);
 s+=txt(44,111,ch.title,36,C.ink,700)+txt(46,148,ch.sub,19,C.muted);
 // Persistent network map; same coordinates preserve spatial continuity.
 s+=rect(36,184,804,390,'#FFFFFF')+txt(58,213,'NETWORK TOPOLOGY',12,C.muted,700)+txt(817,213,i>=5&&i<7?'隔離測試床':'網路場景示意',12,C.muted,400,'end');
 const normal=[138,290],bad=[138,465],router=[338,377],firewall=[533,377],service=[735,377];
 s+=flow(normal,router,t,C.green,2)+flow(bad,router,t,C.red,i>0?4:1)+flow(router,firewall,t,C.blue,4);
 const blocked=(i===5&&local>4)||(i===6&&local<10);
 s+=line(...firewall,...service,C.line,3);
 if(!blocked)s+=flow(firewall,service,t,i===6?C.green:C.blue,3);
 else {s+=packet(firewall,service,(t*.2)%0.35,C.red)+txt(630,342,'規則已套用',14,C.red,600,'middle');s+=line(610,361,610,392,C.red,4)}
 s+=line(533,455,533,487,C.green,2)+flow([533,487],[735,487],t,C.green,2)+line(735,487,735,455,C.green,2)+txt(635,511,'背景交易持續連線',12,C.green,600,'middle');
 s+=device(...normal,'pc','正常使用者','HTTPS / TCP',C.green)+device(...bad,'pc','異常來源','Bot / 暴力嘗試',C.red)+device(...router,'router','邊界路由','流量匯入')+device(...firewall,'firewall','策略閘道',i===6&&local>=10?'到期撤銷':'受控規則')+device(...service,'server','應用服務','測試連線');
 s+=rect(286,521,493,33,i===5?'#EAF7F1':C.soft,'none',5)+txt(300,543,i===5?'背景服務：保留連線　｜　規則範圍：隔離網路':i===6?(local>=10?'規則已撤銷　｜　重新驗證交易與設定回復':'規則有效期追蹤中　｜　到期後自動撤銷'):'感知流量 → 形成事件 → 交付偵測與證據鏈',14,i===5?C.green:C.blue,600);
 // The right panel changes with each chapter, rather than inventing live telemetry.
 const px=864,pw=380;s+=rect(px,184,pw,390,'#FFFFFF');s+=txt(px+23,215,'EVENT / ANALYSIS',12,C.muted,700);
 const row=(y,label,value,active=false)=>rect(px+22,y,pw-44,49,active?C.soft:'#F7F9FC','none',6)+txt(px+36,y+30,label,16,C.muted)+txt(px+pw-36,y+30,value,17,active?C.blue:C.ink,600,'end');
 if(i<2){s+=txt(px+24,264,'不只發現異常',28,C.ink,700)+txt(px+24,302,'也要有證據與下一步。',23,C.ink);s+=row(329,'01　判定','17 類',true)+row(390,'02　查證','Top-5')+row(451,'03　應變','稽核與回復');}
 else if(i===2){s+=txt(px+24,263,'互補分支 → 正式判定',23,C.ink,700);s+=row(286,'CTBM','內容・時間・方向',true)+row(347,'PBCNN','短窗位元組',local>6)+row(408,'凍結 Gate','17 類機率',local>12);s+=txt(px+25,514,'保留表徵，供下游任務檢索。',17,C.muted);}
 else if(i===3){s+=txt(px+24,260,'529 維任務向量',27,C.blue,700);for(let n=0;n<5;n++){const y=282+n*42;s+=rect(px+23,y,pw-46,34,n<=Math.floor(local/3)?C.soft:'#F7F9FC','none',4)+txt(px+35,y+23,`#${n+1}　訓練案例證據`,15,C.ink)+txt(px+pw-36,y+23,'Top-5',13,C.blue,600,'end')}s+=txt(px+24,535,'案例庫只使用真實訓練資料。',16,C.muted);}
 else if(i===4){s+=txt(px+24,264,'本機 AI 證據稽核',26,C.ink,700)+row(287,'支持','交由策略檢核',true)+row(348,'複核','保留人工判斷')+row(409,'不確定','保留人工判斷');s+=txt(px+24,521,'保留原分類與結構化理由。',16,C.muted);}
 else if(i===5){s+=txt(px+24,263,'示意事件：Bot',26,C.ink,700)+row(287,'策略檢核','通過',true)+row(348,'規則與回條','同事件綁定',local>4)+row(409,'背景服務','持續連線',local>10);s+=txt(px+24,521,'隔離網路中的合成 TCP 交易。',16,C.muted);}
 else if(i===6){const left=Math.max(0,Math.ceil(30-local*3));s+=txt(px+24,263,'有期限的測試規則',25,C.ink,700)+txt(px+24,358,left===0?'已到期':`${left} 秒`,62,left===0?C.green:C.blue,700)+row(397,'規則讀回',local>10?'已撤銷':'有效期追蹤',local>10)+row(458,'連線回復',local>10?'驗證完成':'檢查中',local>10);s+=txt(px+24,549,'動畫加速；實測使用實際 30 秒。',14,C.muted);}
 else if(i===7){s+=txt(px+24,267,'93.05%',50,C.blue,700)+txt(px+24,298,'Macro-F1 · 18,998 筆測試',16,C.muted)+txt(px+24,359,'97.62%',50,C.blue,700)+txt(px+24,391,'Top-5 · 463 筆整合查詢',16,C.muted)+txt(px+24,453,'6 / 6',46,C.green,700)+txt(px+24,487,'隔離情境背景與回復通過',16,C.muted)+txt(px+24,539,'各項指標依各自實驗範圍呈現。',14,C.muted);}
 else {s+=txt(px+24,277,'偵測有依據',30,C.blue,700)+txt(px+24,342,'稽核有證據',30,C.blue,700)+txt(px+24,407,'回復有紀錄',30,C.green,700)+txt(px+24,493,'同一事件，串起完整處理。',20,C.ink);}
 const labels=['偵測判定','案例證據','AI 稽核','隔離與回復'];const active=i<2?-1:i===2?0:i===3?1:i===4?2:3;
 labels.forEach((l,k)=>{const x=44+k*300;s+=rect(x,590,285,40,k<=active?C.soft:'#FFFFFF',k===active?C.blue:C.line,7)+txt(x+16,616,`0${k+1}　${l}`,16,k<=active?C.blue:C.muted,600)});
 // Sentence split conservatively: no captions overlap diagram or controls.
 const cap=ch.caption,cut=cap.length>52?cap.lastIndexOf('，',52)+1:0;
 s+=txt(640,662,cut?cap.slice(0,cut):cap,18,C.ink,500,'middle');if(cut)s+=txt(640,690,cap.slice(cut),18,C.ink,500,'middle');
 s+=rect(0,715,1280*(t/duration),5,C.blue,C.blue,0)+`</svg>`;return s;
}
