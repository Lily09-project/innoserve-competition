(() => {
  const D = window.VERIFIED_RESULTS;
  const $ = (id) => document.getElementById(id);
  const pct = (value) => (value * 100).toFixed(2) + "%";
  const metric = (value, label, scope) =>
    `<div class="metric"><strong>${value}</strong><span>${label}</span><small>${scope}</small></div>`;
  const gate = D.detection["OOF Gate"],
    retrieval = D.retrieval,
    judge = D.judge,
    network = D.framework;
  $("headline-metrics").innerHTML =
    metric(
      pct(gate.accuracy),
      "17類偵測 Accuracy",
      `${gate.n.toLocaleString()}筆封存測試`,
    ) +
    metric(pct(gate.macro_f1), "17類偵測 Macro-F1", "相同測試集的模型比較") +
    metric(
      pct(retrieval.top5),
      "任務檢索 Top-5",
      `${retrieval.bank_rows.toLocaleString()}案例 · ${retrieval.queries}查詢`,
    ) +
    metric(
      `${network.rollback_passed_cases} / ${network.network_cases}`,
      "隔離情境完整回復",
      "同事件、同執行批次驗證",
    );
  $("model-bars").innerHTML = ["PBCNN", "CTBM", "OOF Gate"]
    .map(
      (name) =>
        `<div class="bar-row ${name === "OOF Gate" ? "ours" : ""}"><span>${name}</span><div class="bar-track"><div class="bar-value" style="width:${D.detection[name].macro_f1 * 100}%"></div></div><output>${pct(D.detection[name].macro_f1)}</output></div>`,
    )
    .join("");
  $("model-gain").textContent =
    `融合模型 Macro-F1 較 PBCNN 提高 ${((gate.macro_f1 - D.detection.PBCNN.macro_f1) * 100).toFixed(2)} 個百分點，較 CTBM 提高 ${((gate.macro_f1 - D.detection.CTBM.macro_f1) * 100).toFixed(2)} 個百分點。`;
  $("retrieval-metrics").innerHTML =
    `<div><strong>${pct(retrieval.top5)}</strong><span>Top-5 命中率</span></div><div><strong>${pct(retrieval.mrr5)}</strong><span>MRR@5</span></div>`;
  const states = { support: "支持", review: "複核", uncertain: "不確定" };
  $("judge-counts").innerHTML = Object.entries(states)
    .map(
      ([key, label]) =>
        `<div>${label}<strong>${judge.assessment_counts[key]}<small> 筆</small></strong></div>`,
    )
    .join("");
  $("audit-detail").textContent =
    `${judge.cases}筆事件完成本機稽核，${judge.valid_json_count}筆輸出有效JSON，正式分類改寫${judge.classification_changed_count}筆；支持精確率${pct(judge.support_precision)}。`;
  $("audit-scope").textContent =
    `${judge.detector_error_count}筆偵測誤判中，${judge.intercepted_error_count}筆分流至複核或不確定（${pct(judge.error_interception_rate)}），${judge.false_support_count}筆得到支持。策略閘門另行檢核，稽核結果不直接視為處置授權。`;
  function classTable() {
    const model = $("model-filter").value,
      query = $("class-search").value.trim().toLowerCase();
    const rows = D.detection[model].per_class.filter((row) =>
      row.label.toLowerCase().includes(query),
    );
    $("class-table").replaceChildren();
    for (const row of rows) {
      const tr = document.createElement("tr");
      const label = document.createElement("td");
      label.textContent = row.label;
      tr.append(label);
      const f1 = document.createElement("td");
      f1.innerHTML = `<span class="table-bar" aria-hidden="true"><i style="width:${row.f1 * 100}%"></i></span>${pct(row.f1)}`;
      tr.append(f1);
      for (const value of [
        pct(row.precision),
        pct(row.recall),
        row.support.toLocaleString(),
      ]) {
        const cell = document.createElement("td");
        cell.textContent = value;
        tr.append(cell);
      }
      $("class-table").append(tr);
    }
    if (!rows.length) {
      const tr = document.createElement("tr"),
        td = document.createElement("td");
      td.colSpan = 5;
      td.textContent = "沒有符合的類別，請調整搜尋條件。";
      tr.append(td);
      $("class-table").append(tr);
    }
    $("class-status").textContent =
      `${model} · 顯示${rows.length}／17類 · 稀有類別依實際測試筆數呈現。`;
  }
  $("model-filter").onchange = classTable;
  $("class-search").oninput = classTable;
  classTable();
  $("validation-metrics").innerHTML =
    metric(network.real_live_classes, "真實輸入類別", "本機模型即時重跑") +
    metric(network.real_local_llm_calls, "本機AI呼叫", "接續同事件Top-5證據") +
    metric(
      `${network.background_preserved_cases} / ${network.network_cases}`,
      "背景服務驗證通過",
      "六種隔離情境",
    ) +
    metric(
      network.stale_execution_rejected ? "通過" : "未通過",
      "過期批次拒絕檢查",
      "處置回條綁定同次執行",
    );
  const actions = {
    monitor: "持續監測",
    auth_hardening: "登入服務保護",
    upstream_scrubbing: "上游流量處理",
    capture_evidence: "蒐證與複核",
    block_c2_destination: "限制C2目的端連線",
  };
  $("network-table").innerHTML = network.cases
    .map(
      (row) =>
        `<tr><td>${row.validation_label}<small>${actions[row.action] || row.action}</small></td><td>${row.rules_applied}條</td><td>${pct(row.baseline_success_rate)} → ${pct(row.after_success_rate)}</td><td>${pct(row.background_success_rate)}</td><td class="status-good">${row.rollback_integrity ? "通過" : "未通過"}</td><td>${row.ttl_rollback_elapsed_seconds == null ? "監測／蒐證" : row.ttl_rollback_elapsed_seconds.toFixed(2) + "秒"}</td></tr>`,
    )
    .join("");
  const files = {
    "detection_17class.json": "17類偵測與模型比較",
    "retrieval_17class.json": "任務導向檢索",
    "local_judge_17class.json": "本機AI證據稽核",
    "framework_validation.json": "完整鏈路與隔離回復",
  };
  $("source-links").innerHTML =
    Object.entries(files)
      .map(
        ([name, label]) =>
          `<a class="source-link" href="results/${name}" download>${label} <span>↗ JSON</span></a>`,
      )
      .join("") +
    `<a class="source-link" href="publication-manifest.json">發布來源與檔案雜湊 ↗</a>`;
  $("version").textContent =
    `資料來源：四份實測彙整檔 · 版本 ${D.revision.slice(0, 7)} · 本頁只呈現保存結果，不在瀏覽器執行偵測模型或部署網路策略。`;
})();
