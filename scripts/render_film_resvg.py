"""Render media/film/scene.mjs to MP4 without sharp: node emits SVG frames, resvg rasterizes, ffmpeg encodes."""
import json, subprocess, sys, resvg_py, imageio_ffmpeg
node, repo, out = sys.argv[1:4]
fps = 24
js = f"""import {{frameSvg,presentationDuration,playbackSpeed,maxDuration}} from 'file:///{repo}/media/film/scene.mjs';
if(presentationDuration>maxDuration||playbackSpeed<1.5)throw Error('Finals timing constraint');
const n=Math.round(presentationDuration*{fps});for(let f=0;f<n;f++)process.stdout.write(JSON.stringify(frameSvg(f/{fps}*playbackSpeed))+String.fromCharCode(10));"""
src = subprocess.Popen([node, '--input-type=module', '-e', js], stdout=subprocess.PIPE)
enc = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(fps), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
for k, ln in enumerate(src.stdout):
    enc.stdin.write(bytes(resvg_py.svg_to_bytes(svg_string=json.loads(ln), width=1920, height=1080, skip_system_fonts=True, font_files=['C:/Windows/Fonts/msjh.ttc','C:/Windows/Fonts/msjhbd.ttc','C:/Windows/Fonts/segoeui.ttf','C:/Windows/Fonts/segoeuib.ttf','C:/Windows/Fonts/CascadiaMono.ttf','C:/Windows/Fonts/consola.ttf','C:/Windows/Fonts/seguisym.ttf'], font_family='Microsoft JhengHei')))
    if k % 480 == 0: print('frame', k, flush=True)
enc.stdin.close(); enc.wait(); print('done', out)
