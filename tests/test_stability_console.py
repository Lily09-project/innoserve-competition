"""Disposable failure tests; these fixtures are never experimental evidence."""
import http.client
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from contract_fixtures import write_private_bundle, event_bundle, measurement
from server import create_server, source_revision
from network_safety import cleanup_owned, NetworkDeadline
from network_contract import build_network_scenario,validate_measurement
import showcase


class CleanupTests(unittest.TestCase):
    def test_normal_cleanup_is_measured(self):
        net=Mock();process=Mock();process.poll.side_effect=[None,0]
        host=Mock(waiting=True)
        host.monitor.side_effect=lambda **kwargs:setattr(host,'waiting',False)
        net.hosts=[host]
        report=cleanup_owned({'net':net,'process':process,'policy_started':True},Mock(),lambda _: {'iptables':''},lambda _:False)
        self.assertTrue(report['passed']);net.stop.assert_called_once();process.terminate.assert_called_once()
        host.sendInt.assert_called_once();self.assertTrue(report['commands_drained'])

    def test_reset_failure_still_stops_network_and_server(self):
        net=Mock();process=Mock();process.poll.return_value=0
        report=cleanup_owned({'net':net,'process':process,'policy_started':True},Mock(side_effect=RuntimeError()),Mock(),lambda _:False)
        self.assertFalse(report['passed']);self.assertTrue(report['server_stopped']);net.stop.assert_called_once()

    def test_hung_server_is_killed_and_waited(self):
        process=Mock();process.poll.side_effect=[None,-9]
        process.wait.side_effect=[subprocess.TimeoutExpired('fixture',5),None]
        report=cleanup_owned({'process':process},Mock(),Mock())
        self.assertTrue(report['passed']);process.kill.assert_called_once()

    def test_partial_start_and_residual_interfaces_are_distinguished(self):
        net=Mock();net.get.side_effect=KeyError('router never created')
        report=cleanup_owned({'net':net},Mock(),Mock(),lambda _:False)
        self.assertTrue(report['passed']);net.stop.assert_called_once()
        report=cleanup_owned({'net':net},Mock(),Mock(),lambda n:n=='s1')
        self.assertFalse(report['passed']);self.assertEqual(report['remaining_owned_links'],['s1'])

    def test_deadline_signals_raise_and_disable_repeated_interrupts(self):
        fake=Mock(SIGALRM=14,SIGTERM=15,SIGINT=2,SIG_IGN=1)
        with patch('network_safety.signal',fake):
            timer=NetworkDeadline(5)
            with timer:
                with self.assertRaises(TimeoutError):timer.interrupt(14,None)
                with self.assertRaises(InterruptedError):timer.interrupt(15,None)
            fake.alarm.assert_any_call(0)
        for seconds in (0,True,901):
            with self.assertRaises(ValueError):NetworkDeadline(seconds)

    def test_success_receipt_requires_cleanup_proof(self):
        _,events,_=event_bundle();scenario=build_network_scenario(events[1]);receipt=measurement(scenario)
        self.assertTrue(validate_measurement(scenario,receipt))
        receipt.pop('cleanup')
        with self.assertRaisesRegex(ValueError,'cleanup_not_verified'):validate_measurement(scenario,receipt)


class ServerRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='server-recovery-contract-')
        cls.root=Path(cls.temp.name);write_private_bundle(cls.root/'evidence/fresh17')
        cls.server=create_server(0,cls.root)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=5);cls.temp.cleanup()

    def request(self,path,payload=None):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            c.request('GET' if payload is None else 'POST',path,None if payload is None else json.dumps(payload),{'Content-Type':'application/json'})
            r=c.getresponse();return r.status,json.loads(r.read())
        finally:c.close()

    def wait(self,key):
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            status,value=self.request('/api/jobs/'+key)
            if value.get('state')!='running':return value
            time.sleep(.01)
        self.fail('fixture job did not finish')

    def test_load_failure_busy_inference_failure_and_retry(self):
        entered=threading.Event();release=threading.Event()
        class Engine:
            asset_revision='fixture'
            def infer(self,event,progress):raise RuntimeError('private diagnostic must not be public')
        def broken(progress):
            entered.set();release.wait(3);raise RuntimeError('private load path')
        module=types.SimpleNamespace(LiveEngine=broken)
        with patch.dict(sys.modules,{'live_engine':module}):
            _,job=self.request('/api/operate',{'action':'warmup'})
            self.assertTrue(entered.wait(2))
            self.assertEqual(self.request('/api/stop',{})[0],409)
            self.assertEqual(self.request('/api/operate',{'action':'warmup'})[0],409)
            release.set();failed=self.wait(job['job_id'])
            self.assertEqual(failed['error_code'],'model_load_failed')
            self.assertFalse(self.request('/api/status')[1]['model_ready'])
            module.LiveEngine=lambda progress:Engine()
            _,job=self.request('/api/operate',{'action':'warmup'})
            self.assertEqual(self.wait(job['job_id'])['state'],'done')
            _,job=self.request('/api/operate',{'action':'live','event_id':'query-1'})
            failed=self.wait(job['job_id'])
            self.assertEqual(failed['error_code'],'inference_failed')
            self.assertNotIn('private',json.dumps(failed))
            self.assertEqual(self.request('/api/status')[0],200)
            with patch('server.Path.write_text',side_effect=OSError('fixture disk full')):
                _,job=self.request('/api/operate',{'action':'live','event_id':'query-1'})
                failed=self.wait(job['job_id'])
                self.assertEqual(failed['state'],'error')
                self.assertFalse(failed['diagnostic_saved'])
            Engine.infer=lambda self,event,progress:event
            _,job=self.request('/api/operate',{'action':'live','event_id':'query-1'})
            self.assertEqual(self.wait(job['job_id'])['state'],'done')
            with patch('server.subprocess.run',side_effect=subprocess.TimeoutExpired('fixture wsl',1)):
                _,job=self.request('/api/operate',{'action':'network','event_id':'query-1','execution_id':'run-1'})
                failed=self.wait(job['job_id'])
                self.assertEqual(failed['error_code'],'network_timeout')
                self.assertNotIn('result',failed)
            self.assertIsNone(self.request('/api/status')[1]['active_job'])


class ConsoleTests(unittest.TestCase):
    def test_saved_mode_does_not_warmup_or_add_network(self):
        status={'live_event_options':[{'index':4,'prediction_label':'SSH-Bruteforce','saved_assessment':'support'}]}
        with patch.object(showcase,'ensure_service'),patch.object(showcase,'prepare') as warmup,patch.object(showcase,'request',return_value=status),patch.object(showcase.demo_walkthrough,'main',return_value=0) as walk:
            self.assertEqual(showcase.main(['--scenario','ssh','--mode','saved','--port','8877']),0)
            warmup.assert_not_called();self.assertNotIn('--network',walk.call_args.args[0]);self.assertIn('8877',walk.call_args.args[0])

    def test_review_selects_exact_option_and_missing_scenario_fails(self):
        rows=[{'index':1,'prediction_label':'Web-XSS','saved_assessment':'support'},{'index':6,'prediction_label':'Web-XSS','saved_assessment':'review'}]
        self.assertEqual(showcase.choose_event({'live_event_options':rows},'review')['index'],6)
        with self.assertRaises(ValueError):showcase.choose_event({'live_event_options':rows},'ssh')

    def test_existing_old_service_is_not_killed_or_replaced(self):
        with patch.object(showcase,'request',return_value={'product':'ai-security-demo.v3','source_revision':'old'}),patch.object(showcase.subprocess,'Popen') as launch:
            with self.assertRaisesRegex(RuntimeError,'outdated'):showcase.ensure_service(8765)
            launch.assert_not_called()

    def test_existing_current_service_reused(self):
        with patch.object(showcase,'request',return_value={'product':'ai-security-demo.v3','source_revision':source_revision()}):
            self.assertFalse(showcase.ensure_service(8765))
