/* Verify the public results page without any private data or backend. */
const { JSDOM, VirtualConsole } = require("jsdom");
const assert = require("node:assert/strict");
const fs = require("node:fs"),
  os = require("node:os"),
  path = require("node:path");
const { spawnSync } = require("node:child_process");
const root = path.resolve(__dirname, "..");
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "verified-site-"));
let dom;
try {
  const site = path.join(temporary, "site");
  const build = spawnSync(
    process.env.PYTHON || "python",
    ["scripts/build_public_site.py", "--output", site],
    { cwd: root, encoding: "utf8" },
  );
  assert.equal(build.status, 0, build.stderr);
  const errors = [],
    virtualConsole = new VirtualConsole();
  virtualConsole.on("jsdomError", (e) => errors.push(e.message));
  dom = new JSDOM(fs.readFileSync(path.join(site, "index.html"), "utf8"), {
    url: "https://example.github.io/innoserve-competition/",
    runScripts: "outside-only",
    virtualConsole,
  });
  dom.window.fetch = () => {
    throw Error("Public results must not call APIs");
  };
  for (const name of ["results-data.js", "site.js"])
    dom.window.eval(fs.readFileSync(path.join(site, name), "utf8"));
  const doc = dom.window.document;
  assert.equal(doc.querySelectorAll("#class-table tr").length, 17);
  assert.match(doc.getElementById("headline-metrics").textContent, /98.08%/);
  assert.match(doc.getElementById("retrieval-metrics").textContent, /97.62%/);
  assert.match(doc.getElementById("audit-scope").textContent, /18筆/);
  assert.match(doc.getElementById("audit-scope").textContent, /12筆/);
  const search = doc.getElementById("class-search");
  search.value = "Web";
  search.dispatchEvent(new dom.window.Event("input"));
  assert.equal(doc.querySelectorAll("#class-table tr").length, 2);
  search.value = "<script>";
  search.dispatchEvent(new dom.window.Event("input"));
  assert.match(doc.getElementById("class-status").textContent, /顯示0/);
  search.value = "";
  search.dispatchEvent(new dom.window.Event("input"));
  const select = doc.getElementById("model-filter");
  select.value = "PBCNN";
  select.dispatchEvent(new dom.window.Event("change"));
  assert.match(doc.getElementById("class-status").textContent, /PBCNN/);
  assert.equal(doc.querySelectorAll("#network-table tr").length, 6);
  assert.deepEqual(errors, []);
  for (const anchor of doc.querySelectorAll("a[href]")) {
    const href = anchor.getAttribute("href");
    if (href.startsWith("http") || href.startsWith("#")) continue;
    const file = path.join(
      site,
      href.endsWith("/") ? href + "index.html" : href,
    );
    assert.ok(fs.existsSync(file), "Missing linked artifact: " + href);
  }
  process.stdout.write(
    "PASS public site: verified metrics, 17-class filters, 6 network cases, downloads, no backend\n",
  );
} finally {
  dom?.window.close();
  fs.rmSync(temporary, { recursive: true, force: true });
}
