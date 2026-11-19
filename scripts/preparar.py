#!/usr/bin/env python3
"""Prepara uma gravação bruta pra edição Xavier.

    python3 preparar.py GRAVACAO.mov PASTA_DO_PROJETO [--modelo small] [--remover "12.4-18.9,300-305"]
                        [--pausa 0.35] [--sem-corte]

Faz, em ordem:
  1. transcreve palavra por palavra (Whisper, português)
  2. tira os trechos de --remover (take errado) e corta as pausas maiores que --pausa segundos
  3. gera o vídeo cortado na resolução original (assets/cortado.mp4) e uma cópia 1080p 60 pra prévia (assets/cam1080.mp4)
  4. refaz os tempos das palavras na linha do tempo cortada
  5. acha o rosto a cada 0,1 s (YuNet), a forma de onda e a folha de quadros
  6. monta PASTA/hf/ com o motor (lib.py, estilo.css, build.py de exemplo, hyperframes.json) e os sons

Saída em PASTA/hf/dados/: fala.words.json ([[início, fim, palavra]]), fala.txt, cuts.json, face.json, wave.json,
info.json e folha.jpg.
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


def run(args, **kw):
    r = subprocess.run(args, **kw)
    if r.returncode != 0:
        sys.exit(f"falhou: {' '.join(map(str, args[:6]))} …")
    return r


def probe(src):
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", src],
                         capture_output=True, text=True).stdout
    d = json.loads(out)
    st = d["streams"][0]
    a, b = st["r_frame_rate"].split("/")
    fps = float(a) / float(b)
    return int(st["width"]), int(st["height"]), fps, float(d["format"]["duration"])


def transcrever(wav, modelo):
    """[[início, fim, palavra]] com Whisper (faster-whisper se tiver, senão openai-whisper)."""
    try:
        from faster_whisper import WhisperModel
        m = WhisperModel(modelo, compute_type="int8")
        segs, _ = m.transcribe(wav, language="pt", word_timestamps=True, vad_filter=False)
        return [[round(w.start, 3), round(w.end, 3), w.word.strip()] for s in segs for w in (s.words or []) if w.word.strip()]
    except ImportError:
        import whisper
        m = whisper.load_model(modelo)
        r = m.transcribe(wav, language="pt", word_timestamps=True, fp16=False, condition_on_previous_text=False)
        return [[round(w["start"], 3), round(w["end"], 3), w["word"].strip()] for s in r["segments"] for w in s.get("words", []) if w["word"].strip()]


def faixas_para_manter(words, dur, pausa, remover):
    """trechos [a, b] do bruto que ficam: a fala, sem as pausas longas e sem o que foi removido."""
    def removido(t0, t1):
        return any(t0 < b and t1 > a for a, b in remover)
    ws = [w for w in words if not removido(w[0], w[1])]
    if not ws:
        sys.exit("nenhuma palavra encontrada: confira o áudio da gravação")
    PRE, POS = 0.10, 0.16           # folga antes e depois da fala, pra não comer começo nem fim de palavra
    faixas = []
    a, b = max(0, ws[0][0] - PRE), ws[0][1]
    for s, e, _ in ws[1:]:
        if s - b > pausa or removido(b, s):
            faixas.append([a, min(dur, b + POS)])
            a = max(0, s - PRE)
        b = max(b, e)
    faixas.append([a, min(dur, b + POS)])
    # junta faixas que se encostaram por causa da folga
    out = []
    for f in faixas:
        if out and f[0] <= out[-1][1] + 0.02:
            out[-1][1] = max(out[-1][1], f[1])
        else:
            out.append(f)
    return [[round(x, 3), round(y, 3)] for x, y in out]


COR = ["-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]


def cortar(src, faixas, saida, fps, crf=14, preset="medium"):
    """uma passada só: mantém as faixas (select/aselect) e emenda, com vídeo e áudio no mesmo relógio."""
    expr = "+".join(f"between(t,{a},{b})" for a, b in faixas)
    fc = (f"[0:v]fps={fps},select='{expr}',setpts=N/FRAME_RATE/TB[v];"
          f"[0:a]aselect='{expr}',asetpts=N/SR/TB[a]")
    script = Path(saida).with_suffix(".filtro.txt")
    script.write_text(fc)
    run([FFMPEG, "-y", "-v", "error", "-stats", "-i", src, "-filter_complex_script", str(script),
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", str(crf), "-preset", preset, *COR,
         "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", saida])
    script.unlink()


def proxy(src, saida):
    """cópia 1080p 60 pra montar e renderizar a prévia rápido."""
    run([FFMPEG, "-y", "-v", "error", "-stats", "-i", src, "-vf", "scale=1920:1080:flags=lanczos,fps=60",
         "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", *COR, "-c:a", "aac", "-b:a", "256k",
         "-movflags", "+faststart", saida])


def remapear(words, faixas):
    """tempos das palavras na linha do tempo cortada + pontos de corte."""
    out, cuts, base = [], [], 0.0
    for a, b in faixas:
        for s, e, w in words:
            if s >= a - 0.001 and e <= b + 0.05:
                out.append([round(s - a + base, 3), round(min(e, b) - a + base, 3), w])
        base += b - a
        cuts.append(round(base, 3))
    return out, cuts[:-1], round(base, 3)


def rosto(video, modelo_onnx, saida):
    import cv2, numpy as np
    W, H = 960, 540
    det = cv2.FaceDetectorYN.create(str(modelo_onnx), "", (W, H), 0.6)
    p = subprocess.Popen([FFMPEG, "-v", "error", "-i", video, "-vf", f"fps=10,scale={W}:{H}", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    out, i, ult = [], 0, [960.0, 500.0, 420.0]
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        f = np.frombuffer(b, np.uint8).reshape(H, W, 3)
        _, faces = det.detect(f)
        if faces is not None and len(faces):
            x, y, w, h = map(float, faces[0][:4])
            ult = [round((x + w / 2) / W * 1920, 1), round((y + h / 2) / H * 1080, 1), round(h / H * 1080, 1)]
            out.append([round(i / 10, 2), *ult, round(float(faces[0][-1]), 3)])
        else:
            out.append([round(i / 10, 2), *ult, 0])     # sem rosto: repete a última posição
        i += 1
    json.dump(out, open(saida, "w"))
    achou = sum(1 for o in out if o[4] > 0)
    print(f"  rosto achado em {achou} de {len(out)} quadros")


def onda(video, saida):
    import numpy as np
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", video, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    a = np.abs(np.frombuffer(raw, np.int16).astype(np.float32))
    n = 400                                   # 50 ms a 8 kHz
    picos = [float(a[i:i + n].max()) if len(a[i:i + n]) else 0 for i in range(0, len(a), n)]
    m = max(picos) or 1
    json.dump([round(p / m, 3) for p in picos], open(saida, "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bruto")
    ap.add_argument("pasta")
    ap.add_argument("--modelo", default="small", help="tiny, base, small, medium, large-v3 (maior = melhor e mais lento)")
    ap.add_argument("--remover", default="", help='trechos do BRUTO pra tirar, em segundos: "12.4-18.9,300-305"')
    ap.add_argument("--pausa", type=float, default=0.35, help="pausa maior que isso (s) é cortada")
    ap.add_argument("--sem-corte", action="store_true", help="não corta pausas (só transcreve e prepara)")
    a = ap.parse_args()

    src = str(Path(a.bruto).resolve())
    proj = Path(a.pasta).resolve()
    hf = proj / "hf"
    dados, assets = hf / "dados", hf / "assets"
    for d in (dados, assets / "cap", assets / "sfx", hf / "renders"):
        d.mkdir(parents=True, exist_ok=True)
    w, h, fps, dur = probe(src)
    print(f"bruto: {w}x{h} {fps:.2f} fps {dur:.1f} s")

    print("1/6 transcrevendo (pode demorar)…")
    wav = str(dados / "voz16k.wav")
    run([FFMPEG, "-y", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", wav])
    words = transcrever(wav, a.modelo)
    json.dump(words, open(dados / "bruto.words.json", "w"), ensure_ascii=False)

    remover = []
    for par in filter(None, a.remover.split(",")):
        x, y = par.split("-")
        remover.append((float(x), float(y)))
    faixas = [[0, dur]] if a.sem_corte else faixas_para_manter(words, dur, a.pausa, remover)
    json.dump(faixas, open(dados / "faixas.json", "w"))
    tirado = dur - sum(b - x for x, b in faixas)
    print(f"2/6 {len(faixas)} trechos, {tirado:.1f} s de pausa e take removidos")

    print("3/6 gerando o vídeo cortado (resolução original) e a cópia 1080p 60…")
    cortar(src, faixas, str(assets / "cortado.mp4"), round(fps, 3))
    proxy(str(assets / "cortado.mp4"), str(assets / "cam1080.mp4"))

    print("4/6 refazendo os tempos das palavras…")
    fala, cuts, total = remapear(words, faixas)
    json.dump(fala, open(dados / "fala.words.json", "w"), ensure_ascii=False)
    json.dump(cuts, open(dados / "cuts.json", "w"))
    (dados / "fala.txt").write_text("\n".join(
        f"[{int(s // 60):02d}:{s % 60:05.2f}] " + " ".join(x[2] for x in fala if s <= x[0] < s + 10)
        for s in range(0, int(total) + 1, 10)), encoding="utf-8")
    json.dump({"duracao": total, "largura": w, "altura": h, "fps": fps, "bruto": src}, open(dados / "info.json", "w"))

    print("5/6 rosto, forma de onda e folha de quadros…")
    rosto(str(assets / "cam1080.mp4"), SKILL / "modelos" / "yunet.onnx", dados / "face.json")
    onda(str(assets / "cam1080.mp4"), dados / "wave.json")
    run([sys.executable, str(SKILL / "scripts" / "folha.py"), str(assets / "cam1080.mp4"), str(dados / "folha.jpg")])

    print("6/6 montando a pasta do HyperFrames…")
    for f in ("lib.py", "estilo.css"):
        shutil.copy(SKILL / "motor" / f, hf / f)
    if not (hf / "build.py").exists():
        shutil.copy(SKILL / "motor" / "exemplo_build.py", hf / "build.py")
    shutil.copy(SKILL / "motor" / "hyperframes.json", hf / "hyperframes.json")
    if (SKILL / "motor" / "Inter.woff2").exists():
        shutil.copy(SKILL / "motor" / "Inter.woff2", assets / "Inter.woff2")
    sons = SKILL / "sons"
    if not any(sons.glob("*.wav")):
        run([sys.executable, str(SKILL / "scripts" / "sons.py"), str(sons)])
    for f in sons.glob("*.wav"):
        shutil.copy(f, assets / "sfx" / f.name)
    print(f"PRONTO: {hf}\n  leia dados/fala.txt e abra dados/folha.jpg antes de montar o build.py")


if __name__ == "__main__":
    main()
