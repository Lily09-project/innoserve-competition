/** Render code-native vector icons; original bitmap artwork is preserved. */
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const require=createRequire(process.env.RENDER_NODE_MODULES+'/package.json');
const sharp=require('sharp');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const palette=JSON.parse(fs.readFileSync(path.join(root,'design-system/palette.json'),'utf8'));
const icons=JSON.parse(fs.readFileSync(path.join(root,'design-system/icons.json'),'utf8'));
for(const [index,name] of ['network','model','retrieval','shield'].entries()){
  const body=icons[name].replace(/\{\{(\w+)\}\}/g,(_,key)=>palette[key]);
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 64 64">${body}</svg>`;
  const base=path.join(root,`deliverables/source/flat-icon-${index+1}`);
  fs.writeFileSync(base+'.svg',svg);
  await sharp(Buffer.from(svg)).png().toFile(base+'.png');
}
console.log('Four shared flat vector icons and transparent PNGs generated.');
