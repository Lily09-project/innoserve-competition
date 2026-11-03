/** Render the 30-second explainer film from the interactive exhibit itself.

The exhibit (deliverables/interactive/AI資安框架_自動循環展示.html) is opened in projector mode
in a headless Edge/Chrome, the HTTP-flood scenario is selected, and every frame is captured with
the timeline paused at an exact exhibit time, so the animation is the exhibit's own. A camera
pushes in on the station being processed (rendered at 2x, cropped back to 1080p) with a chapter
card, and pulls back to the whole board before the results. Title and
results cards use the same light visual system; figures on the results card come from
media/film/metrics.mjs, which refuses a stale results snapshot. The voiceover is
media/exhibit-film/narration.m4a, built by scripts/presentation/build_narration.py.

Needs EXHIBIT_BROWSER (or Edge/Chrome at the default path) and FFMPEG_BINARY.
Usage: node scripts/render_exhibit_film.mjs [stillsFolder]
*/
import {spawn, spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {metrics} from '../media/film/metrics.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const exhibit = path.join(root, 'deliverables/interactive/AI資安框架_自動循環展示.html');
const narration = path.join(root, 'media/exhibit-film/narration.m4a');
const output = path.join(root, 'deliverables/AI資安框架_系統展示影片_30秒快版.mp4');
const stills = path.resolve(root, process.argv[2] || 'validation/exhibit-film');
const FPS = 30, WIDTH = 1920, HEIGHT = 1080, TOTAL = 30, TITLE = 1.6, ENDING = 26, FADE = 0.4;
// Video seconds -> exhibit seconds, one segment per exhibit chapter; the final hold shows the delivered decision.
const SEGMENTS = [[1.6, 2.8, 0, 2], [2.8, 7.8, 2, 14], [7.8, 10.2, 14, 17], [10.2, 12.4, 17, 20], [12.4, 15.8, 20, 26],
  [15.8, 17.4, 26, 28], [17.4, 20.2, 28, 32], [20.2, 23, 32, 36], [23, 25.5, 36, 37.95], [25.5, 26 + FADE, 37.95, 37.95]];
const CHAPTER_STILLS = [2.0, 5.0, 9.0, 11.5, 14.5, 16.8, 19.0, 22.0, 25.0];
// Camera keyframes [video s, centre x, centre y, zoom] in CSS px of the 1920x1080 projector page:
// it pushes in on the station being processed so its text reads on a projector, then pulls back.
const CAMERA = [[1.6, 960, 540, 1], [2.6, 960, 540, 1], [3.4, 480, 580, 1.7], [7.6, 480, 580, 1.7], [8.3, 800, 620, 1.9],
  [10.0, 800, 620, 1.9], [10.6, 900, 690, 1.9], [12.2, 900, 690, 1.9], [12.9, 1070, 480, 1.8], [15.6, 1070, 480, 1.8],
  [16.2, 1300, 600, 1.8], [17.2, 1300, 600, 1.8], [17.9, 1650, 420, 1.9], [20.0, 1650, 420, 1.9], [20.6, 1680, 620, 1.8],
  [22.8, 1680, 620, 1.8], [23.4, 1680, 740, 1.9], [25.3, 1680, 740, 1.9], [26.0, 960, 540, 1]];
// Chapter cards shown while the camera is in close: [from, to, stage number, stage, step].
const CAPTIONS = [[2.8, 7.8, 1, '偵測', '封包逐筆編碼'], [7.8, 10.2, 1, '偵測', '雙模型融合判定'], [10.2, 12.4, 2, '檢索', '組合查詢向量'],
  [12.4, 17.4, 2, '檢索', 'Top-5 相似案例'], [17.4, 20.2, 3, '稽核', '本機 AI 核對證據'], [20.2, 23, 4, '處置', '策略逐項檢查'],
  [23, 25.5, 4, '處置', '限速送達路由器 r1']];
const SCALE = 2;  // render at 2x so close-ups stay sharp after the crop
const browserPath = [process.env.EXHIBIT_BROWSER, 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Google/Chrome/Application/chrome.exe'].find(p => p && fs.existsSync(p));
const ffmpeg = process.env.FFMPEG_BINARY;
if (!browserPath || !ffmpeg) throw new Error('Set EXHIBIT_BROWSER (if Edge/Chrome is elsewhere) and FFMPEG_BINARY');

function camera(v) {
  // Smoothstep between keyframes; before the first or after the last keyframe the camera holds.
  const k = CAMERA.findIndex(([t]) => t > v);
  let x, y, z;
  if (k <= 0) [, x, y, z] = CAMERA[k === 0 ? 0 : CAMERA.length - 1];
  else {
    const [t0, ...a] = CAMERA[k - 1], [t1, ...b] = CAMERA[k];
    const u = (v - t0) / (t1 - t0), e = u * u * (3 - 2 * u);
    [x, y, z] = a.map((value, i) => value + (b[i] - value) * e);
  }
  const w = WIDTH / z, h = HEIGHT / z;
  return {x: Math.min(Math.max(x - w / 2, 0), WIDTH - w), y: Math.min(Math.max(y - h / 2, 0), HEIGHT - h), w, h, z};
}

function exhibitTime(v) {
  const [a, b, t0, t1] = SEGMENTS.find(([s, e]) => v >= s && v < e) || SEGMENTS.at(-1);
  return t0 + (t1 - t0) * Math.min(1, (v - a) / (b - a));
}

// The film shows the board, scenario row and step caption; playback controls and links are hidden.
const FILM_CSS = `*{transition:none!important;animation:none!important}
.timeline,.view-tools,#openDetail,.mobile-hint{display:none!important}
body.focus-view .stage-bottom{justify-content:center}
#filmCaption{position:absolute;z-index:99;transform-origin:0 0;display:flex;align-items:center;gap:18px;padding:16px 30px 16px 16px;
  border-radius:44px;background:rgba(255,255,255,.96);box-shadow:0 10px 32px rgba(11,27,46,.22);border:2px solid #DCE3EC;
  font:700 40px "Segoe UI","Microsoft JhengHei",sans-serif;color:#0B1B2E;white-space:nowrap}
#filmCaption i{width:56px;height:56px;border-radius:50%;background:#F59E0B;color:#fff;font-style:normal;display:grid;place-items:center;font-size:34px}
#filmCaption b{color:#0F766E}
#filmCaption[hidden]{display:none}`;

function card(kind) {
  const pct = v => `${(v * 100).toFixed(2)}%`;
  const body = kind === 'title'
    ? `<div class="tag">2026 資安技術組 · 決賽</div>
       <h1>一次 HTTP 洪流<br>從封包到處置</h1>
       <p>偵測 → 檢索 → 稽核 → 處置 · 互動展示實錄（合成封包）</p>`
    : `<div class="tag">實測成果</div>
       <div class="row">${[[pct(metrics.accuracy), '17 類整體準確率'], [pct(metrics.top5), 'Top-5 檢索命中率'],
         [`${metrics.rollback}/${metrics.network_cases}`, '隔離情境到期回復']].map(([v, l]) => `<div class="stat"><b>${v}</b><span>${l}</span></div>`).join('')}</div>
       <p>偵測有依據，稽核有證據，處置可回復。</p>`;
  return `<!doctype html><meta charset="utf-8"><style>
    html,body{margin:0;width:${WIDTH}px;height:${HEIGHT}px;background:#F3F6FA;font-family:"Segoe UI","Microsoft JhengHei",sans-serif;color:#0B1B2E}
    main{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;text-align:center}
    .tag{color:#0F766E;font-weight:700;font-size:30px;letter-spacing:4px}
    h1{margin:0;font-size:96px;line-height:1.25}
    p{margin:0;font-size:36px;color:#52637A}
    .row{display:flex;gap:40px}
    .stat{width:420px;padding:44px 0;border-radius:24px;background:#fff;border:2px solid #DCE3EC;display:flex;flex-direction:column;gap:14px}
    .stat b{font-size:84px;color:#0F766E}.stat span{font-size:32px;color:#52637A}
    .bar{width:120px;height:8px;border-radius:4px;background:#F59E0B}
  </style><main>${body}<div class="bar"></div></main>`;
}

class Cdp {
  constructor(url) { this.ws = new WebSocket(url); this.id = 0; this.wait = new Map(); }
  async open() {
    await new Promise((resolve, reject) => { this.ws.onopen = resolve; this.ws.onerror = reject; });
    this.ws.onmessage = ({data}) => { const msg = JSON.parse(data); const done = this.wait.get(msg.id); if (done) { this.wait.delete(msg.id); done(msg); } };
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.wait.delete(id); reject(new Error(`${method}: no reply in 20s`)); }, 20000);
      this.wait.set(id, msg => { clearTimeout(timer); msg.error ? reject(new Error(`${method}: ${msg.error.message}`)) : resolve(msg.result); });
      this.ws.send(JSON.stringify({id, method, params}));
    });
  }
  async eval(expression) {
    const {result, exceptionDetails} = await this.send('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true});
    if (exceptionDetails) throw new Error(exceptionDetails.text);
    return result.value;
  }
  async shot(file, view = {x: 0, y: 0, w: WIDTH, h: HEIGHT}) {
    // The clip is the camera window; its scale maps it back to a 1920-px-wide frame at the 2x render.
    const clip = {x: view.x, y: view.y, width: view.w, height: view.h, scale: WIDTH / view.w / SCALE};
    const {data} = await this.send('Page.captureScreenshot', {format: 'png', clip});
    fs.writeFileSync(file, Buffer.from(data, 'base64'));
  }
  async load(url) {
    await this.send('Page.navigate', {url});
    await this.eval('new Promise(r => document.readyState === "complete" ? r() : addEventListener("load", r))');
  }
}

