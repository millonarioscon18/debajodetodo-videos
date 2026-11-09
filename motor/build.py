#!/usr/bin/env python3
"""Motor v2 de Debajo de Todo.
Uso:  python3 build.py <carpeta_video>
La carpeta tiene: vo.mp3, music.mp3, clip.mp4 (gancho IA), img/*.png, sfx/*.mp3, words.json y config.json.

config.json:
{
  "out": "ducha.mp4",
  "segs":  [[inicio, fin, "fuente", "efecto", {opciones}], ...],
     efectos: clip | zoom_in | zoom_to (opc. fx,fy,z) | zoom_dark | punch (opc. fy) | pan_down (opc. cx) | pan_up | zoom_out
  "tags":  [[t0, t1, "TEXTO", y, "Tag"|"Big"], ...],
  "sfx":   [["sfx/x.mp3", t, volumen], ...],
  "fixes": {"palabra_mal": "palabra_bien"},  # opcional: correcciones de la transcripcion
  "key":   ["palabras", "clave"]
}
"""
import json, subprocess, os, sys

W, H, FPS = 1080, 1920, 30
FONTDIR = '/usr/share/fonts/truetype/google-fonts'

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)

def dur_of(f):
    return float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{f}'", shell=True))

def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def seg(i, a, b, src, kind, o):
    dur = b - a; n = round(dur * FPS); out = f'seg/s{i}.mp4'
    enc = f'-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r {FPS} -frames:v {n} -an'
    if kind == 'clip':
        f = dur / dur_of(src)
        run(f'ffmpeg -v error -y -i {src} -vf "setpts={f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}" {enc} {out}')
        return out
    if kind in ('pan_down', 'pan_up'):
        cx = o.get('cx', 0.5)
        # si la imagen es apaisada, recorta una franja vertical; si es vertical, la amplia un 25 %
        pre = (f"scale='if(gt(iw,ih),-2,{int(W*1.25)})':'if(gt(iw,ih),ih,-2)',"
               f"crop='min(iw,ih*0.45)':ih:'max(0,min(iw-min(iw,ih*0.45),iw*{cx}-min(iw,ih*0.45)/2))':0,scale={W}:-2:flags=lanczos")
        yexpr = f"(ih-{H})*min(t/{dur},1)" if kind == 'pan_down' else f"(ih-{H})*(1-min(t/{dur},1))"
        run(f'ffmpeg -v error -y -loop 1 -t {dur} -i {src} -vf "{pre},crop={W}:{H}:0:\'{yexpr}\',fps={FPS}" {enc} {out}')
        return out
    pre = f'scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2}'
    if kind == 'zoom_to':
        fx, fy, zz = o.get('fx', 0.5), o.get('fy', 0.5), o.get('z', 0.45)
        z = (f"zoompan=z='1+{zz}*on/{n}':x='(iw-iw/zoom)*{fx}':y='(ih-ih/zoom)*{fy}'"
             f":d={n}:s={W}x{H}:fps={FPS}")
    elif kind == 'zoom_dark':
        fy = o.get('fy', 0.42)
        z = (f"zoompan=z='1.05+0.6*on/{n}':x='iw/2-(iw/zoom/2)':y='ih*{fy}-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},"
             f"eq=brightness='-0.18*t/{dur}':eval=frame")
    elif kind == 'punch':
        fy = o.get('fy', 0.55)
        z = (f"zoompan=z='if(lt(on,6),1.35-0.05*on,1.05+0.12*(on-6)/{n})'"
             f":x='iw/2-(iw/zoom/2)+if(lt(on,12),18*sin(on*2.1),0)':y='ih*{fy}-(ih/zoom/2)+if(lt(on,12),14*cos(on*2.7),0)'"
             f":d={n}:s={W}x{H}:fps={FPS}")
    elif kind == 'zoom_out':
        z = f"zoompan=z='1.3-0.3*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS}"
    else:  # zoom_in
        z = f"zoompan=z='1+0.18*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS}"
    run(f'ffmpeg -v error -y -loop 1 -framerate {FPS} -t {dur} -i {src} -vf "{pre},{z}" {enc} {out}')
    return out

