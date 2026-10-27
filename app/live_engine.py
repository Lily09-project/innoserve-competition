"""Live local inference for 17 genuine, preprocessed demonstration inputs."""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
ROOT=Path(__file__).resolve().parents[1]
from settings import optional_asset_path
sys.path.insert(0,str(optional_asset_path("judge_packages_dir",ROOT / "runtime/judge_packages")))
sys.path.insert(0,str(ROOT / "scripts"))
os.environ["HF_HUB_OFFLINE"]="1"
os.environ["TRANSFORMERS_OFFLINE"]="1"
from pipeline import TrainOnlyBank, task_vector, run_event, digest


class LiveEngine:
    def __init__(self,progress):
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        from rebuild_retrieval import model_module,load_gate,REF,MODEL_ROOT,sha
        from run_local_judge import MODEL,PROMPT,payload_for
        self.torch=torch
        self.prompt=PROMPT
        self.payload_for=payload_for
        self.model_revision=MODEL.name
        self.device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
        torch.set_num_threads(4)
        progress("核對偵測權重、案例庫與類別版本")
        manifest=json.loads((ROOT / "evidence/fresh17/train_bank_manifest.json").read_text(encoding="utf-8"))
        model_hashes={name:sha(MODEL_ROOT / name / "best_model.pt") for name in ["CTBM_Full","PBCNN_M1","PBCNN_M2"]}
        if model_hashes!=manifest["model_hashes"] or digest(model_hashes)!=manifest["model_sha256"]:
            raise ValueError("live_checkpoint_bank_hash_mismatch")
        self.bank=TrainOnlyBank.load(ROOT / "evidence/fresh17/train_bank.npz",ROOT / "evidence/fresh17/train_bank_manifest.json")
        progress("載入17類偵測模型與Gate")
        c=model_module(REF / "runtime_sources/ctbm_full_none_real_only_seed_42.py","live_ctbm")
        b=model_module(REF / "runtime_sources/SMOTE_校準式類別感知Gate動態融合訓練_nofilm.py","live_pbcnn")
        self.pbcnn=b
        checkpoints={name:torch.load(MODEL_ROOT / name / "best_model.pt",map_location="cpu",weights_only=False)
                     for name in ["CTBM_Full","PBCNN_M1","PBCNN_M2"]}
        ck=checkpoints["CTBM_Full"]
        self.models={"CTBM_Full":c.build_model_for_stage("rgb_time_heat",17,ck["hparams"])}
        for name,n,cls in [("PBCNN_M1",2,b.PBCNNM1Classifier),("PBCNN_M2",16,b.PBCNNM2Classifier)]:
            hp=checkpoints[name]["hparams"]
            self.models[name]=cls(n,hp["h_dim"],hp["dropout"])
        for name,model in self.models.items():
            model.load_state_dict(checkpoints[name]["model_state_dict"],strict=True)
            model.to(self.device).eval()
        self.threshold=checkpoints["PBCNN_M1"]["hparams"].get("m1_attack_threshold",.5)
        self.gate=load_gate()
        progress("載入本機Llama 3 8B與案例庫")
        self.tokenizer=AutoTokenizer.from_pretrained(str(MODEL),local_files_only=True)
        self.tokenizer.pad_token=self.tokenizer.eos_token
        self.llm=AutoModelForCausalLM.from_pretrained(str(MODEL),torch_dtype=torch.float16,
                   local_files_only=True,attn_implementation="sdpa").to(self.device).eval()
        with np.load(ROOT / "evidence/fresh17/live_inputs_private.npz",allow_pickle=False) as inputs:
            self.inputs={k:inputs[k].copy() for k in inputs.files}
        self.index={key:i for i,key in enumerate(self.inputs["event_ids"].tolist())}
        progress("模型預載完成")

    def infer(self,event,progress):
        torch=self.torch
        if event["model_sha256"]!=self.bank.model_sha256 or event["representation_id"]!=self.bank.representation_id:
            raise ValueError("live_event_model_provenance_mismatch")
        if event["event_id"] not in self.index: raise ValueError("live_input_not_available")
        i=self.index[event["event_id"]]
        def t(key):return torch.from_numpy(self.inputs[key][i:i+1]).to(self.device)
        progress("即時執行CTBM、PBCNN與OOF Gate")
        started=time.perf_counter()
        with torch.inference_mode():
            c=self.models["CTBM_Full"](x_a=t("temporal"),x_rgb=t("content"),mask_rgb=t("mask"),direction_ids=t("directions"))
            m1=self.models["PBCNN_M1"](t("bytes"),mask_a=t("byte_mask"))
            m2=self.models["PBCNN_M2"](t("bytes"),mask_a=t("byte_mask"))
            pp,_=self.pbcnn.hierarchical_pbcnn_distribution(m1["logits"],m2["logits"],torch.softmax(m1["logits"],1)[:,1]>=self.threshold)
            cp=torch.softmax(c["logits"],1).cpu().numpy()
            pp=pp.cpu().numpy()
            embed=c["z_B"].cpu().numpy()[0]
        gp=self.gate(cp,pp)[0]
        detector_ms=(time.perf_counter()-started)*1000
        fresh={**event,"execution_id":uuid.uuid4().hex,"policy_ttl_seconds":30,"prediction":int(gp.argmax()),"confidence":float(gp.max()),"probabilities":gp.tolist(),
               "embedding":embed.tolist(),"pred_ctbm":int(cp.argmax()),"pred_pbcnn":int(pp.argmax()),"mode":"live_checkpoint_inference"}
        progress("以529維任務向量重新查詢Top-5訓練案例")
        began=time.perf_counter()
        fresh["evidence"]=self.bank.retrieve(task_vector(embed,gp),fresh["event_id"],fresh["representation_id"],fresh["model_sha256"])
        retrieval_ms=(time.perf_counter()-began)*1000
        progress("本機Llama即時產生稽核回覆")
        payload=self.payload_for(fresh)
        prompt=self.tokenizer.apply_chat_template([{"role":"system","content":self.prompt},
                 {"role":"user","content":json.dumps(payload,ensure_ascii=False)}],tokenize=False,add_generation_prompt=True)
        tokens=self.tokenizer(prompt,return_tensors="pt").to(self.device)
        began=time.perf_counter()
        with torch.inference_mode():
            generated=self.llm.generate(**tokens,max_new_tokens=112,do_sample=False,temperature=None,top_p=None,
                       pad_token_id=self.tokenizer.eos_token_id,
                       eos_token_id=[self.tokenizer.eos_token_id,self.tokenizer.convert_tokens_to_ids("<|eot_id|>")])
        raw=self.tokenizer.decode(generated[0,tokens.input_ids.shape[1]:],skip_special_tokens=True)
        llm_ms=(time.perf_counter()-began)*1000
        valid=False
        try:
            value=json.loads(re.search(r"\{.*?\}",raw,re.S).group(0))
            if value.get("assessment") not in {"support","review","uncertain"} or not isinstance(value.get("reason"),str):raise ValueError()
            valid=True
        except Exception:value={"assessment":"uncertain","reason":"Invalid model response; manual review required."}
        record={"input_sha256":digest({"event_id":fresh["event_id"],"prediction":fresh["prediction"],"evidence":fresh["evidence"]}),
                "assessment":value["assessment"],"reason":value["reason"],"model":"Meta-Llama-3-8B-Instruct",
                "prompt_sha256":hashlib.sha256(self.prompt.encode()).hexdigest(),"store":False,
                "classification_changed":False,"model_revision":self.model_revision,"raw_response":raw,"valid_json":valid,"payload":payload,
                "execution_mode":"live_local_llm_inference"}
        progress("策略檢核與保存事件紀錄")
        result=run_event(fresh,self.bank,record)
        fresh["result"]=result
        fresh["timings"]={"detector_ms":detector_ms,"retrieval_ms":retrieval_ms,"fresh_llm_ms":llm_ms}
        fresh["execution_mode"]="live_local_models"
        run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        private=ROOT / "evidence/live_runs"
        private.mkdir(exist_ok=True)
        (private / (run_id+".json")).write_text(json.dumps({"event":fresh,"judge_record":record},ensure_ascii=False,indent=2),encoding="utf-8")
        return {k:v for k,v in fresh.items() if k not in {"embedding","model_sha256"}}
