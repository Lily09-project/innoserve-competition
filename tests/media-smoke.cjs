const assert = require('node:assert/strict');
(async () => {
  const {frameSvg, duration, chapters} = await import('../media/film/scene.mjs');
  const {JSDOM} = require('jsdom');
  assert.equal(duration, 60);
  for (const t of [...chapters.map(c => c.at + 1), 59.9]) {
    const source = frameSvg(t);
    assert.equal(source, frameSvg(t), 'frames must be deterministic');
    const document = new JSDOM(source, {contentType: 'image/svg+xml'}).window.document;
    assert.equal(document.querySelector('parsererror'), null);
    assert.ok(document.querySelector('svg'));
    assert.ok(!source.includes('NaN'));
  }
  console.log('Media smoke: deterministic, valid SVG across all chapters');
})();
