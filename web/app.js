/* Local model execution and evidence replay; network tests use isolated Mininet only. */
if(!window.FINAL_DATA){document.getElementById('event-content').innerHTML='<div class="empty-state"><strong>尚未產生展示資料。</strong><p>請依 README 設定本機資產後執行 <code>python scripts/export_web_data.py</code>，再重新整理頁面。</p></div>';throw Error('web/data.js missing');}
const {summary:S,events:E}=window.FINAL_DATA;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=x=>x==null?'—':`${(x*100).toFixed(2)}%`;
const names={support:'支持',review:'複核',uncertain:'不確定'};
let current=E.find(e=>e.prediction===13)||E[0],step=0;
let caseLimit=40;let liveIds=new Set(),backend=false,busy=false;const liveDone=new Set();
function block(title,body){return `<section class="section"><h3>${title}</h3>${body}</section>`}
function metric(value,label){return `<div class="metric"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`}
async function requestJson(path,options={},timeout=12000){const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),timeout);try{const response=await fetch(path,{...options,signal:controller.signal});if(!response.ok){let detail;try{detail=await response.json()}catch{}throw Error(detail?.message||(response.status===409?'已有工作執行中，請等待完成後再試。':`本機服務回應異常（${response.status}），請確認事件與執行批次。`))}return await response.json()}catch(error){if(error.name==='AbortError')throw Error('本機服務連線逾時。工作可能仍在執行，請稍後再確認。');throw error}finally{clearTimeout(timer)}}
function postJson(path,value){return requestJson(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)})}
function networkHtml(r){return block('本次即時隔離驗證',`<div class="metrics">${metric(pct(r.subject_after.success_rate),'套用後測試交易成功率')}${metric(pct(r.background_after.success_rate),'背景服務保留')}${metric(r.rollback_integrity?'完整回復':'需檢查','規則與連線回復')}</div><p>實際套用規則${r.rules_applied}條，${r.expiry_mode==='actual_monotonic_ttl_scheduler'?`有效${r.ttl_seconds}秒，${r.ttl_rollback_elapsed_seconds.toFixed(2)}秒完成到期撤銷`:'本事件採監測或蒐證策略，保留連線'}。</p><p>本次偵測與處置已依相同事件及執行批次核對，執行回條接續原事件紀錄。</p><p class="note">隔離網路中的合成TCP交易驗證，非原始攻擊封包的防禦率。</p>`)}
function selection(){const label=$('class-filter').value,mode=$('case-filter').value;return E.filter(e=>(label==='all'||e.validation_label===Number(label))&&(mode==='all'||mode==='live'&&liveIds.has(e.event_id)||mode==='error'&&e.prediction!==e.validation_label||mode===e.result.judge.assessment))}
function list(){const rows=selection();$('case-count').textContent=`${rows.length} 筆事件`;$('case-list').replaceChildren();rows.slice(0,caseLimit).forEach(e=>{const b=document.createElement('button');b.textContent=`${S.labels[e.prediction]} · ${pct(e.confidence)}`;const sm=document.createElement('small');sm.textContent=`${e.event_id.slice(-10)}　${names[e.result.judge.assessment]||'複核'}`;b.append(sm);b.setAttribute('aria-current',String(current?.event_id===e.event_id));b.onclick=()=>{current=e;step=0;list();render()};$('case-list').append(b)});if(rows.length>caseLimit){const more=document.createElement('button');more.textContent=`載入更多（尚有 ${rows.length-caseLimit} 筆）`;more.onclick=()=>{caseLimit+=40;list();controls()};$('case-list').append(more)}if(!rows.length){$('case-list').textContent='此條件沒有驗證案例。'}}
function render(){if(!current){$('event-content').textContent='此篩選條件沒有事件，請調整類別或案例範圍。';$('event-id').textContent='';$('event-title').textContent='沒有符合的事件';$('network-result').innerHTML='';$('ledger').textContent='';$('api-status').textContent='';controls();return}const e=current,r=e.result;$('event-id').textContent=e.event_id;$('event-title').textContent=S.labels[e.prediction];[...$('steps').children,...document.querySelectorAll('.hero-chain li')].forEach((x,i)=>x.classList.toggle('active',i%4<=step));let html=block('正式偵測結果',`<div class="metrics">${metric(pct(e.confidence),'正式分類信心')}${metric(e.pred_ctbm===e.pred_pbcnn?'一致':'分歧','模型分支判定')}${metric(e.prediction===e.validation_label?'正確':'誤判','本機驗證標籤對照')}</div><p class="note">${e.execution_mode==='live_local_models'?'本次已即時執行CTBM、PBCNN與凍結Gate。':'此畫面重播已完成的CTBM、PBCNN與凍結Gate推論結果。'}驗證標籤只用於本機成效計算。</p>`);
if(step>=1)html+=block('Top-5 訓練案例證據',`<table><thead><tr><th>排名</th><th>案例</th><th>類別</th><th>相似度</th></tr></thead><tbody>${e.evidence.map(x=>`<tr><td>${x.rank}</td><td class="mono">${esc(x.case_id.slice(-10))}</td><td>${esc(x.label)}</td><td>${x.similarity.toFixed(4)}</td></tr>`).join('')}</tbody></table><p class="note">529維任務向量，L2正規化與餘弦相似度。案例庫僅包含真實訓練資料。</p>`);
if(step>=2)html+=block('AI 證據稽核',`<p class="status ${r.judge.assessment==='support'?'':'warn'}">${names[r.judge.assessment]||'複核'}</p><p class="evidence-summary">前五筆案例中，${e.evidence.filter(x=>x.label_id===e.prediction).length}筆與正式分類一致，模型信心為${pct(e.confidence)}。</p><p>${esc(r.judge.reason)}</p><p class="note">${esc(r.judge.model||'人工複核分流')}　${r.judge.model?(e.execution_mode==='live_local_models'?'本次即時生成回覆':'讀取同事件保存回覆'):'人工複核模式'}。正式分類保持不變。</p>`);
if(step>=3)html+=block('策略檢核與動作編譯',`<div class="split"><div><p class="status ${r.policy.allowed?'':'warn'}">${r.policy.allowed?'通過策略檢核':'保留人工複核'}</p><p>${esc(r.policy.action)}</p><p>${esc(r.policy.reason)}</p></div><div><h3>執行範圍</h3><p>此頁顯示結構化動作與策略結果。</p><p>即時重跑後，可按上方「隔離處置與回復」，實際套用本次策略、讀回規則及驗證回復。</p></div></div>`);
$('event-content').innerHTML=html;$('network-result').innerHTML=e.network_receipt?networkHtml(e.network_receipt):'';$('ledger').textContent=JSON.stringify(e.network_receipt?.ledger||r.ledger,null,2);$('next').disabled=step>=3;$('api-status').textContent=e.execution_mode==='live_local_models'?`即時推論${e.timings.detector_ms.toFixed(1)} ms，本機AI${(e.timings.fresh_llm_ms/1000).toFixed(2)}秒`:'資料來自已保存的真實推論與檢索結果';document.querySelector('.mode').textContent=e.execution_mode==='live_local_models'?'本機模型即時執行結果':'本次實測結果重播';controls()}
function bars(rows){return rows.map(([name,value])=>`<div class="barrow"><span>${esc(name)}</span><div class="bartrack"><div class="bar" style="width:${Math.max(0,Math.min(100,value*100))}%"></div></div><span>${pct(value)}</span></div>`).join('')}
function results(){const f=S.fresh_retrieval,j=S.local_judge,n=S.network;let html=`<section class="result-block"><h3>17類偵測：18,998筆封存測試重新計分</h3><div class="metrics">${metric(pct(S.detection['OOF Gate'].accuracy),'Accuracy')}${metric(pct(S.detection['OOF Gate'].macro_f1),'Macro-F1')}</div>${bars(['PBCNN','CTBM','OOF Gate'].map(k=>[k,S.detection[k].macro_f1]))}<p class="note">上圖比較相同測試集的Macro-F1。</p></section>`;
if(f)html+=`<section class="result-block"><h3>本次17類任務檢索重跑</h3><div class="metrics">${metric(pct(f.top5),'Top-5命中率')}${metric(pct(f.mrr5),'MRR@5')}${metric(String(f.bank_rows),'真實訓練案例')}${metric(String(f.queries),'測試查詢')}</div><p>以固定模型重新產生512維表徵與17維正式機率。分類結果與封存Gate預測一致率${pct(f.fresh_prediction_agreement)}。</p></section>`;
if(j)html+=`<section class="result-block"><h3>本次17類本機AI稽核</h3><div class="metrics">${metric(String(j.cases),'實際稽核事件')}${metric(pct(j.error_interception_rate),'偵測誤判攔截率')}${metric(String(j.false_support_count),'誤判支持筆數')}</div><p>模型：${esc(j.model)}。誤判攔截分母為${j.detector_error_count}筆偵測誤判。這是本次本機模型結果。</p></section>`;
if(n)html+=`<section class="result-block"><h3>本次人工核准策略的隔離交易測試</h3><div class="metrics">${metric(pct(n.attack_suppression),'攻擊型測試交易抑制')}${metric(pct(n.normal_service),'正常測試交易保留')}${metric(pct(n.rollback),'回復完整性')}</div><p>${n.scenarios}個策略情境，共${n.rows}次重播。此測試使用人工核准靜態策略，與AI端到端處置效果分開驗證。</p></section>`;
html+=`<section class="result-block"><h3>歷史Fine-11模組證據：1,830筆配對稽核</h3>${bars(S.judge_comparison.map(x=>[x.name,x.error_interception]))}<p class="note">上圖為原始研究的偵測誤判攔截率，使用522維改良FE-Net；與本次17類、529維實驗分開呈現。</p></section>`;
if(S.faults)html+=`<section class="result-block"><h3>本次隔離故障驗證</h3><p>${S.faults.passed}／${S.faults.tests}項通過：包含未知動作、未知類別、未知稽核狀態、正常流量阻擋、不確定事件處置、高風險複核與部署失敗清理。</p></section>`;$('results-content').innerHTML=html}
const pageNames={events:'事件工作台',results:'實測與驗證',method:'方法與架構'};
for(const key of ['events','results','method']){
 $(key+'-tab').onclick=()=>{for(const k of ['events','results','method']){$(k+'-view').hidden=k!==key;$(k+'-tab').setAttribute('aria-selected',String(k===key));$(k+'-tab').tabIndex=k===key?0:-1} $('page-location').textContent=pageNames[key]};
 $(key+'-tab').onkeydown=event=>{const keys=['events','results','method'],index=keys.indexOf(key);let next;if(['ArrowDown','ArrowRight'].includes(event.key))next=(index+1)%3;if(['ArrowUp','ArrowLeft'].includes(event.key))next=(index+2)%3;if(event.key==='Home')next=0;if(event.key==='End')next=2;if(next!==undefined){event.preventDefault();$(keys[next]+'-tab').click();$(keys[next]+'-tab').focus()}};
}

