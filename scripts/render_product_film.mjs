/** Offline graphics rendering only: no browser automation or generative images. */
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {spawn,execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {frameSvg,duration,chapters} from '../web/film/scene.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(process.env.RENDER_NODE_MODULES+'/package.json');
const sharp=require('sharp');
const output=path.resolve(process.argv[2]||path.join(root,'validation/product_film'));
fs.mkdirSync(output,{recursive:true});
const fps=24,width=1920,height=1080;
const ffmpeg=process.env.FFMPEG_BINARY;if(!ffmpeg)throw Error('Set FFMPEG_BINARY to installed encoder');
const mode=process.argv.includes('--preview')?'preview':'full';
const sampleTimes=chapters.map((c,i)=>Math.min(duration-0.1,c.at+(c.card?3.5:8)));
for(let i=0;i<sampleTimes.length;i++)await sharp(Buffer.from(frameSvg(sampleTimes[i]))).resize(width,height).png().toFile(path.join(output,`chapter-${i+1}.png`));
if(mode==='preview'){console.log(JSON.stringify({preview_frames:sampleTimes.length,output}));process.exit(0)}
const file=path.join(output,'AI資安框架_系統展示影片_60秒.mp4');
if(fs.existsSync(file))throw Error('Output exists; choose a new output directory to retain previous release');
const encoder=spawn(ffmpeg,['-hide_banner','-loglevel','error','-f','image2pipe','-framerate',String(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',file],{stdio:['pipe','inherit','inherit'],windowsHide:true});
const exit=new Promise((resolve,reject)=>{encoder.on('error',reject);encoder.on('close',c=>c===0?resolve():reject(Error(`encoder exit ${c}`)))});
for(let f=0;f<duration*fps;f++){
 const png=await sharp(Buffer.from(frameSvg(f/fps))).resize(width,height).png({compressionLevel:1}).toBuffer();
 if(!encoder.stdin.write(png))await new Promise(resolve=>encoder.stdin.once('drain',resolve));
 if(f%(fps*15)===0)console.log(`Rendered ${f/fps}/${duration} seconds`);
}
encoder.stdin.end();await exit;
const analysis=execFileSync(ffmpeg,['-hide_banner','-i',file,'-f','null','-'],{encoding:'utf8',stdio:['ignore','pipe','pipe'],windowsHide:true});
fs.writeFileSync(path.join(output,'render.json'),JSON.stringify({file,duration_seconds:duration,fps,width,height,frames:duration*fps,has_audio:false,renderer:'shared frameSvg -> sharp -> ffmpeg',bytes:fs.statSync(file).size},null,2));
console.log(JSON.stringify({file,bytes:fs.statSync(file).size}));
