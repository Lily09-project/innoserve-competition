/** Run the self-contained exhibit without a network or genuine model assets. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM, VirtualConsole } = require("jsdom");
const root = path.resolve(__dirname, "..");
const filename = path.join(
  root,
  "deliverables/interactive/AI資安框架_離線互動展示.html",
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

function boot(reduced = false) {
  const errors = [];
  const dom = new JSDOM(html, {
    url: "file:///offline-exhibit.html",
    runScripts: "outside-only",
    virtualConsole: new VirtualConsole().on("jsdomError", (error) =>
      errors.push(error.message),
    ),
  });
  const w = dom.window;
  let tick;
  const downloads = [];
  Object.defineProperty(w.document, "hidden", { value: false });
  w.TextEncoder = TextEncoder;
  w.matchMedia = () => ({
    matches: reduced,
    addEventListener() {},
    removeEventListener() {},
  });
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
    "window.__test={state,SCENARIOS,LABELS,policyFor,retrieve,demoVector,stateAt,makeTransactions,networkAt,commandsFor,jump,render};\n        bind();",
  );
  w.eval(instrumented);
  assert.equal(errors.length, 0, errors.join("\n"));
  return { w, api: w.__test, errors, downloads, tick: (stamp) => tick(stamp) };
}

async function main() {
  const { w, api, downloads, tick } = boot();
  assert.equal(api.LABELS.length, 17);
  assert.equal(w.document.querySelectorAll("[data-scenario]").length, 4);
  assert.equal(api.state.speed, 2);
  assert.equal(api.state.playing, false);
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
    for (const time of [0, 2, 14, 18, 22, 27, 31, 37, 38, 50, 68, 73]) {
      api.jump(time, false);
      assert.ok(!w.document.querySelector("#board").outerHTML.includes("NaN"));
      assert.ok(w.document.querySelector("#detail").textContent.length > 10);
      const count = api.networkAt(api.makeTransactions(key), time).counts;
      assert.ok(
        Object.values(count)
          .filter((x) => typeof x === "object")
          .every((x) => x.passed >= 0 && x.dropped >= 0),
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
    const count = api.networkAt(api.makeTransactions(key), 73).counts;
    assert.ok(count.after.dropped > 0);
    assert.equal(count.before.dropped, 0);
    assert.equal(count.recovered.dropped, 0);
  }
  w.document.querySelector("[data-scenario=ddos]").click();
  tick(100);
  tick(200);
  assert.ok(
    Math.abs(api.state.time - 0.2) < 1e-8,
    "2x doubles elapsed display time",
  );
  w.document.querySelector("#playPause").click();
  assert.equal(api.state.playing, false);
  const seek = w.document.querySelector("#seek");
  seek.value = "45";
  seek.dispatchEvent(new w.Event("input"));
  assert.equal(api.state.time, 45);
  w.document.querySelector('[data-chapter="68"]').click();
  assert.equal(api.state.time, 68);
  assert.equal(api.state.playing, false);
  w.document.querySelector("#restart").click();
  assert.equal(api.state.time, 0);
  w.document.querySelector("#playPause").click();
  w.document
    .querySelector("[data-inspect]")
    .dispatchEvent(new w.KeyboardEvent("keydown", { key: " ", bubbles: true }));
  assert.equal(api.state.playing, false);
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
  const reduced = boot(true);
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
      api.jump(50, false);
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
  const offline = await readBlob(downloads[1]);
  assert.ok(offline.includes('id="playPause"'));
  assert.ok(offline.includes("script data-bundled"));
  assert.ok(!offline.includes("window.__test="));
  w.close();
  reduced.w.close();
  console.log(
    "Offline exhibit: 4 scenarios, 48 state transitions, retrieval, guard, playback, seek, keyboard, downloads and reduced motion passed. SVG geometry is stubbed in DOM tests; browser layout is not asserted.",
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
