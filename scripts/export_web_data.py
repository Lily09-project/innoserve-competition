"""Build the private browser payload from verified local experiment artifacts."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "app"))
from pipeline import LABELS


def read(path):return json.loads(path.read_text(encoding="utf-8"))


def main():
    fresh=ROOT / "evidence/fresh17"
    events=[]
    for event in read(fresh / "events.json"):
        events.append({k:v for k,v in event.items() if k not in {"embedding","model_sha256"}})
    paired=read(ROOT / "sources/paper_code/results/llm_full1830/three_way_summary.json")
    comparison=[]
    for key,name in [("no_rag","無檢索"),("original_fine11_fenet_rag","原始檢索"),("head_augmented_fine11_embedding_rag","改良檢索")]:
        value=paired["conditions"][key]
        comparison.append({"name":name,"error_interception":value["operational_safety"]["pbcnn_error_detection_rate"]})
    summary={"labels":LABELS,"detection":read(ROOT / "results/detection_17class.json"),
             "fresh_retrieval":read(fresh / "summary.json"),"local_judge":read(fresh / "judge_summary.json"),
             "judge_comparison":comparison,"network":None,"faults":None}
    framework=ROOT / "results/framework_validation.json"
    if framework.exists():summary["framework_validation"]=read(framework)
    (ROOT / "web/data.js").write_text("window.FINAL_DATA="+json.dumps({"summary":summary,"events":events},ensure_ascii=False,allow_nan=False)+";\n",encoding="utf-8")
    print("Private web/data.js generated for",len(events),"events.")


if __name__=="__main__":main()
