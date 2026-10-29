"""Fresh local LLM calls for three paired input arms plus two rule baselines."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
import time

from common import ROOT,ARMS,PROMPT,load_data,retrieve,payload,rule,summarize,sha,digest
from settings import optional_asset_path,asset_path
from provenance import runtime_assets,identifier,code_revision
from judge_response import parse_judge_response


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    sys.path.insert(0,str(optional_asset_path('judge_packages_dir',ROOT/'runtime/judge_packages')))
    bank,events=load_data()
    protocol={'version':1,'arms':ARMS,'cases':len(events),'seed':42,'batch_size':4,'max_new_tokens':112,'do_sample':False,
        'prompt':PROMPT,'prompt_sha256':digest(PROMPT),'source_revision':code_revision(),'asset_revision':identifier(runtime_assets()),
        'query_sha256':sha(ROOT/'evidence/fresh17/events.json'),'bank_sha256':sha(ROOT/'evidence/fresh17/train_bank.npz'),
        'experiment_sources':{name:sha(ROOT/'experiments'/name) for name in ('common.py','ablation.py')},
        'guard_scope':'All arms use the same original 529D evidence in the final Guard. This isolates auditor input, not removal of all retrieval from the production pipeline.',
        'prompt_scope':'One common optional-evidence experimental prompt across all LLM arms; distinct from the historical production prompt. Production saved replies are never reused.'}
    protocol=json.loads(json.dumps(protocol))
    if args.output.exists():
        if not args.resume or json.loads((args.output/'protocol.json').read_text(encoding='utf-8'))!=protocol:raise ValueError('resume_protocol_mismatch')
    else:
        args.output.mkdir(parents=True)
        (args.output/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf-8')
    production={e['event_id']:retrieve(bank,e,529) for e in events}
    for e in events:
        if [r['case_id'] for r in production[e['event_id']]]!=[r['case_id'] for r in e['evidence']]:raise ValueError('baseline_ranking_drift')
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM
    if not torch.cuda.is_available():raise RuntimeError('CUDA required')
    torch.set_num_threads(4);torch.manual_seed(42)
    model_path=asset_path('llama_model_dir')
    tokenizer=AutoTokenizer.from_pretrained(str(model_path),local_files_only=True)
    tokenizer.pad_token=tokenizer.eos_token;tokenizer.padding_side='left'
    model=AutoModelForCausalLM.from_pretrained(str(model_path),torch_dtype=torch.float16,local_files_only=True,attn_implementation='sdpa').to('cuda').eval()
    summary={}
    for arm in ARMS:
        path=args.output/(arm+'.jsonl')
        existing={}
        if path.exists():
            for line in path.read_text(encoding='utf-8').splitlines():
                r=json.loads(line)
                if r['event_id'] in existing or r['protocol_sha256']!=digest(protocol):raise ValueError('invalid_existing_record')
                existing[r['event_id']]=r
        pending=[]
        for e in events:
            neighbours=[] if arm in ('llm_none','confidence_rule') else retrieve(bank,e,512 if arm=='llm_512' else 529)
            data=payload(e,neighbours);binding=digest({'event_id':e['event_id'],'payload':data,'protocol':digest(protocol),'arm':arm})
            if e['event_id'] in existing:
                if existing[e['event_id']]['input_sha256']!=binding:raise ValueError('resumed_input_mismatch')
            else:pending.append((e,data,binding))
        with path.open('a',encoding='utf-8') as stream:
            for start in range(0,len(pending),4):
                chunk=pending[start:start+4]
                if arm.startswith('llm_'):
                    prompts=[tokenizer.apply_chat_template([{'role':'system','content':PROMPT},{'role':'user','content':json.dumps(data,ensure_ascii=False)}],tokenize=False,add_generation_prompt=True) for _,data,_ in chunk]
                    tokens=tokenizer(prompts,padding=True,return_tensors='pt').to('cuda')
                    torch.cuda.synchronize();began=time.perf_counter()
                    with torch.inference_mode():
                        output=model.generate(**tokens,max_new_tokens=112,do_sample=False,temperature=None,top_p=None,pad_token_id=tokenizer.eos_token_id,
                            eos_token_id=[tokenizer.eos_token_id,tokenizer.convert_tokens_to_ids('<|eot_id|>')])
                    torch.cuda.synchronize();elapsed=(time.perf_counter()-began)*1000
                    raw=tokenizer.batch_decode(output[:,tokens.input_ids.shape[1]:],skip_special_tokens=True)
                else:raw=['']*len(chunk);elapsed=None
                for (e,data,binding),text in zip(chunk,raw):
                    valid=True
                    if arm.startswith('llm_'):
                        try:value=parse_judge_response(text)
                        except ValueError:value={'assessment':'uncertain','reason':'Invalid response; no authorization.'};valid=False
                    else:value={'assessment':rule(e,None if arm=='confidence_rule' else production[e['event_id']]),'reason':'Predeclared deterministic baseline'}
                    row={'event_id':e['event_id'],'arm':arm,'payload':data,'input_sha256':binding,'protocol_sha256':digest(protocol),
                        **value,'valid_json':valid,'raw_response':text,'llm_executed':arm.startswith('llm_'),'batch_ms':elapsed,'batch_size':len(chunk)}
                    stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush();existing[e['event_id']]=row
                if start%40==0:print(arm,start+len(chunk),'/',len(pending),flush=True)
        ordered=[existing[e['event_id']] for e in events]
        summary[arm]={**summarize(events,[r['assessment'] for r in ordered],production),
            'fresh_llm_calls':sum(r['llm_executed'] for r in ordered),'valid_json_count':sum(r['valid_json'] for r in ordered)}
        print('ARM_DONE',arm,json.dumps(summary[arm]),flush=True)
    result={'status':'passed','created_utc':datetime.now(timezone.utc).isoformat(),'protocol':protocol,'arms':summary,
        'raw_record_sha256':{arm:sha(args.output/(arm+'.jsonl')) for arm in ARMS},
        'scope':'Paired saved detector inputs and fresh local LLM audits. No detector retraining, no ground truth in prompts and no network actions. Support precision must be interpreted alongside coverage.'}
    (args.output/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ABLATION_COMPLETE',flush=True)


if __name__=='__main__':main()
