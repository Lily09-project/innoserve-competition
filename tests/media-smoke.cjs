const assert = require('node:assert/strict');
const palette = require('../design-system/palette.json');
const typography = require('../design-system/typography.json');
(async () => {
  const {frameSvg, duration, chapters,controlTimeline,playbackSpeed,presentationDuration,maxDuration} = await import('../media/film/scene.mjs');
  const {JSDOM} = require('jsdom');
  assert.equal(duration, 60);
  assert.equal(chapters.at(-1).title,'展示結束');
  assert.ok(frameSvg(59.9).includes('展示結束'));
  assert.ok(frameSvg(59.9).includes(typography.cjk));
  assert.ok(frameSvg(59.9).includes(typography.latin));
  assert.ok(playbackSpeed>=1.5);
  assert.ok(presentationDuration<=maxDuration && maxDuration<=40);
  assert.ok(frameSvg(24).includes(palette.teal), 'completed stages use the shared teal');
  assert.ok(frameSvg(24).includes(palette.navy), 'headings retain the shared navy');
  assert.equal(chapters.find(c=>c.title==='實測成果').at,52, 'results receive 2.5 seconds at 2x');
  assert.ok(frameSvg(51.5).includes('到期回復'), 'recovery remains visible before the results cut');
  const resultsAt=chapters.find(c=>c.title==='實測成果').at;
  assert.equal(controlTimeline.start,chapters.find(c=>c.title==='受控處置').at);
  assert.ok(controlTimeline.apply>=controlTimeline.start);
  for(const span of [controlTimeline.readback-controlTimeline.apply,controlTimeline.expiry-controlTimeline.readback,resultsAt-controlTimeline.expiry]){
    assert.ok(span/playbackSpeed>=1,'apply, readback and recovery each need at least one second');
  }
  // Each label is checked in the chapter that shows it: topology, detection, retrieval and audit.
  for(const [time,label] of [...['正常使用者','異常來源','核心交換器','策略閘道','應用服務','IDS'].map(l=>[9,l]),...['CTBM','PBCNN','校準＋OOF Gate'].map(l=>[24,l]),[35,'Top-5'],[41,'AI Judge'],[47.5,'規則生效'],[51.5,'到期回復']]){
    const document = new JSDOM(frameSvg(time), {contentType:'image/svg+xml'}).window.document;
    const node = [...document.querySelectorAll('text')].find(text=>text.textContent===label);
    assert.ok(node, `missing label: ${label}`);
    assert.equal(node.getAttribute('text-anchor'),'middle',`label must be explicitly centered: ${label}`);
  }
  for (const t of [...chapters.map(c => c.at + 1), 59.9]) {
    const source = frameSvg(t);
    assert.equal(source, frameSvg(t), 'frames must be deterministic');
    const document = new JSDOM(source, {contentType: 'image/svg+xml'}).window.document;
    assert.equal(document.querySelector('parsererror'), null);
    assert.ok(document.querySelector('svg'));
    assert.equal(document.querySelector('svg > rect').getAttribute('fill'), palette.gray, 'film chapters use the light canvas');
    assert.ok(!source.includes('NaN'));
  }
  console.log('Media smoke: deterministic, valid SVG across all chapters');
})();
