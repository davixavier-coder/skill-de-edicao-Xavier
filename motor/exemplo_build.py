#!/usr/bin/env python3
"""build.py de EXEMPLO da edição Xavier: roda em qualquer gravação preparada, só pra testar o motor.

    python3 build.py [--src assets/cortado.mp4]   → index.html, sfx.json, events.json

Num vídeo de verdade, apague o miolo e monte cena por cena com T("frase dita"), seguindo o plano de cenas e
referencias/estilo.md. Aqui as cenas caem em pontos fixos do vídeo (frações da duração) pra funcionar em qualquer fala.
"""
from lib import *

d = DUR


def palavra_perto(t):
    """instante de início da palavra mais perto de t (as cenas caem sempre numa palavra)"""
    return min(W, key=lambda w: abs(w[0] - t))[0]


# --- enquadramentos: troca a cada ideia, corte seco nos cortes de pausa e suave no meio da fala
cam(0, "M", "cut")
for k, c in enumerate([c for c in CUTS if c > 2][:12]):
    cam(c, ["CL", "X", "W", "CR", "M"][k % 5], "cut")

# --- soco de zoom numa ênfase
punch(palavra_perto(d * 0.08))

# --- pergunta imaginária no começo de uma fala
t = palavra_perto(d * 0.15)
pergunta(t, t + 2.4, "ah, mas e se eu nunca editei nada?")

# --- material oficial em tela cheia (troque pela captura real: scripts/capturar.py URL assets/cap/site.png)
t0 = palavra_perto(d * 0.3)
if os.path.exists("assets/cap/exemplo.png"):
    pagina(t0, t0 + 3.5, "assets/cap/exemplo.png", "github.com/exemplo", y0=0, y1=600)
else:
    textao(t0, t0 + 2.2, "MATERIAL OFICIAL", "aqui entra o site real", tom="b", pos="chest", tam=120)

# --- número dito, contando
t = palavra_perto(d * 0.5)
numero(t, t + 2.4, 938, suf="%", rotulo="a procura subiu", tom="g")

# --- capítulo na virada de assunto
capitulo(palavra_perto(d * 0.65), 2, "o que muda agora")

# --- revelação: texto verde grande sobre o rosto (não um slide)
t = palavra_perto(d * 0.82)
textao(t, t + 2.0, "JÁ ERA", tom="g", pos="chest", tam=170)

salvar()
