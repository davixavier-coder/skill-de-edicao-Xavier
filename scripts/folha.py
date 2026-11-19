#!/usr/bin/env python3
"""Folha de quadros: um quadro a cada N segundos numa imagem só, com o tempo escrito, pra assistir o vídeo inteiro.

    python3 folha.py VIDEO.mp4 folha.jpg [--cada 5] [--colunas 6]
"""
import argparse, json, math, shutil, subprocess, tempfile
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("saida")
ap.add_argument("--cada", type=float, default=0)
ap.add_argument("--colunas", type=int, default=6)
a = ap.parse_args()

FF = shutil.which("ffmpeg") or "ffmpeg"
dur = float(json.loads(subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-show_entries",
                                       "format=duration", "-of", "json", a.video], capture_output=True, text=True).stdout)["format"]["duration"])
cada = a.cada or max(2.0, round(dur / 72, 1))          # até ~72 quadros por folha
n = int(dur // cada) + 1
linhas = math.ceil(n / a.colunas)
with tempfile.TemporaryDirectory() as tmp:
    for i in range(n):
        t = i * cada
        txt = f"{int(t // 60):02d}\\:{t % 60:04.1f}"
        subprocess.run([FF, "-v", "error", "-ss", str(t), "-i", a.video, "-frames:v", "1", "-vf",
                        f"scale=480:-2,drawtext=text='{txt}':x=10:y=10:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6",
                        f"{tmp}/q{i:04d}.jpg"])
    subprocess.run([FF, "-y", "-v", "error", "-framerate", "1", "-i", f"{tmp}/q%04d.jpg", "-vf",
                    f"tile={a.colunas}x{linhas}:padding=4:color=black", "-frames:v", "1", "-q:v", "3", a.saida])
print("folha:", a.saida, f"({n} quadros, um a cada {cada:g} s)")
