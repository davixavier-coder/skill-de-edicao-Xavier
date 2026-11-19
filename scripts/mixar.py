#!/usr/bin/env python3
"""Som final: a voz original intocada (do vídeo cortado) + os efeitos do sfx.json.

    cd PASTA/hf && python3 mixar.py renders/previa.mp4 renders/previa-som.mp4 [--voz assets/cam1080.mp4]

O render do HyperFrames sai com a voz mais baixa ou sem ela; aqui a voz volta no volume original.
"""
import argparse, json, shutil, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("render")
ap.add_argument("saida")
ap.add_argument("--voz", default="assets/cam1080.mp4")
ap.add_argument("--sfx", default="sfx.json")
a = ap.parse_args()

DEF = {"whoosh": 0.5, "whip": 0.4, "pop": 0.3, "impact": 0.5, "riser": 0.3, "key": 0.2}
cues = json.load(open(a.sfx))
args = [shutil.which("ffmpeg") or "ffmpeg", "-y", "-loglevel", "error", "-i", a.render, "-i", a.voz]
fc = []
for i, (t, kind, vol) in enumerate(cues):
    args += ["-i", f"assets/sfx/{kind}.wav"]
    v = vol if vol is not None else DEF[kind]
    ms = max(0, int(round(t * 1000)))
    fc.append(f"[{i+2}:a]aresample=48000,aformat=channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{i}]")
fc.append("[1:a]aresample=48000,aformat=channel_layouts=stereo[v]")
fc.append("[v]" + "".join(f"[s{i}]" for i in range(len(cues))) +
          f"amix=inputs={len(cues)+1}:normalize=0:duration=first,alimiter=limit=0.95[a]")
args += ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
         "-shortest", "-movflags", "+faststart", a.saida]
subprocess.run(args, check=True)
print("ok", a.saida, f"({len(cues)} sons)")
