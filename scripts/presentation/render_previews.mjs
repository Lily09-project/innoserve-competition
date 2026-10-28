/** Regenerate reference previews from the current native and movie outputs. */
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const require=createRequire(process.env.RENDER_NODE_MODULES+'/package.json');
const sharp=require('sharp');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const powerpointFolder=process.argv[2]||'validation/palette-powerpoint';
const filmFolder=process.argv[3]||'validation/palette-film-20261028';
const source=path.join(root,'deliverables/source');
let architecture=fs.readFileSync(path.join(source,'architecture.svg'),'utf8');
architecture=architecture.replace(/href="(icon-\d\.png)"/g,(_,name)=>`href="data:image/png;base64,${fs.readFileSync(path.join(source,name)).toString('base64')}"`);
await sharp(Buffer.from(architecture)).resize(2560,1072).png().toFile(path.join(root,'deliverables/figures/fig_architecture.png'));
async function contact(files,columns,tileWidth,tileHeight,target){
  const tiles=await Promise.all(files.map(async(file,i)=>({input:await sharp(file).resize(tileWidth,tileHeight,{fit:'contain',background:'#FFFFFF'}).png().toBuffer(),left:(i%columns)*tileWidth,top:Math.floor(i/columns)*tileHeight})));
  await sharp({create:{width:columns*tileWidth,height:Math.ceil(files.length/columns)*tileHeight,channels:3,background:'#FFFFFF'}}).composite(tiles).png().toFile(target);
}
await contact(Array.from({length:12},(_,i)=>path.join(root,powerpointFolder,`slide-${String(i+1).padStart(2,'0')}.png`)),3,640,360,path.join(root,'deliverables/figures/slides-preview.png'));
await contact(Array.from({length:9},(_,i)=>path.join(root,filmFolder,`chapter-${i+1}.png`)),3,640,360,path.join(root,'deliverables/figures/film-preview.png'));
console.log('Architecture, native slide and movie previews regenerated.');
