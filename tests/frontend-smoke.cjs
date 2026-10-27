/* Execute the real UI against a disposable public-demo server. */
const { JSDOM, VirtualConsole } = require("jsdom");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "..");
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "innoserve-ui-"));
const demoRoot = path.join(temporary, "demo");
const child = spawn(
  process.env.PYTHON || "python",
  ["-u", "app/server.py", "--demo", "--demo-root", demoRoot, "--port", "0"],
  { cwd: root },
);
let output = "",
  diagnostics = "",
  dom;
child.stdout.on("data", (chunk) => (output += chunk));
child.stderr.on("data", (chunk) => (diagnostics += chunk));
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
(async () => {
  try {
    let base;
    for (let i = 0; i < 200; i++) {
      base = output.match(/http:\/\/127\.0\.0\.1:\d+/)?.[0];
      if (base) break;
      if (child.exitCode !== null) throw Error(diagnostics || output);
      await sleep(50);
    }
    assert.ok(base, "Demo server must start without private assets");
    const errors = [];
    const console = new VirtualConsole();
    console.on("jsdomError", (e) => errors.push(e.message));
    dom = new JSDOM(await (await fetch(base)).text(), {
      url: base,
      runScripts: "outside-only",
      virtualConsole: console,
    });
    dom.window.fetch = (url, options) => fetch(new URL(url, base), options);
    dom.window.AbortController = AbortController;
    dom.window.eval(
      fs.readFileSync(path.join(demoRoot, "web/data.js"), "utf8"),
    );
    dom.window.eval(fs.readFileSync(path.join(root, "web/app.js"), "utf8"));
    const doc = dom.window.document;
    for (let i = 0; i < 100 && doc.getElementById("recompute").disabled; i++)
      await sleep(20);
    assert.match(
      doc.querySelector(".synthetic-banner").textContent,
      /合成資料，非實測/,
    );
    assert.equal(doc.querySelectorAll("#case-list button").length, 17);
    for (const id of ["warmup", "live-run", "network-run"])
      assert.equal(doc.getElementById(id).disabled, true);
    doc.getElementById("show-all").click();
    assert.equal(doc.querySelectorAll("#event-content tbody tr").length, 5);
    doc.getElementById("recompute").click();
    for (let i = 0; i < 100 && doc.getElementById("recompute").disabled; i++)
      await sleep(20);
    assert.match(doc.getElementById("api-status").textContent, /檢索/);
    doc.getElementById("results-tab").click();
    assert.match(
      doc.getElementById("results-content").textContent,
      /合成資料，非實測/,
    );
    assert.doesNotMatch(
      doc.getElementById("results-content").textContent,
      /18,998|97.62/,
    );
    assert.deepEqual(errors, []);
    process.stdout.write(
      "PASS public-demo frontend smoke (17 events, retrieval, mode isolation)\n",
    );
  } finally {
    dom?.window.close();
    child.kill();
    await new Promise((resolve) =>
      child.exitCode !== null ? resolve() : child.once("exit", resolve),
    );
    fs.rmSync(temporary, { recursive: true, force: true });
  }
})().catch((error) => {
  process.stderr.write(error.stack + "\n");
  process.exitCode = 1;
});
