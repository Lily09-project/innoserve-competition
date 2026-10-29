/** Stale results stop rendering; a refreshed snapshot changes the displayed value. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'media-data-contract-'));
try{
 const names=['media/film/scene.mjs','media/film/metrics.mjs','media/film/metrics.json',
 'design-system/palette.json','design-system/typography.json','design-system/icons.json',
 'results/detection_17class.json','results/retrieval_17class.json','results/local_judge_17class.json','results/framework_validation.json'];
 for(const name of names){const target=path.join(temp,name);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(path.join(root,name),target);}
 const run=()=>spawnSync(process.execPath,['--input-type=module','-e',`import {frameSvg} from ${JSON.stringify(pathToFileURL(path.join(temp,'media/film/scene.mjs')).href)};console.log(frameSvg(54));`],{encoding:'utf8'});
 assert.equal(run().status,0);
 const result=path.join(temp,'results/retrieval_17class.json');
 const data=JSON.parse(fs.readFileSync(result,'utf8'));data.top5=.98;fs.writeFileSync(result,JSON.stringify(data));
 const stale=run();assert.notEqual(stale.status,0);assert.match(stale.stderr,/metrics are stale/);
 const snapshotPath=path.join(temp,'media/film/metrics.json');
 const snapshot=JSON.parse(fs.readFileSync(snapshotPath,'utf8'));
 snapshot.sources['results/retrieval_17class.json']=crypto.createHash('sha256').update(fs.readFileSync(result,'utf8').replace(/\r\n/g,'\n')).digest('hex');
 snapshot.values.top5=.98;fs.writeFileSync(snapshotPath,JSON.stringify(snapshot));
 const current=run();assert.equal(current.status,0);assert.ok(current.stdout.includes('98.00%'));assert.ok(!current.stdout.includes('97.62%'));
 console.log('Media data: stale snapshot rejected; updated test value rendered');
}finally{
 // The path is returned by mkdtemp inside os.tmpdir; remove only that owned fixture.
 if(path.dirname(temp)!==os.tmpdir()||!path.basename(temp).startsWith('media-data-contract-'))throw Error('Unsafe fixture cleanup');
 fs.rmSync(temp,{recursive:true,force:true});
}
