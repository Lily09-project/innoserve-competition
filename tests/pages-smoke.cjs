/* No backend: execute built static site with all network calls forbidden. */
const { JSDOM, VirtualConsole } = require("jsdom");
const fs = require("node:fs"),
  os = require("node:os"),
  path = require("node:path");
const { spawnSync } = require("node:child_process");
const assert = require("node:assert/strict");
const root = path.resolve(__dirname, "..");
const temporary = fs.mkdtempSync(
  path.join(os.tmpdir(), "innoserve-pages-test-"),
);
const site = path.join(temporary, "site");
(async () => {
  let dom;
  try {
    const build = spawnSync(
      process.env.PYTHON || "python",
      ["scripts/build_pages.py", "--output", site],
      { cwd: root, encoding: "utf8" },
    );
    assert.equal(build.status, 0, build.stderr);
    const errors = [],
      console = new VirtualConsole();
    console.on("jsdomError", (e) => errors.push(e.message));
    dom = new JSDOM(fs.readFileSync(path.join(site, "index.html"), "utf8"), {
      url: "https://example.github.io/innoserve-competition/",
      runScripts: "outside-only",
      virtualConsole: console,
    });
    dom.window.fetch = () => {
      throw Error("Static demo must never contact local APIs");
    };
    dom.window.Response = Response;
    dom.window.AbortController = AbortController;
    for (const name of ["data.js", "static-adapter.js", "app.js"])
      dom.window.eval(fs.readFileSync(path.join(site, name), "utf8"));
    await new Promise((r) => setTimeout(r, 30));
    const doc = dom.window.document;
    assert.equal(doc.querySelectorAll("#case-list button").length, 17);
    assert.match(
      doc.getElementById("operation-status").textContent,
      /GitHub Pages/,
    );
    assert.equal(doc.getElementById("stop-service").disabled, true);
    for (const event of dom.window.FINAL_DATA.events) {
      const response = await dom.window.STATIC_DEMO.fetch("/api/retrieve", {
        body: JSON.stringify({ event_id: event.event_id }),
      });
      assert.equal(response.status, 200);
      const result = await response.json();
      assert.equal(result.browser_ranking_verified, true);
      assert.equal(result.evidence.length, 5);
      const exported = await dom.window.STATIC_DEMO.fetch("/api/export", {
        body: JSON.stringify({ event_id: event.event_id }),
      });
      assert.equal(
        await exported.text(),
        dom.window.STATIC_FIXTURES.exports[event.event_id],
      );
    }
    doc.getElementById("recompute").click();
    await new Promise((r) => setTimeout(r, 30));
    assert.match(doc.getElementById("api-status").textContent, /瀏覽器重算/);
    assert.equal(doc.getElementById("warmup").disabled, true);
    assert.equal(fs.existsSync(path.join(site, "evidence")), false);
    assert.ok(
      fs.statSync(path.join(site, "film/media/product-45s.mp4")).size > 100000,
    );
    assert.match(
      fs.readFileSync(path.join(site, "film/index.html"), "utf8"),
      /45 秒/,
    );
    assert.deepEqual(errors, []);
    process.stdout.write(
      "PASS static Pages: 17 browser retrievals, canonical exports, no backend calls, fast video\n",
    );
  } finally {
    dom?.window.close();
    fs.rmSync(temporary, { recursive: true, force: true });
  }
})().catch((error) => {
  process.stderr.write(error.stack + "\n");
  process.exitCode = 1;
});
