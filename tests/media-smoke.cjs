const assert = require('node:assert/strict');
(async () => {
  const {frameSvg, duration, chapters,playbackSpeed,presentationDuration,maxDuration} = await import('../media/film/scene.mjs');
  const {JSDOM} = require('jsdom');
  assert.equal(duration, 60);
  assert.equal(chapters.at(-1).title,'展示結束');
  assert.ok(frameSvg(59.9).includes('展示結束'));
  assert.ok(frameSvg(59.9).includes('DFKai-SB'));
  assert.ok(frameSvg(59.9).includes('Times New Roman'));
  assert.ok(playbackSpeed>=1.5);
  assert.ok(presentationDuration<=maxDuration && maxDuration<=40);
  assert.ok(frameSvg(24).includes('#FDB338'), 'active states use the supplied gold');
  assert.ok(frameSvg(24).includes('#092B42'), 'gold highlights use dark navy labels');
  for (const t of [...chapters.map(c => c.at + 1), 59.9]) {
    const source = frameSvg(t);
    assert.equal(source, frameSvg(t), 'frames must be deterministic');
    const document = new JSDOM(source, {contentType: 'image/svg+xml'}).window.document;
    assert.equal(document.querySelector('parsererror'), null);
    assert.ok(document.querySelector('svg'));
    assert.ok(['#FFFFFF','#F0F2F3'].includes(document.querySelector('svg > rect').getAttribute('fill')), 'film chapters must use light canvas');
    assert.ok(!source.includes('NaN'));
  }
  console.log('Media smoke: deterministic, valid SVG across all chapters');
})();