def build(folder):
    os.chdir(folder); os.makedirs('seg', exist_ok=True); os.makedirs('out', exist_ok=True)
    cfg = json.load(open('config.json'))
    TOTAL = round(dur_of('vo.mp3') + cfg.get('tail', 0.0), 2)
    segs = cfg['segs']; segs[-1][1] = TOTAL
    outs = [seg(i, *s[:4], s[4] if len(s) > 4 else {}) for i, s in enumerate(segs)]
    with open('seg/list.txt', 'w') as f:
        for o in outs: f.write(f"file '{os.path.basename(o)}'\n")
    run('ffmpeg -v error -y -f concat -safe 0 -i seg/list.txt -c copy seg/base.mp4')
    flash = '+'.join(f"between(t,{s[0]:.2f},{s[0]+0.10:.2f})" for s in segs[1:])

    # ---- subtitulos ----
    words = json.load(open('words.json'))
    fixes = cfg.get('fixes', {})
    txt = []; i = 0
    while i < len(words):
        a, b, w = words[i]
        if i + 1 < len(words) and f"{w} {words[i+1][2]}" in fixes:
            txt.append([a, words[i+1][1], fixes[f"{w} {words[i+1][2]}"]]); i += 2; continue
        txt.append([a, b, fixes.get(w, w)]); i += 1
    chunks, cur = [], []
    for wd in txt:
        cur.append(wd)
        if len(cur) == 3 or wd[2][-1] in '.,…:?!':
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    KEY = set(k.lower() for k in cfg.get('key', []))
    clean = lambda s: s.lower().strip('.,…:¿?¡!')
    ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: Cap,Poppins,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,2,60,60,560,1",
           "Style: Big,Poppins,150,&H0000D7FF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,9,4,5,40,40,0,1",
           "Style: Tag,Poppins,70,&H00FFFFFF,&H00FFFFFF,&H00141414,&H00000000,-1,0,0,0,100,100,0,0,3,18,0,5,40,40,0,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for ci, ch in enumerate(chunks):
        st = ch[0][0]; en = chunks[ci+1][0][0] if ci + 1 < len(chunks) else TOTAL
        en = min(en, ch[-1][1] + 0.6)
        for wi, (a, b, w) in enumerate(ch):
            s0 = st if wi == 0 else a
            e0 = ch[wi+1][0] if wi + 1 < len(ch) else en
            parts = []
            for wj, (_, _, w2) in enumerate(ch):
                u = w2.upper().strip('.,…:')
                if wj == wi:
                    col = '&H0000D7FF&' if clean(w2) in KEY else '&H0000FFFF&'
                    parts.append(r"{\c" + col + r"\fscx112\fscy112}" + u + r"{\c&HFFFFFF&\fscx100\fscy100}")
                else:
                    parts.append(u)
            pop = r"{\t(0,80,\fscx104\fscy104)\t(80,160,\fscx100\fscy100)}" if wi == 0 else ''
            ass.append(f"Dialogue: 1,{ts(s0)},{ts(e0)},Cap,,0,0,0,,{pop}{' '.join(parts)}")
    for t0, t1, text, y, style in cfg.get('tags', []):
        ass.append(f"Dialogue: 2,{ts(t0)},{ts(t1)},{style},,0,0,0,,"
                   + r"{\pos(540," + f"{y}" + r")\fscx20\fscy20\t(0,180,\fscx115\fscy115)\t(180,300,\fscx100\fscy100)\fad(0,150)}" + text)
    open('subs.ass', 'w').write('\n'.join(ass) + '\n')

    vf = (f"eq=contrast=1.05:saturation=1.12,"
          f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.85:t=fill:enable='{flash}',vignette=PI/5,"
          f"drawtext=fontfile={FONTDIR}/Poppins-Bold.ttf:text='DEBAJO DE TODO':fontsize=34:fontcolor=white@0.75:x=(w-tw)/2:y=110:shadowcolor=black@0.6:shadowx=2:shadowy=2,"
          f"ass=subs.ass:fontsdir={FONTDIR}")
    SFX = cfg.get('sfx', [])
    inputs = '-i vo.mp3 -i music.mp3 ' + ' '.join(f'-i {s[0]}' for s in SFX)
    fc = ["[1:a]highpass=f=70,asplit=2[vo][vosc]",
          f"[2:a]volume={cfg.get('music_vol', 0.55)},atrim=0:{TOTAL},afade=t=in:d=0.3[mus]",
          "[mus][vosc]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=300[musd]"]
    mix = ['[vo]', '[musd]']
    for k, (f, t, v) in enumerate(SFX):
        fc.append(f"[{k+3}:a]adelay={int(t*1000)}|{int(t*1000)},volume={v}[s{k}]"); mix.append(f'[s{k}]')
    fc.append(''.join(mix) + f"amix=inputs={len(mix)}:normalize=0,atrim=0:{TOTAL},loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    out = f"out/{cfg['out']}"
    run(f'ffmpeg -v error -y -i seg/base.mp4 {inputs} -filter_complex "[0:v]{vf}[v];' + ';'.join(fc)
        + f'" -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -r {FPS} '
        + f'-c:a aac -b:a 192k -t {TOTAL} -movflags +faststart {out}')
    print('OK', os.path.abspath(out), TOTAL, 's')

def words(folder):
    """Transcribe vo.mp3 con marcas de tiempo por palabra (faster-whisper, local, gratis)."""
    from faster_whisper import WhisperModel
    import soundfile as sf
    os.chdir(folder)
    run('ffmpeg -v error -y -i vo.mp3 -ac 1 -ar 16000 vo16.wav')
    a, _ = sf.read('vo16.wav', dtype='float32')
    segs, _ = WhisperModel('small', compute_type='int8').transcribe(a, language='es', word_timestamps=True)
    w = [[round(x.start, 2), round(x.end, 2), x.word.strip()] for s in segs for x in s.words]
    json.dump(w, open('words.json', 'w'), ensure_ascii=False)
    print(' '.join(f'{a}:{t}' for a, b, t in w))

if __name__ == '__main__':
    folder = os.path.abspath(sys.argv[-1])
    if sys.argv[1] == 'words': words(folder)
    else: build(folder)
