"""Three fresh Python processes; direct full-pipeline latency, no HTTP overhead."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))


def worker(output):
    began = time.perf_counter()
    from live_engine import LiveEngine
    import numpy as np
    engine = LiveEngine(lambda _: None)
    initialized = time.perf_counter()
    events = json.loads((ROOT / 'evidence/fresh17/events.json').read_text(encoding='utf-8'))
    chosen = [next(e for e in events if e['event_id'] == key) for key in engine.index]
    if len(chosen) != 17:
        raise ValueError('expected_17_real_inputs')
    engine.torch.cuda.synchronize()
    first = engine.infer(chosen[0], lambda _: None)
    engine.torch.cuda.synchronize()
    first_finished = time.perf_counter()
    rows = []
    engine.torch.cuda.reset_peak_memory_stats()
    for index in range(102):
        event = chosen[index % 17]
        engine.torch.cuda.synchronize()
        started = time.perf_counter()
        result = engine.infer(event, lambda _: None)
        engine.torch.cuda.synchronize()
        rows.append({'event_id': event['event_id'], 'elapsed_ms': (time.perf_counter() - started) * 1000,
                     'timings': result['timings'], 'llm_valid_pipeline_result': bool(result['result']['judge']),
                     'classification_matches_saved': result['prediction'] == event['prediction']})
    values = [r['elapsed_ms'] for r in rows]
    report = {'initialization_seconds_from_worker_entry': initialized - began,
              'first_inference_ms': (first_finished - initialized) * 1000,
              'first_prediction_matches_saved': first['prediction'] == chosen[0]['prediction'],
              'warm': rows, 'warm_calls': len(rows), 'unique_inputs': 17,
              'warm_p50_ms': float(np.percentile(values, 50)), 'warm_p95_ms': float(np.percentile(values, 95)),
              'warm_min_ms': min(values), 'warm_max_ms': max(values),
              'serial_calls_per_second': len(values) / (sum(values) / 1000),
              'torch_peak_allocated_bytes': engine.torch.cuda.max_memory_allocated(),
              'source_revision': __import__('provenance').code_revision(),
              'asset_revision': engine.asset_revision}
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('latency_output_exists')
    if args.worker:
        worker(args.output)
        return
    args.output.mkdir(parents=True)
    runs = []
    for trial in range(3):
        path = args.output / f'process-{trial + 1}.json'
        started = time.perf_counter()
        subprocess.run([sys.executable, '-X', 'utf8', str(Path(__file__).resolve()), '--worker', '--output', str(path)], check=True)
        runs.append({'trial': trial + 1, 'process_total_seconds': time.perf_counter() - started, **json.loads(path.read_text(encoding='utf-8'))})
        print('LATENCY_PROCESS_COMPLETE', trial + 1, flush=True)
    summary = {'status': 'completed', 'runs': runs,
               'scope': '3 fresh Python processes, each loads models then 1 first inference and 102 serial full-pipeline calls over 17 repeated genuine prepared inputs. OS filesystem cache not cleared. Direct LiveEngine includes output persistence, excludes HTTP/job polling and network enforcement. Repeats are latency samples, not additional accuracy cases. No concurrent-load capacity claim.'}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
