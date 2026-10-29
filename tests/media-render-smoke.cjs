/** Compile every chapter using repository dependencies, with no private runtime. */
const assert = require('node:assert/strict');
const sharp = require('sharp');
(async () => {
  const {frameSvg,chapters} = await import('../media/film/scene.mjs');
  for(const chapter of chapters){
    const {data,info}=await sharp(Buffer.from(frameSvg(chapter.at+1))).png().toBuffer({resolveWithObject:true});
    assert.equal(info.width,1280);assert.equal(info.height,720);
    assert.ok(data.length>10000,`empty chapter: ${chapter.title}`);
  }
  console.log('Media render smoke: nine chapters compiled using project sharp');
})();