$('class-filter').innerHTML='<option value="all">全部17類</option>'+S.labels.map((x,i)=>`<option value="${i}">${esc(x)}</option>`).join('');
for(const id of ['class-filter','case-filter'])$(id).onchange=()=>{caseLimit=40;const rows=selection();if(!rows.includes(current)){current=rows[0]||null;step=0;render()}list()};
$('reset').onclick=()=>{step=0;render()};$('next').onclick=()=>{step=Math.min(3,step+1);render()};$('show-all').onclick=()=>{step=3;render()};
$('recompute').onclick=async()=>{if(busy||!current)return;const id=current.event_id;busy=true;controls();$('api-status').textContent='正在從本機案例庫重新計算…';try{const data=await postJson('/api/retrieve',{event_id:id});if(data.replay_event?.event_id!==id)throw Error('檢索回覆與選擇事件不符，已停止更新。');const index=E.findIndex(e=>e.event_id===id);E[index]=data.replay_event;current=E[index];liveDone.delete(id);step=3;render();list();$('api-status').textContent=`已重新載入同筆封存判定並重算檢索與策略，檢索耗時${data.retrieval_ms.toFixed(2)} ms。稽核使用同事件保存回覆。`;$('operation-status').textContent='目前顯示封存事件重算結果；再次部署前請重新執行模型。'}catch(error){$('api-status').textContent=error.message||'本機服務無法連線，請確認啟動作品.cmd已開啟。'}finally{busy=false;controls()}};
function controls(){for(const id of ['recompute','reset','next','show-all','export-event'])$(id).disabled=busy||!current||(id==='next'&&step>=3)||(id==='recompute'&&!backend);$('stop-service').disabled=!backend||busy;$('warmup').disabled=!backend||busy;$('live-run').disabled=!backend||busy||!current||!liveIds.has(current.event_id);$('network-run').disabled=!backend||busy||!current||!liveDone.has(current.event_id)||![0,1,2,3,4,7,9,10,11,12,13].includes(current.prediction)||![0,1,2,3,4,7,9,10,11,12,13].includes(current.validation_label);for(const id of ['class-filter','case-filter'])$(id).disabled=busy;document.querySelectorAll('#case-list button').forEach(b=>b.disabled=busy)}
async function operation(action){
  if(busy||action!=='warmup'&&!current)return;
  const id=current?.event_id,execution=current?.execution_id;
  busy=true;if(action==='live')liveDone.delete(id);controls();
  $('operation-status').textContent='正在提交本機執行工作…';
  try{
    const {job_id}=await postJson('/api/operate',{action,event_id:id,execution_id:execution});
    const deadline=Date.now()+300000;
    while(true){
      if(Date.now()>deadline)throw Error('取得工作結果逾時，工作可能仍在執行。請等待服務恢復後再確認。');
      await new Promise(r=>setTimeout(r,700));
      const job=await requestJson('/api/jobs/'+job_id);
      $('operation-status').textContent=job.phase;
      if(job.state==='error')throw Error(job.phase);
      if(job.state!=='done')continue;
      if(action==='live'){
        if(job.result.event_id!==id)throw Error('模型回覆事件不符，已停止更新。');
        const index=E.findIndex(e=>e.event_id===id);E[index]=job.result;liveDone.add(id);
        if(current?.event_id===id){current=E[index];step=3;render()}list();
        $('operation-status').textContent='已完成即時偵測、檢索、本機AI與策略檢核，紀錄已保存。';
      }else if(action==='network'){
        const r=job.result;
        if(r.event_id!==id||r.execution_id!==execution)throw Error('處置回條批次不符，已停止更新。');
        const event=E.find(e=>e.event_id===id);event.network_receipt=r;
        if(current?.event_id===id)render();
        $('operation-status').textContent=r.rollback_integrity?'隔離測試完成，虛擬網路已清理。':'隔離測試已完成，恢復檢查異常，請查看回條。';
      }else $('operation-status').textContent='模型已預載。選擇可即時重跑的事件開始展示。';
      break;
    }
  }catch(error){$('operation-status').textContent=error.message||'執行失敗，已保留本機紀錄。'}
  finally{busy=false;controls()}
}
$('warmup').onclick=()=>operation('warmup');$('live-run').onclick=()=>operation('live');$('network-run').onclick=()=>operation('network');
$('stop-service').onclick=async()=>{if(busy)return;busy=true;controls();try{await postJson('/api/stop',{});backend=false;liveDone.clear();$('operation-status').textContent='本機服務已停止。重新執行「啟動作品.cmd」即可開啟。';document.querySelector('.mode').textContent='本機服務已停止'}catch(error){$('operation-status').textContent=error.message||'目前無法停止，請完成工作後重試。'}finally{busy=false;controls()}};
$('export-event').onclick=async()=>{
  if(busy||!current)return;
  const event=current;busy=true;controls();
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
  try{
    const response=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({event_id:event.event_id,execution_id:event.execution_id,mode:event.execution_mode==='live_local_models'?'live_local_models':'saved_prediction_replay'}),signal:controller.signal});
    if(!response.ok)throw Error('匯出失敗，事件批次可能已更新，請重新執行模型或載入事件後再試。');
    const canonicalText=await response.text();
    const url=URL.createObjectURL(new Blob([canonicalText],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download=event.event_id+'.json';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    $('operation-status').textContent='已匯出後端原始紀錄，保留事件鏈與處置回條的雜湊格式。';
  }catch(error){$('operation-status').textContent=error.name==='AbortError'?'匯出連線逾時，請確認本機服務。':error.message}
  finally{clearTimeout(timer);busy=false;controls()}
};
function frameworkResults(){const v=S.framework_validation;if(!v)return;$('results-content').insertAdjacentHTML('afterbegin',`<section class="result-block"><h3>本次完整鏈路驗證：即時模型到隔離處置</h3><div class="metrics">${metric(v.real_live_classes,'真實輸入類別')}${metric(v.network_cases,'同事件隔離情境')}${metric(v.background_preserved_cases+'/'+v.network_cases,'背景服務通過')}${metric(v.rollback_passed_cases+'/'+v.network_cases,'恢復驗證通過')}</div><p>17類輸入重新執行本機偵測、Top-5與AI稽核，6種事件接續同次執行結果進入隔離網路。其中${v.network_cases-v.non_disruptive_network_cases}種實際套用規則，${v.non_disruptive_network_cases}種維持監測或蒐證。</p><p class="note">執行回條核對事件與執行批次，過期批次遭拒。此為合成TCP交易的整合概念驗證。</p></section>`)}
$('class-filter').value='all';$('case-filter').value='all';list();render();results();requestJson('/api/status').then(v=>{if(v.product!=='ai-security-demo.v3')throw Error('展示服務版本不符，請停止舊服務並重新啟動作品。');backend=true;liveIds=new Set(v.live_event_ids);$('case-filter').value='live';const readyRows=selection();if(!readyRows.includes(current))current=readyRows.find(e=>e.prediction===13)||readyRows[0]||null;list();render();$('operation-status').textContent=v.model_ready?'模型已預載，可選擇17類輸入即時執行。':'可選「預載本機模型」，或直接重跑事件。';controls()}).catch(error=>{backend=false;$('operation-status').textContent=error.message||'本機服務尚未啟動，請執行啟動作品.cmd。';controls()});
frameworkResults();
