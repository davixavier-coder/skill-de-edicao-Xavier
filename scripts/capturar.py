#!/usr/bin/env python3
"""Captura um site real (material oficial) com o Chrome em modo headless.

    python3 capturar.py URL saida.png [--largura 1440] [--altura 2600] [--escuro]

Página longa: aumente --altura pra ter o que rolar no vídeo. Confira a imagem depois (cookies, login, 404).
"""
import argparse, os, platform, shutil, subprocess, sys, tempfile

ap = argparse.ArgumentParser()
ap.add_argument("url")
ap.add_argument("saida")
ap.add_argument("--largura", type=int, default=1440)
ap.add_argument("--altura", type=int, default=2600)
ap.add_argument("--escuro", action="store_true")
a = ap.parse_args()

candidatos = {
    "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "/Applications/Chromium.app/Contents/MacOS/Chromium",
               "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
    "Windows": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
}.get(platform.system(), []) + [shutil.which(x) or "" for x in ("google-chrome", "chromium", "chromium-browser", "chrome")]
chrome = next((c for c in candidatos if c and os.path.exists(c)), None)
if not chrome:
    sys.exit("Chrome não encontrado: instale o Google Chrome")

saida = os.path.abspath(a.saida)
os.makedirs(os.path.dirname(saida), exist_ok=True)
with tempfile.TemporaryDirectory() as perfil:
    args = [chrome, "--headless=new", "--hide-scrollbars", "--disable-gpu", f"--user-data-dir={perfil}",
            f"--window-size={a.largura},{a.altura}", "--virtual-time-budget=8000", "--force-device-scale-factor=2",
            f"--screenshot={saida}"]
    if a.escuro:
        args.append("--force-dark-mode")
    subprocess.run(args + [a.url], capture_output=True, timeout=120)
if not os.path.exists(saida):
    sys.exit("a captura falhou: tente de novo ou peça um print pra pessoa")
print("capturado:", saida)
