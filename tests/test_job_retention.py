"""Bound job history without deleting in-flight work or unrelated event receipts."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from server import prune_jobs


class JobRetentionTests(unittest.TestCase):
    def test_active_jobs_are_never_evicted(self):
        jobs={'active':{'state':'running'},'expired':{'state':'done','finished_at':0}}
        prune_jobs(jobs,100,10,1)
        self.assertEqual(jobs,{'active':{'state':'running'}})

    def test_keep_newest_finished_work_including_errors(self):
        jobs={str(i):{'state':'done' if i%2 else 'error','finished_at':i} for i in range(5)}
        prune_jobs(jobs,5,100,2)
        self.assertEqual(set(jobs),{'3','4'})

    def test_expiry_boundary_and_separate_receipts(self):
        receipts={'event':{'execution_id':'preserved'}}
        jobs={'old':{'state':'done','finished_at':90},'new':{'state':'done','finished_at':91}}
        prune_jobs(jobs,100,10,10)
        self.assertEqual(set(jobs),{'new'})
        self.assertEqual(receipts,{'event':{'execution_id':'preserved'}})