const work = fs.mkdtempSync(path.join(os.tmpdir(), 'exhibit-film-'));
const frames = path.join(work, 'frames');
fs.mkdirSync(frames);
fs.mkdirSync(stills, {recursive: true});
const port = 9400 + Math.floor(Math.random() * 400);
const browser = spawn(browserPath, ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--remote-debugging-port=${port}`,
  `--user-data-dir=${path.join(work, 'profile')}`, `--window-size=${WIDTH},${HEIGHT}`, 'about:blank'], {stdio: 'ignore'});
try {
  let targets;
  for (let k = 0; k < 50 && !targets; k++) {
    try { targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); } catch { await new Promise(r => setTimeout(r, 200)); }
  }
  const cdp = new Cdp(targets.find(t => t.type === 'page').webSocketDebuggerUrl);
  await cdp.open();
  await cdp.send('Page.enable');
  // Keep the page rendering as if it were in front; background throttling stalls headless capture.
  await cdp.send('Emulation.setFocusEmulationEnabled', {enabled: true});
  await cdp.send('Page.setWebLifecycleState', {state: 'active'});
  await cdp.send('Emulation.setDeviceMetricsOverride', {width: WIDTH, height: HEIGHT, deviceScaleFactor: SCALE, mobile: false});
  for (const kind of ['title', 'ending']) {
    const file = path.join(work, `${kind}.html`);
    fs.writeFileSync(file, card(kind));
    await cdp.load(pathToFileURL(file).href);
    await cdp.shot(path.join(work, `${kind}.png`));
  }
  await cdp.load(pathToFileURL(exhibit).href + '#present');
  await cdp.eval(`(async () => {
    document.head.insertAdjacentHTML('beforeend', '<style>${FILM_CSS.replace(/\n/g, '')}</style>');
    document.querySelector('[data-scenario="ddos"]').click();
    await new Promise(r => setTimeout(r, 300));
    document.getElementById('seek').step = 'any';
    document.body.insertAdjacentHTML('beforeend', '<div id="filmCaption" hidden></div>');
  })()`);
  // Place the chapter card at the camera window's lower left, scaled so it renders at a fixed size.
  const caption = (v, view) => {
    const item = CAPTIONS.find(([a, b]) => v >= a && v < b);
    const shown = item && view.z > 1.4;
    const html = shown ? `<i>${item[2]}</i><span><b>${item[3]}</b>｜${item[4]}</span>` : '';
    return cdp.eval(`(() => { const c = document.getElementById('filmCaption'); c.hidden = ${!shown};
      c.innerHTML = ${JSON.stringify(html)}; c.style.left = '${view.x + 36 / view.z}px'; c.style.top = '${view.y + view.h - 124 / view.z}px';
      c.style.transform = 'scale(${1 / view.z})'; })()`);
  };
  const seek = t => cdp.eval(`(async () => { const s = document.getElementById('seek'); s.value = '${t}';
    s.dispatchEvent(new Event('input')); await new Promise(r => setTimeout(r, 40)); })()`);
  const first = Math.round(TITLE * FPS), last = Math.round((ENDING + FADE) * FPS);
  for (let n = first; n < last; n++) {
    const view = camera(n / FPS);
    await seek(exhibitTime(n / FPS).toFixed(4));
    await caption(n / FPS, view);
    await cdp.shot(path.join(frames, `f${String(n - first).padStart(4, '0')}.png`), view);
    if ((n - first) % 100 === 0) console.log(`frame ${n - first} / ${last - first}`);
  }
  for (const [k, v] of CHAPTER_STILLS.entries()) {
    const view = camera(v);
    await seek(exhibitTime(v).toFixed(4));
    await caption(v, view);
    await cdp.shot(path.join(stills, `chapter-${k + 1}.png`), view);
  }
  // The slide-2 poster frame is the whole board once the decision is delivered.
  await seek('37.95');
  await caption(0, camera(0));
  await cdp.shot(path.join(stills, 'poster-frame.png'));
} finally {
  browser.kill();
}

// Title fades into the exhibit, the exhibit fades into the results card; narration mixed under.
const exhibitSeconds = ENDING + FADE - TITLE;
const graph = [`[0:v]fps=${FPS},trim=duration=${TITLE + FADE},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.3,format=yuv420p[t]`,
  `[1:v]fps=${FPS},format=yuv420p[x]`,
  `[2:v]fps=${FPS},trim=duration=${TOTAL - ENDING},setpts=PTS-STARTPTS,fade=t=out:st=${TOTAL - ENDING - 0.4}:d=0.4,format=yuv420p[e]`,
  `[t][x]xfade=transition=fade:duration=${FADE}:offset=${TITLE}[tx]`,
  `[tx][e]xfade=transition=fade:duration=${FADE}:offset=${ENDING}[v]`].join(';');
const result = spawnSync(ffmpeg, ['-hide_banner', '-loglevel', 'error', '-y',
  '-loop', '1', '-t', String(TITLE + FADE), '-i', path.join(work, 'title.png'),
  '-framerate', String(FPS), '-i', path.join(frames, 'f%04d.png'),
  '-loop', '1', '-t', String(TOTAL - ENDING), '-i', path.join(work, 'ending.png'),
  '-i', narration, '-filter_complex', graph, '-map', '[v]', '-map', '3:a', '-t', String(TOTAL),
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS),
  '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', output], {stdio: 'inherit'});
if (result.status !== 0) throw new Error('ffmpeg failed');
fs.rmSync(work, {recursive: true, force: true});
console.log(`Explainer film: ${path.relative(root, output)} (${TOTAL}s, ${exhibitSeconds.toFixed(1)}s of exhibit animation)`);
