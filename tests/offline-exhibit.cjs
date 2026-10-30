/** Run the self-contained exhibit without a network or genuine model assets. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM, VirtualConsole } = require("jsdom");
const root = path.resolve(__dirname, "..");
const filename = path.join(
  root,
  "deliverables/interactive/AI資安框架_自動循環展示.html",
);
const html = fs.readFileSync(filename, "utf8");
const source = new JSDOM(html);
assert.equal(
  source.window.document.querySelectorAll(
    "script[src],link[rel=stylesheet],iframe,form",
  ).length,
  0,
);
assert.equal(source.window.document.querySelectorAll("script").length, 1);
assert.equal(
  source.window.document.querySelectorAll('[src^="http"],[href^="http"]')
    .length,
  0,
);
source.window.close();

function boot(reduced = false, input = html) {
  const errors = [];
  const dom = new JSDOM(input, {
    url: "file:///offline-exhibit.html",
    runScripts: "outside-only",
    virtualConsole: new VirtualConsole().on("jsdomError", (error) =>
      errors.push(error.message),
    ),
  });
  const w = dom.window;
  let tick;
  const downloads = [];
  Object.defineProperty(w.document, "hidden", {
    value: false,
    configurable: true,
  });
  w.TextEncoder = TextEncoder;
  const motionListeners = [];
  const motion = {
    matches: reduced,
    addEventListener(type, callback) {
      if (type === "change") motionListeners.push(callback);
    },
    removeEventListener() {},
  };
  w.matchMedia = () => motion;
  w.requestAnimationFrame = (callback) => {
    tick = callback;
    return 1;
  };
  w.HTMLElement.prototype.scrollIntoView = function () {};
  w.SVGElement.prototype.getTotalLength = () => 100;
  w.SVGElement.prototype.getPointAtLength = (length) => ({
    x: length,
    y: length,
  });
  w.HTMLDialogElement.prototype.showModal = function () {
    this.open = true;
  };
  w.HTMLDialogElement.prototype.close = function () {
    this.open = false;
    this.dispatchEvent(new w.Event("close"));
  };
  w.URL.createObjectURL = (blob) => {
    downloads.push(blob);
    return "blob:test";
  };
  w.URL.revokeObjectURL = () => {};
  w.HTMLAnchorElement.prototype.click = function () {};
  const code = w.document.querySelector("script").textContent;
  // Test-only instrumentation: production file has no exposed debug state.
  const instrumented = code.replace(
    "        bind();",
    "window.__test={state,SCENARIOS,LABELS,policyFor,retrieve,demoVector,stateAt,makeTransactions,networkAt,commandsFor,jump,render,startScenario,DURATION,COMMAND_ARRIVAL,SCENARIO_ORDER,activeNodeIds};\n        bind();",
  );
  w.eval(instrumented);
  assert.equal(errors.length, 0, errors.join("\n"));
  return {
    w,
    api: w.__test,
    errors,
    downloads,
    tick: (stamp) => tick(stamp),
    setReduced(value) {
      motion.matches = value;
      motionListeners.forEach((callback) => callback({ matches: value }));
    },
  };
}

async function main() {
  const { w, api, downloads, tick, errors } = boot();
  assert.equal(api.LABELS.length, 17);
  assert.equal(w.document.querySelectorAll(".light-legend > span").length, 4);
  for (const selector of [
    "#sceneLabel",
    "#sceneCaption",
    "#processingLabel",
    ".light-legend",
    ".view-tools",
    "#stageMessage",
    "#openDetail",
  ])
    assert.equal(w.document.querySelectorAll(selector).length, 1, selector);
  const zoom = w.document.querySelector("#diagramZoom");
  for (const value of ["100", "125", "150", "200"]) {
    zoom.value = value;
    zoom.dispatchEvent(new w.Event("change"));
    assert.equal(
      w.document
        .querySelector("#board")
        .style.getPropertyValue("--diagram-width"),
      value + "%",
    );
  }
  const originalTime = api.state.time;
  w.document.querySelector("#focusView").click();
  assert.equal(w.document.body.classList.contains("focus-view"), true);
  assert.equal(
    w.document.querySelector("#focusView").getAttribute("aria-pressed"),
    "true",
  );
  w.document.dispatchEvent(
    new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
  );
  assert.equal(w.document.body.classList.contains("focus-view"), false);
  assert.equal(api.state.time, originalTime);
  const scrollRegion = w.document.querySelector(".board-scroll");
  scrollRegion.dispatchEvent(
    new w.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }),
  );
  assert.equal(
    api.state.time,
    originalTime,
    "arrow keys in diagram scroll rather than seek",
  );
  assert.equal(w.document.querySelectorAll("[data-scenario]").length, 4);
  assert.equal(api.state.speed, 1);
  assert.equal(api.state.playing, true);
  for (const key of Object.keys(api.SCENARIOS)) {
    w.document.querySelector(`[data-scenario="${key}"]`).click();
    assert.equal(api.state.key, key);
    assert.equal(api.state.playing, true);
    const top = api.retrieve(key);
    assert.equal(top.length, 5);
    assert.equal(new Set(top.map((row) => row.id)).size, 5);
    assert.ok(
      top.every(
        (row) =>
          row.vector.length === 529 &&
          Math.abs(Math.hypot(...row.vector) - 1) < 1e-10,
      ),
    );
    for (let i = 1; i < top.length; i++)
      assert.ok(top[i - 1].similarity >= top[i].similarity);
    for (const time of [0, 2, 14, 17, 20, 26, 28, 32, 36, 37, 37.6, 38]) {
      api.jump(time, false);
      const stage =
        time < 14
          ? "traffic"
          : time < 20
            ? "detection"
            : time < 32
              ? "audit"
              : "policy";
      assert.equal(
        w.document.querySelectorAll('[aria-current="step"]').length,
        1,
      );
      assert.equal(
        w.document.querySelector('[aria-current="step"]').dataset.stage,
        stage,
      );
      assert.ok(!w.document.querySelector("#board").outerHTML.includes("NaN"));
      assert.ok(w.document.querySelector("#detail").textContent.length > 10);
      const count = api.networkAt(api.makeTransactions(key), time).counts;
      assert.ok(
        [count.before.passed, count.before.dropped, count.background].every(
          (x) => Number.isFinite(x) && x >= 0,
        ),
      );
    }
  }
  assert.equal(api.policyFor("review").allowed, false);
  assert.equal(api.policyFor("review").action, "capture_evidence");
  assert.ok(
    api.commandsFor("review").every((line) => !line.startsWith("iptables")),
  );
  assert.equal(api.policyFor("benign").allowed, true);
  for (const key of ["ddos", "ssh"]) {
    assert.equal(api.policyFor(key).allowed, true);
    const count = api.networkAt(api.makeTransactions(key), 38).counts;
    assert.ok(
      count.before.passed >= 0 &&
        count.before.dropped === 0 &&
        count.background >= 0,
    );
    assert.equal(
      count.after,
      undefined,
      "no invented post-rule effect counter",
    );
  }
  w.document.querySelector("[data-scenario=ddos]").click();
  const speed = w.document.querySelector("#speed");
  speed.value = "2";
  speed.dispatchEvent(new w.Event("change"));
  tick(100);
  tick(200);
  assert.ok(
    Math.abs(api.state.time - 0.2) < 1e-8,
    "2x doubles elapsed display time",
  );
  w.document.querySelector("#playPause").click();
  assert.equal(api.state.playing, false);
  const seek = w.document.querySelector("#seek");
  seek.value = "25";
  seek.dispatchEvent(new w.Event("input"));
  assert.equal(api.state.time, 25);
  w.document.querySelector('[data-chapter="36"]').click();
  assert.equal(api.state.time, 36);
  assert.equal(api.state.playing, false);
  w.document.querySelector("#restart").click();
  assert.equal(api.state.time, 0);
  w.document.querySelector("#playPause").click();
  w.document
    .querySelector("[data-inspect]")
    .dispatchEvent(new w.KeyboardEvent("keydown", { key: " ", bubbles: true }));
  assert.equal(api.state.playing, false);
  w.document.querySelector("#focusView").click();
  w.document.querySelector("#openDetail").click();
  assert.equal(w.document.body.classList.contains("focus-view"), false);
  w.document.querySelector("#about").click();
  assert.ok(w.document.querySelector("#dialog").open);
  w.document.querySelector("#closeDialog").click();
  assert.ok(!w.document.querySelector("#dialog").open);
  w.document.querySelector("#export").click();
  assert.equal(downloads.length, 1);
  w.document.querySelector("#offline").click();
  assert.equal(downloads.length, 2);
  api.jump(30, false);
  w.document.querySelector("[data-tab=rag]").click();
  assert.equal(
    w.document.querySelector("[data-tab=rag]").getAttribute("aria-pressed"),
    "true",
  );
  assert.equal(
    w.document.querySelectorAll("[id]").length,
    new Set([...w.document.querySelectorAll("[id]")].map((n) => n.id)).size,
  );
  // Real frame callbacks must wrap in order across two full cycles.
  const loop = boot();
  assert.equal(loop.api.DURATION, 38);
  let stamp = 100;
  const expected = [
    "ddos",
    "ssh",
    "review",
    "benign",
    "ddos",
    "ssh",
    "review",
    "benign",
  ];
  loop.tick(stamp);
  for (const next of expected) {
    loop.api.jump(37.95, true);
    loop.tick((stamp += 100));
    loop.tick((stamp += 100));
    assert.equal(loop.api.state.key, next);
    assert.equal(loop.api.state.time, 0);
    assert.equal(loop.api.state.playing, true);
  }
  loop.w.document.querySelector("#about").click();
  const saved = loop.api.state.key;
  for (let i = 0; i < 400; i++) loop.tick((stamp += 100));
  assert.equal(loop.api.state.key, saved);
  assert.ok(loop.w.document.querySelector("#dialog").open);
  assert.equal(loop.api.state.playing, false);
  loop.w.document.querySelector("#closeDialog").click();
  loop.w.document.querySelector("#playPause").click();
  Object.defineProperty(loop.w.document, "hidden", {
    value: true,
    configurable: true,
  });
  loop.w.document.dispatchEvent(new loop.w.Event("visibilitychange"));
  const time = loop.api.state.time;
  loop.tick((stamp += 100000));
  assert.equal(loop.api.state.time, time);
  Object.defineProperty(loop.w.document, "hidden", {
    value: false,
    configurable: true,
  });
  loop.w.document.dispatchEvent(new loop.w.Event("visibilitychange"));
  loop.tick((stamp += 100000));
  assert.equal(loop.api.state.time, time, "no background catch-up");
  assert.deepEqual(loop.errors, []);
  loop.w.close();
  const reading = boot();
  reading.api.jump(20, true);
  reading.w.document.querySelector("#follow").focus();
  assert.equal(
    reading.api.state.playing,
    false,
    "focus pauses without replacing focused content",
  );
  assert.equal(reading.w.document.activeElement.id, "follow");
  reading.w.document.querySelector("#playPause").click();
  reading.w.document.querySelector("#diagramRegion").focus();
  assert.equal(reading.api.state.playing, false);
  reading.w.document.querySelector("#about").focus();
  reading.w.document.querySelector("#about").click();
  assert.equal(
    reading.w.document.querySelector("#dialog").getAttribute("aria-labelledby"),
    "dialogTitle",
  );
  assert.ok(
    reading.w.document.querySelector("#dialogTitle").textContent.length > 0,
  );
  assert.equal(reading.w.document.activeElement.id, "closeDialog");
  reading.w.document.querySelector("#closeDialog").click();
  assert.equal(reading.w.document.activeElement.id, "about");
  reading.api.jump(20, false);
  const modified = new reading.w.KeyboardEvent("keydown", {
    key: "ArrowRight",
    ctrlKey: true,
    bubbles: true,
    cancelable: true,
  });
  reading.w.document.body.dispatchEvent(modified);
  assert.equal(reading.api.state.time, 20);
  assert.equal(modified.defaultPrevented, false);
  reading.w.document.querySelector("#playPause").click();
  reading.setReduced(true);
  assert.equal(
    reading.api.state.playing,
    false,
    "runtime preference change pauses",
  );
  reading.setReduced(false);
  assert.equal(
    reading.api.state.playing,
    false,
    "preference change does not restart",
  );
  assert.equal(reading.w.document.querySelectorAll(".skip-links a").length, 2);
  assert.deepEqual(reading.errors, []);
  reading.w.close();
  const reduced = boot(true);
  assert.equal(reduced.api.state.playing, false);
  reduced.w.document.querySelector("[data-scenario=ssh]").click();
  assert.equal(
    reduced.api.state.playing,
    false,
    "reduced motion respects static navigation",
  );
  if (process.argv.includes("--render")) {
    const dir = path.join(root, "validation/offline-exhibit-20261029");
    fs.mkdirSync(dir, { recursive: true });
    for (const key of Object.keys(api.SCENARIOS)) {
      w.document.querySelector(`[data-scenario=${key}]`).click();
      api.jump(37.6, false);
      fs.writeFileSync(
        path.join(dir, key + ".svg"),
        w.document.querySelector("#board").outerHTML,
      );
    }
  }
  const readBlob = (blob) =>
    new Promise((resolve, reject) => {
      const reader = new w.FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsText(blob);
    });
  const exported = JSON.parse(await readBlob(downloads[0]));
  assert.equal(exported.mode, "synthetic_educational_demo");
  assert.equal(exported.learned_models_executed, false);
  assert.equal(exported.llm_called, false);
  assert.equal(exported.network_rules_executed, false);
  assert.equal(
    exported.encoding.mode,
    "illustrative_not_training_preprocessor",
  );
  assert.equal(exported.query_vector.length, 529);
  assert.equal(exported.top5.length, 5);
  assert.equal(exported.scenario_duration_seconds, 38);
  assert.equal(exported.playback, "automatic_cycle");
  const offline = await readBlob(downloads[1]);
  assert.ok(offline.includes('id="playPause"'));
  assert.ok(offline.includes("script data-bundled"));
  assert.ok(!offline.includes("window.__test="));
  const savedPage = boot(false, offline);
  assert.equal(savedPage.api.state.key, "benign");
  assert.equal(savedPage.api.state.playing, true);
  assert.equal(savedPage.w.document.querySelectorAll("#playPause").length, 1);
  savedPage.w.close();
  assert.deepEqual(
    errors,
    [],
    "No runtime errors after all interaction states",
  );
  assert.deepEqual(reduced.errors, [], "No runtime errors with reduced motion");
  w.close();
  reduced.w.close();
  console.log(
    "Offline exhibit: 4 scenarios, 48 state transitions, 8 automatic wraps, retrieval, guard, playback, seek, keyboard, downloads and reduced motion passed. SVG geometry is stubbed in DOM tests; browser layout is not asserted.",
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
