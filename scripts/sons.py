#!/usr/bin/env python3
"""Gera os sons da edição Xavier do zero (sintetizados aqui, sem direito autoral de ninguém).

    python3 sons.py PASTA_SAIDA

whoosh (troca grande de cena), whip (chicote de câmera), pop (grave e baixo), impact (grave, capítulo/número),
riser (subida antes de revelação) e key (clique de mouse). O pico de cada um bate com PEAK no motor/lib.py.
"""
import sys, wave
from pathlib import Path
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def salvar(nome, x, pasta):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    st = np.stack([x, x], 1)
    with wave.open(str(pasta / f"{nome}.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def passa_baixa(x, corte):
    """filtro de 1 polo com corte variando no tempo (array em Hz)"""
    a = np.exp(-2 * np.pi * np.asarray(corte) / SR) * np.ones_like(x)
    y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def env(n, pico, ataque_pow=2.0, queda_pow=2.5):
    t = np.linspace(0, 1, n)
    p = pico / n
    e = np.where(t < p, (t / max(p, 1e-6)) ** ataque_pow, ((1 - t) / max(1 - p, 1e-6)) ** queda_pow)
    return e


def whoosh(dur=0.85, pico=0.42):
    n = int(SR * dur)
    ruido = rng.standard_normal(n)
    corte = np.interp(np.arange(n), [0, int(SR * pico), n], [300, 3800, 500])
    x = passa_baixa(passa_baixa(ruido, corte), corte)
    return x * env(n, int(SR * pico))


def whip(dur=0.4, pico=0.18):
    n = int(SR * dur)
    ruido = rng.standard_normal(n)
    corte = np.interp(np.arange(n), [0, int(SR * pico), n], [900, 6500, 1200])
    x = ruido - passa_baixa(ruido, 400)
    x = passa_baixa(x, corte)
    return x * env(n, int(SR * pico), 1.5, 4)


def pop(dur=0.16):
    n = int(SR * dur); t = np.arange(n) / SR
    f = np.interp(t, [0, dur], [190, 85])
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return x * np.exp(-t * 30) * np.minimum(1, t * 900)


def impact(dur=1.1):
    n = int(SR * dur); t = np.arange(n) / SR
    f = np.interp(t, [0, 0.25, dur], [95, 52, 42])
    corpo = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.2)
    batida = passa_baixa(rng.standard_normal(n), 700) * np.exp(-t * 28) * 2.5
    return (corpo + batida) * np.minimum(1, t * 1200)


def riser(dur=1.25, pico=1.15):
    n = int(SR * dur); t = np.arange(n) / SR
    ruido = rng.standard_normal(n)
    corte = np.interp(np.arange(n), [0, int(SR * pico)], [200, 5000])
    x = passa_baixa(ruido, corte)
    tom = np.sin(2 * np.pi * np.cumsum(np.interp(t, [0, dur], [180, 420])) / SR) * 0.25
    e = np.where(t < pico, (t / pico) ** 2.2, np.exp(-(t - pico) * 40))
    return (x + tom) * e


def key(dur=0.05):
    n = int(SR * dur); t = np.arange(n) / SR
    x = rng.standard_normal(n) - passa_baixa(rng.standard_normal(n), 1500)
    return x * np.exp(-t * 160)


if __name__ == "__main__":
    pasta = Path(sys.argv[1] if len(sys.argv) > 1 else "sons")
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, f in [("whoosh", whoosh), ("whip", whip), ("pop", pop), ("impact", impact), ("riser", riser), ("key", key)]:
        salvar(nome, f(), pasta)
    print("sons gerados em", pasta)
