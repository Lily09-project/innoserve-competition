"""Synthesize the film voiceover from media/film/narration.json and fit each line to its chapter window.

Needs edge-tts and FFMPEG_BINARY; the resulting media/film/narration.m4a is committed so film
rendering itself stays offline.
"""
import asyncio
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / 'media/film/narration.json'
OUTPUT = ROOT / 'media/film/narration.m4a'
MAX_TEMPO = 1.3


def seconds(ffmpeg, path):
    probe = subprocess.run([ffmpeg, '-hide_banner', '-i', str(path)], capture_output=True, text=True, encoding='utf-8')
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', probe.stderr).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


async def synthesize(spec, folder):
    import edge_tts
    paths = []
    for index, line in enumerate(spec['lines']):
        path = Path(folder) / f'line-{index}.mp3'
        await edge_tts.Communicate(line['text'], spec['voice'], rate=spec['rate']).save(str(path))
        paths.append(path)
    return paths


def trim(ffmpeg, paths):
    # The service pads each clip with silence; strip both ends so windows measure speech only.
    edge = 'silenceremove=start_periods=1:start_threshold=-45dB'
    trimmed = []
    for path in paths:
        target = path.with_suffix('.wav')
        subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(path), '-af', f'{edge},areverse,{edge},areverse', str(target)], check=True)
        trimmed.append(target)
    return trimmed


def build():
    ffmpeg = os.environ.get('FFMPEG_BINARY')
    if not ffmpeg:
        raise SystemExit('Set FFMPEG_BINARY to installed encoder')
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    lines, total = spec['lines'], spec['seconds']
    with tempfile.TemporaryDirectory() as folder:
        paths = trim(ffmpeg, asyncio.run(synthesize(spec, folder)))
        filters, report = [], []
        for index, (line, path) in enumerate(zip(lines, paths)):
            end = lines[index + 1]['at'] - .1 if index + 1 < len(lines) else total - .3
            length = seconds(ffmpeg, path)
            tempo = max(1.0, length / (end - line['at']))
            if tempo > MAX_TEMPO:
                raise SystemExit(f'Line too long for its chapter window: {line["text"]} ({length:.2f}s)')
            filters.append(f'[{index}:a]atempo={tempo:.4f},adelay={round(line["at"] * 1000)}:all=1[v{index}]')
            report.append({'chapter': line['chapter'], 'start': line['at'], 'end': round(line['at'] + length / tempo, 2), 'tempo': round(tempo, 3)})
        mix = ''.join(f'[v{k}]' for k in range(len(lines)))
        graph = ';'.join(filters) + f';{mix}amix=inputs={len(lines)}:normalize=0,apad,atrim=0:{total},loudnorm=I=-16:TP=-1.5[out]'
        command = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y']
        for path in paths:
            command += ['-i', str(path)]
        command += ['-filter_complex', graph, '-map', '[out]', '-ar', '48000', '-ac', '1', '-c:a', 'aac', '-b:a', '128k', str(OUTPUT)]
        subprocess.run(command, check=True)
    print(json.dumps({'output': OUTPUT.relative_to(ROOT).as_posix(), 'voice': spec['voice'], 'seconds': round(seconds(ffmpeg, OUTPUT), 3), 'lines': report}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    build()
