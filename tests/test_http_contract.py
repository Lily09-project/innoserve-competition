"""Local HTTP behavior with disposable synthetic assets, not model performance."""
import hashlib
import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "app"))
from pipeline import LABELS, task_vector, verify_ledger
from server import create_server


class HttpContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="innoserve-contract-")
        cls.root=Path(cls.temp.name)
        data=cls.root / "evidence/fresh17";data.mkdir(parents=True)
        web=cls.root / "web";web.mkdir()
        (web / "index.html").write_text("<h1>Disposable HTTP contract fixture</h1>",encoding="utf-8")
        p=np.eye(17)[7]
        bank=data / "train_bank.npz"
        np.savez(bank,vectors=np.tile(task_vector(np.ones(512),p),(5,1)),
            ids=np.array(list("abcde")),labels=np.array([7]*5),splits=np.array(["train"]*5))
        manifest={"npz_sha256":hashlib.sha256(bank.read_bytes()).hexdigest(),"label_order":LABELS,
            "representation_id":"fixture","model_sha256":"a"*64}
        (data / "train_bank_manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
        cls.event={"event_id":"query","prediction":7,"confidence":1.0,"probabilities":p.tolist(),
            "embedding":np.ones(512).tolist(),"representation_id":"fixture","model_sha256":"a"*64,
            "pred_ctbm":7,"pred_pbcnn":7,"validation_label":7,
            "execution_id":"must-not-leak-from-frozen-snapshot","timings":{"detector_ms":9},"network_receipt":{"old":True}}
        (data / "events.json").write_text(json.dumps([cls.event]),encoding="utf-8")
        np.savez(data / "live_inputs_private.npz",event_ids=np.array([],dtype="U1"))
        cls.server=create_server(0,cls.root)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=5);cls.temp.cleanup()

    def request(self,path,body=None,headers=None):
        client=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=5)
        try:
            client.request("GET" if body is None else "POST",path,body,
                {"Content-Type":"application/json",**(headers or {})})
            response=client.getresponse();payload=response.read()
            return response.status,payload
        finally:client.close()

    def test_non_object_json_is_rejected_and_service_survives(self):
        for body in (b"[]",b"null",b"42",b'"event"',b"{",b"\xff"):
            with self.subTest(body=body):self.assertEqual(self.request("/api/operate",body)[0],400)
        self.assertEqual(self.request("/api/status")[0],200)

    def test_invalid_stop_body_does_not_stop_service(self):
        self.assertEqual(self.request("/api/stop",b"[]")[0],400)
        self.assertEqual(self.request("/api/status")[0],200)

    def test_unknown_events_and_actions_rejected(self):
        for path,payload in (("/api/retrieve",{"event_id":"unknown"}),
            ("/api/retrieve",{"event_id":[]}),
            ("/api/operate",{"action":"arbitrary-command"}),
            ("/api/operate",{"action":"live","event_id":"query"}),
            ("/api/operate",{"action":"network","event_id":"query","execution_id":"old"})):
            with self.subTest(payload=payload):self.assertEqual(self.request(path,json.dumps(payload).encode())[0],400)

    def test_origin_type_and_size_enforced(self):
        self.assertEqual(self.request("/api/retrieve",b"{}",{"Origin":"https://untrusted.invalid"})[0],403)
        self.assertEqual(self.request("/api/retrieve",b"{}",{"Content-Type":"text/plain"})[0],415)
        self.assertEqual(self.request("/api/retrieve",b" "*2048)[0],400)

    def test_retrieval_returns_complete_frozen_snapshot(self):
        status,body=self.request("/api/retrieve",b'{"event_id":"query"}')
        self.assertEqual(status,200)
        result=json.loads(body);event=result["replay_event"]
        self.assertEqual(event["probabilities"],self.event["probabilities"])
        self.assertEqual(event["confidence"],1)
        self.assertEqual(event["result"]["prediction"],event["prediction"])
        self.assertEqual(event["evidence"],result["evidence"])
        self.assertEqual(event["execution_mode"],"saved_prediction_retrieval_recomputed")
        for key in ("embedding","model_sha256","execution_id","timings","network_receipt"):
            self.assertNotIn(key,event)

    def test_private_assets_not_served(self):
        self.assertEqual(self.request("/evidence/fresh17/events.json")[0],404)
        self.assertEqual(self.request("/../evidence/fresh17/events.json")[0],404)
        self.assertEqual(self.request("/api/jobs/unknown")[0],404)

    def test_export_preserves_canonical_numeric_format_and_ledger(self):
        status,body=self.request("/api/export",b'{"event_id":"query","mode":"saved_prediction_replay"}')
        self.assertEqual(status,200)
        self.assertIn(b'"confidence": 1.0',body)
        event=json.loads(body)
        self.assertTrue(verify_ledger(event["result"]["ledger"]))
        self.assertNotIn("embedding",event)
        self.assertNotIn("execution_id",event)
        self.assertEqual(self.request("/api/export",b'{"event_id":"query","mode":"live_local_models","execution_id":"old"}')[0],400)
        self.assertEqual(self.request("/api/export",b'{"event_id":"query","mode":"unknown"}')[0],400)


if __name__=="__main__":unittest.main()
