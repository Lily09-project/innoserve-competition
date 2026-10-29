/** Generate source-coordinate alignment guides and verify centered film labels. */
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {chapters,frameSvg} from '../../media/film/scene.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const require=createRequire(process.env.RENDER_NODE_MODULES+'/package.json');
const sharp=require('sharp');
const folder=path.join(root,process.argv[2]||'validation/alignment-20261029');
fs.mkdirSync(folder,{recursive:true});
let textCount=0,centerChecks=0;
for(let index=0;index<chapters.length;index++){
 const svg=frameSvg(chapters[index].at+1);
 let guides='';
 for(const match of svg.matchAll(/<text x="([^"]+)" y="([^"]+)" text-anchor="([^"]+)" font-size="([^"]+)"[^>]*>(.*?)<\/text>/g)){
  const [,x,y,anchor,size,content]=match;
  const color=anchor==='middle'?'#004FFF':'#008050';
  guides+=`<path d="M${x} ${+y-size}V${+y+8}" stroke="${color}" stroke-width="1"/>`;
  textCount++;
  const label=content.replace(/<[^>]+>/g,'');
  const expected={'正常使用者':110,'異常來源':110,'核心交換器':310,'策略閘道':515,'應用服務':715,'IDS':310,'Top-5':515,'AI Judge':715,'CTBM':930,'PBCNN':1120,'校準＋OOF Gate':1025,'規則生效':518,'到期回復':518}[label];
  if(expected!==undefined){
   if(anchor!=='middle'||Math.abs(+x-expected)>.01)throw new Error(`Misaligned: ${label}`);
   centerChecks++;
  }
 }
 await sharp(Buffer.from(svg.replace('</svg>',guides+'</svg>'))).resize(1920,1080).png().toFile(path.join(folder,`film-${String(index+1).padStart(2,'0')}-guides.png`));
}
const report={chapters:chapters.length,text_anchor_guides:textCount,explicit_center_checks:centerChecks,errors:[]};
fs.writeFileSync(path.join(folder,'film-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
