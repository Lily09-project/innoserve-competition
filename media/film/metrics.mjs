/** Refuse stale source data before rendering any labelled result frame. */
import fs from 'node:fs';
import crypto from 'node:crypto';
const snapshot=JSON.parse(fs.readFileSync(new URL('./metrics.json',import.meta.url),'utf8'));
const required=['detection_17class.json','retrieval_17class.json','local_judge_17class.json','framework_validation.json'];
if(snapshot.schema_version!==1 || Object.keys(snapshot.sources||{}).sort().join('|')!==required.map(n=>'results/'+n).sort().join('|'))throw Error('Invalid media metric source list');
for(const [name,expected] of Object.entries(snapshot.sources)){
 const content=fs.readFileSync(new URL('../../'+name,import.meta.url),'utf8').replace(/\r\n/g,'\n');
 if(crypto.createHash('sha256').update(content).digest('hex')!==expected)throw Error('Media metrics are stale; run python scripts/media_results.py');
}
export const metrics=Object.freeze(snapshot.values);
export const percent=value=>(value*100).toFixed(2)+'%';
export const count=value=>value.toLocaleString('en-US');
