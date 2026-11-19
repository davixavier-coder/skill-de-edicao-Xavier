"""Motor da edição Xavier (vídeo longo 16:9 em HyperFrames).

Câmera que segue o rosto e troca de enquadramento; telas cheias que entram com zoom pra dentro e desfoque (nunca
deslizando de lado); materiais oficiais; poucos textos grandes em Inter; som audível e raro.

Uso dentro do build.py:
    from lib import *
    cam(0, "M"); cam(T("segunda frase"), "CL")
    tela_cheia(T("olha o site"), T("e depois"), pagina_html(...))
    ...
    salvar()          # escreve index.html, sfx.json e events.json
Lista completa das funções e receitas em referencias/motor.md.
"""
import json, re, sys, unicodedata, html, math, os

E = html.escape
D = "dados"
INFO = json.load(open(f"{D}/info.json"))
DUR = INFO["duracao"]
W = json.load(open(f"{D}/fala.words.json"))          # [[início, fim, palavra], ...] na linha do tempo cortada
CUTS = json.load(open(f"{D}/cuts.json"))             # pontos de corte (s)
FACE_RAW = json.load(open(f"{D}/face.json"))         # [[t, cx, cy, h, conf]] a cada 0,1 s, quadro 1920x1080
SRC = sys.argv[sys.argv.index("--src") + 1] if "--src" in sys.argv else "assets/cam1080.mp4"

els, js, sfx = [], [], []
_uid = [0]
EVENTS = []
_trk = [3]


def nid(p="e"):
    _uid[0] += 1
    return f"{p}{_uid[0]}"


def add(h):
    els.append(h)


def J(s):
    js.append(s)


def r3(x):
    return round(float(x), 3)


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9% ]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def T(frase, depois=0.0):
    """instante (s) em que a frase começa a ser dita, a partir de `depois`. Para se não achar: confira dados/fala.txt."""
    want = norm(frase).split()
    ws = [(norm(x[2]), x[0]) for x in W]
    for i in range(len(ws)):
        if ws[i][1] < depois - 0.01:
            continue
        if [a for a, _ in ws[i:i + len(want)]] == want:
            return round(ws[i][1], 2)
    sys.exit(f"frase não achada: {frase!r} depois de {depois}")


def FIM(frase, depois=0.0):
    """instante em que a última palavra da frase termina de ser dita."""
    want = norm(frase).split()
    t = T(frase, depois)
    i = next(k for k, x in enumerate(W) if abs(x[0] - t) < 0.005)
    return round(W[i + len(want) - 1][1], 2)


def ev(t0, t1, kind, text):
    EVENTS.append(dict(id=f"e{len(EVENTS)+1}", type=kind, t0=round(t0, 2), t1=round(t1, 2), text=text[:90]))


# ---------------------------------------------------------------- som (raro e audível)
# onde cai o pico de cada som gerado por scripts/sons.py (s)
PEAK = {"whoosh": 0.42, "whip": 0.18, "pop": 0.0, "impact": 0.0, "riser": 1.15, "key": 0.0}


def snd(t, kind, vol=None):
    sfx.append([r3(t), kind, vol])


def hit(t, kind, vol=None):
    """som com o pico no instante t"""
    snd(t - PEAK[kind], kind, vol)


# ---------------------------------------------------------------- tweens básicos (GSAP)
def fromto(sel, a, b, t):
    b = dict(b)
    b.setdefault("immediateRender", False)
    b.setdefault("lazy", False)
    J(f'tl.fromTo("{sel}",{json.dumps(a)},{json.dumps(b)},{r3(t)});')


def to(sel, b, t):
    b = dict(b)
    b.setdefault("lazy", False)
    J(f'tl.to("{sel}",{json.dumps(b)},{r3(t)});')


def sett(sel, b, t):
    J(f'tl.set("{sel}",{json.dumps(b)},{r3(t)});')


def win(sel, a, b, disp="block"):
    """o elemento só existe na tela entre a e b (fora disso display:none)"""
    sett(sel, {"display": disp}, max(0.001, a))
    sett(sel, {"display": "none"}, b)


def hide0(sel):
    sett(sel, {"opacity": 0}, 0)


def appear(sel, t, y=36, s=0.9, d=0.5, blur=14):
    hide0(sel)
    fromto(sel, {"opacity": 0, "y": y, "scale": s, "filter": f"blur({blur}px)"},
           {"opacity": 1, "y": 0, "scale": 1, "filter": "blur(0px)", "duration": d, "ease": "expo.out"}, t)


def vanish(sel, t, d=0.28):
    """some terminando em t"""
    fromto(sel, {"opacity": 1, "filter": "blur(0px)"}, {"opacity": 0, "filter": "blur(12px)", "duration": d, "ease": "power3.in"}, t - d)


def pop(sel, t, d=0.45, k=0.4):
    hide0(sel)
    fromto(sel, {"opacity": 0, "scale": k}, {"opacity": 1, "scale": 1, "duration": d, "ease": "back.out(2)"}, t)


def digitar(eid, texto, t, cps=24):
    """texto aparecendo letra por letra em #eid; devolve quando termina"""
    for i in range(1, len(texto) + 1):
        J(f'tl.set("#{eid}",{{textContent:{json.dumps(texto[:i])}}},{r3(t + i / cps)});')
    J(f'tl.set("#{eid}",{{textContent:""}},0);')
    return t + len(texto) / cps


def ptbr(v, dec=0):
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def conta(eid, a, b, t, d=1.0, pre="", suf="", dec=0):
    """número contando de a até b em #eid (formato brasileiro)"""
    fmt = f'(o.v).toLocaleString("pt-BR",{{minimumFractionDigits:{dec},maximumFractionDigits:{dec}}})'
    J(f'(()=>{{const o={{v:{a}}};tl.to(o,{{v:{b},duration:{d},ease:"power3.out",lazy:false,onUpdate:()=>{{'
      f'document.getElementById("{eid}").textContent={json.dumps(pre)}+{fmt}+{json.dumps(suf)};}}}},{r3(t)});'
      f'tl.set("#{eid}",{{textContent:{json.dumps(pre + ptbr(a, dec) + suf)}}},0);}})();')


# ---------------------------------------------------------------- câmera (segue o rosto)
def _smooth():
    xs = [f[1] for f in FACE_RAW]
    ys = [f[2] for f in FACE_RAW]
    k = 7
    out = []
    for i in range(len(xs)):
        a, b = max(0, i - k), min(len(xs), i + k + 1)
        out.append((sum(xs[a:b]) / (b - a), sum(ys[a:b]) / (b - a)))
    return out or [(960, 500)]


FACE = _smooth()


def face_at(t):
    i = max(0, min(len(FACE) - 1, int(round(t * 10))))
    return FACE[i]


# enquadramentos: escala + onde o centro do rosto fica na tela
FRAMES = {
    "W": (1.0, (960, 520)),       # aberto (o ambiente inteiro)
    "M": (1.2, (960, 500)),       # médio
    "CL": (1.45, (1250, 480)),    # fechado, rosto à direita → espaço à esquerda pra material
    "CR": (1.45, (670, 480)),     # fechado, rosto à esquerda → espaço à direita
    "X": (1.6, (960, 530)),       # bem fechado no rosto
}
SHOTS = []          # (t, frame, how)


def cam(t, frame, how=None):
    """muda o enquadramento em t. how: "cut" (seco), "ease" (suave no meio da fala) ou "whip" (chicote com desfoque)"""
    SHOTS.append((r3(t), frame, how))


def _target(t, frame, push):
    s0, (px, py) = FRAMES[frame]
    s = s0 * (1 + push)
    cx, cy = face_at(t)
    x = px - s * cx
    y = py - s * cy
    x = max(1920 * (1 - s), min(0, x))
    y = max(1080 * (1 - s), min(0, y))
    return round(x, 1), round(y, 1), round(s, 4)


def near_cut(t):
    return any(abs(t - c) < 0.12 for c in CUTS)


def build_camera():
    sh = sorted(SHOTS) or [(0, "M", "cut")]
    if sh[0][0] > 0.01:
        sh.insert(0, (0, "M", "cut"))
    sh.append((DUR + 1, "W", "cut"))
    for i in range(len(sh) - 1):
        t0, fr, how = sh[i]
        t1 = sh[i + 1][0]
        if how is None:
            how = "cut" if near_cut(t0) else "ease"
        n = max(1, int((t1 - t0) / 0.5))
        x, y, s = _target(t0, fr, 0)
        if how == "cut" or t0 <= 0.01:
            sett("#camT", {"x": x, "y": y, "scale": s}, t0)
        elif how == "whip":
            fromto("#camT", {}, {"x": x, "y": y, "scale": s, "duration": 0.3, "ease": "power4.inOut"}, t0 - 0.15)
            fromto("#camP", {"filter": "blur(0px)"}, {"keyframes": [{"filter": "blur(9px)", "duration": 0.14}, {"filter": "blur(0px)", "duration": 0.18}], "ease": "none"}, t0 - 0.15)
            hit(t0, "whip", 0.4)
        else:
            fromto("#camT", {}, {"x": x, "y": y, "scale": s, "duration": 0.6, "ease": "power3.inOut"}, t0 - 0.3)
        start = t0 + (0.35 if how != "cut" else 0)
        for k in range(1, n + 1):          # segue o rosto e aproxima devagar dentro do take
            tk = t0 + (t1 - t0) * k / n
            x, y, s = _target(tk, fr, 0.035 * k / n)
            dur = (t1 - t0) / n
            fromto("#camT", {}, {"x": x, "y": y, "scale": s, "duration": r3(dur), "ease": "sine.inOut"}, max(start, tk - dur))


def punch(t, k=1.08, d=0.45):
    """soco de zoom na palavra de ênfase (vai e volta)"""
    fromto("#camP", {"scale": k}, {"scale": 1, "duration": d, "ease": "power2.out"}, t)


def push_in(t, k=1.12, d=0.5):
    fromto("#camP", {"scale": 1}, {"scale": k, "duration": d, "ease": "power3.inOut"}, t)


def push_out(t, d=0.45):
    to("#camP", {"scale": 1, "duration": d, "ease": "power3.inOut"}, t)


def rosto_desfocado(t0, t1):
    """rosto desfocado e escurecido atrás de um material ou texto"""
    fromto("#camFx", {"filter": "blur(0px) brightness(1)"}, {"filter": "blur(16px) brightness(0.55)", "duration": 0.45, "ease": "power2.out"}, t0)
    fromto("#camFx", {"filter": "blur(16px) brightness(0.55)"}, {"filter": "blur(0px) brightness(1)", "duration": 0.4, "ease": "power2.inOut"}, t1 - 0.4)


# ---------------------------------------------------------------- telas cheias
def tela_cheia(t0, t1, inner, sid=None, entra="zoom", sai="zoom", fundo="bgA", som=True, rotulo=""):
    """cena que ocupa o quadro inteiro entre t0 e t1. Termine em t1 = fim da frase que fala dela."""
    sid = sid or nid("fs")
    add(f'<div id="{sid}" class="fs {fundo}"><div class="fsin" id="{sid}_i">{inner}</div></div>')
    ev(t0, t1, "animation", rotulo or re.sub(r"<[^>]+>", " ", inner))
    win(f"#{sid}", t0 - 0.5, t1 + 0.6)
    if t0 <= 0.01:
        sett(f"#{sid}", {"opacity": 1}, 0)
    else:
        hide0(f"#{sid}")
        if entra == "zoom":     # a câmera acelera pra dentro do rosto e a cena nasce grande e desfocada
            fromto("#camP", {"scale": 1, "filter": "blur(0px)"}, {"scale": 1.28, "filter": "blur(10px)", "duration": 0.24, "ease": "power3.in"}, t0 - 0.24)
            sett("#camP", {"scale": 1, "filter": "blur(0px)"}, t0 + 0.3)
            fromto(f"#{sid}", {"opacity": 0, "scale": 1.35, "filter": "blur(26px)"}, {"opacity": 1, "scale": 1, "filter": "blur(0px)", "duration": 0.55, "ease": "expo.out"}, t0 - 0.06)
            if som:
                hit(t0, "whoosh", 0.5)
        elif entra == "cut":
            sett(f"#{sid}", {"opacity": 1}, t0)
            fromto(f"#{sid}_i", {"scale": 1.1}, {"scale": 1, "duration": 0.5, "ease": "expo.out"}, t0)
            if som:
                hit(t0, "whip", 0.35)
        elif entra == "fade":
            fromto(f"#{sid}", {"opacity": 0}, {"opacity": 1, "duration": 0.35, "ease": "power2.out"}, t0)
    if sai == "zoom":
        fromto(f"#{sid}", {"opacity": 1, "scale": 1, "filter": "blur(0px)"}, {"opacity": 0, "scale": 1.3, "filter": "blur(22px)", "duration": 0.34, "ease": "power2.in"}, t1 - 0.34)
        fromto("#camP", {"scale": 1.16, "filter": "blur(10px)"}, {"scale": 1, "filter": "blur(0px)", "duration": 0.6, "ease": "expo.out"}, t1 - 0.12)
    elif sai == "cut":
        sett(f"#{sid}", {"opacity": 0}, t1)
    return sid


def video(src, t0, dur, estilo="", cls="vcheio", inicio_midia=0):
    """<video> mudo que toca entre t0 e t0+dur (use dentro de tela_cheia). inicio_midia = de onde começa no arquivo."""
    _trk[0] += 1
    vid = nid("v")
    return (f'<video id="{vid}" class="clip {cls}" src="{src}" muted playsinline style="{estilo}" data-start="{r3(t0)}" '
            f'data-duration="{r3(dur)}" data-media-start="{inicio_midia}" data-track-index="{_trk[0]}"></video>')


def pagina(t0, t1, src, url, y0=0, y1=0, larg_img=1440, alt_img=None, rotulo="", som=True):
    """site real numa janela de navegador em tela cheia, rolando de y0 até y1 (pixels da captura).
    Devolve o id da página pra usar com anel()/cursor() (coordenadas na tela 1920x1080)."""
    pid = nid("pg")
    inner = (f'<div class="nav"><div class="navbar"><i></i><i></i><i></i><span class="url">{E(url)}</span></div>'
             f'<div class="navvp"><img id="{pid}" src="{src}" style="width:100%"></div></div>')
    tela_cheia(t0, t1, inner, rotulo=rotulo or f"site {url}", som=som)
    k = 1720 / larg_img           # a janela mostra a captura com 1720 px de largura
    if y1 != y0:
        fromto(f"#{pid}", {"y": -y0 * k}, {"y": -y1 * k, "duration": r3(max(0.5, (t1 - t0) - 0.6)), "ease": "sine.inOut"}, t0 + 0.3)
    else:
        sett(f"#{pid}", {"y": -y0 * k}, 0)
        fromto(f"#{pid}", {"scale": 1}, {"scale": 1.04, "duration": r3(t1 - t0), "ease": "none"}, t0)   # nunca 100% parada
    return pid


def imagem(t0, t1, src, rotulo="", ajuste="contain", som=True, zoom=1.06):
    """print ou foto real em tela cheia, com zoom lento (nunca parada). ajuste: contain (inteira) ou cover (preenche)"""
    iid = nid("im")
    inner = (f'<img class="imbg" src="{src}"><img id="{iid}" class="imfg" src="{src}" style="object-fit:{ajuste}">')
    tela_cheia(t0, t1, inner, rotulo=rotulo or src, som=som)
    fromto(f"#{iid}", {"scale": 1}, {"scale": zoom, "duration": r3(t1 - t0), "ease": "none"}, t0)
    return iid


def anel(t0, t1, x, y, w, h, cor="#ffd23f"):
    """anel de destaque na tela (1920x1080), exatamente no termo dito (confira na prévia)"""
    aid = nid("an")
    add(f'<div id="{aid}" class="anel" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-color:{cor}"></div>')
    win(f"#{aid}", t0 - 0.1, t1 + 0.1)
    hide0(f"#{aid}")
    fromto(f"#{aid}", {"opacity": 0, "scale": 1.6}, {"opacity": 1, "scale": 1, "duration": 0.35, "ease": "back.out(1.6)"}, t0)
    vanish(f"#{aid}", t1)
    return aid


def cursor(t, x0, y0, x1, y1, d=0.7, clique=True):
    """seta do mouse indo de (x0,y0) até (x1,y1) e clicando em t+d"""
    cid = nid("cu")
    add(f'<div id="{cid}" class="cursor"><svg viewBox="0 0 24 24" width="46" height="46"><path d="M3 2l7 19 2.6-7.4L20 11z" fill="#fff" stroke="#000" stroke-width="1.4"/></svg></div>')
    win(f"#{cid}", t - 0.2, t + d + 0.9)
    fromto(f"#{cid}", {"x": x0, "y": y0, "opacity": 0}, {"x": x1, "y": y1, "opacity": 1, "duration": d, "ease": "power3.inOut"}, t)
    if clique:
        fromto(f"#{cid} svg", {"scale": 1}, {"scale": 0.8, "duration": 0.08, "yoyo": True, "repeat": 1}, t + d)
        hit(t + d, "key", 0.25)
    vanish(f"#{cid}", t + d + 0.8)
    return cid


def borrar(t0, t1, x, y, w, h):
    """esconde dado pessoal (nome, telefone, conversa) com um desfoque por cima"""
    bid = nid("bl")
    add(f'<div id="{bid}" class="borra" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>')
    win(f"#{bid}", t0 - 0.6, t1 + 0.7)
    return bid


def logos(t0, t1, srcs, rotulo="logos"):
    """logos oficiais coloridos entrando em cascata, sobre o rosto desfocado"""
    lid = nid("lg")
    add(f'<div id="{lid}" class="lgs">' + "".join(f'<div class="lgc"><img src="{s}"></div>' for s in srcs) + '</div>')
    win(f"#{lid}", t0 - 0.2, t1 + 0.1, "flex")
    ev(t0, t1, "graphic", rotulo)
    rosto_desfocado(t0 - 0.1, t1 + 0.2)
    hide0(f"#{lid} .lgc")
    fromto(f"#{lid} .lgc", {"opacity": 0, "y": 80, "scale": 0.5, "filter": "blur(10px)"},
           {"opacity": 1, "y": 0, "scale": 1, "filter": "blur(0px)", "duration": 0.5, "stagger": 0.09, "ease": "back.out(1.7)"}, t0)
    vanish(f"#{lid}", t1)
    hit(t0, "whoosh", 0.35)
    return lid


# ---------------------------------------------------------------- sobre o rosto
POS = {
    "L": "left:90px;top:0;bottom:0;width:820px;display:flex;align-items:center;justify-content:center",
    "R": "right:90px;top:0;bottom:0;width:820px;display:flex;align-items:center;justify-content:center",
    "low": "left:0;right:0;bottom:70px;display:flex;justify-content:center",
    "top": "left:0;right:0;top:70px;display:flex;justify-content:center",
    "C": "inset:0;display:flex;align-items:center;justify-content:center",
}


def ao_lado(t0, t1, inner, pos="L", sid=None, som=None, rotulo=""):
    """material ao lado do rosto (use com cam(..., "CL") ou "CR" pra abrir espaço). Sem som por padrão."""
    sid = sid or nid("ov")
    add(f'<div id="{sid}" class="ov" style="{POS[pos].replace("display:flex;", "")}"><div id="{sid}_c">{inner}</div></div>')
    win(f"#{sid}", t0 - 0.3, t1 + 0.1, "flex")
    ev(t0, t1, "graphic", rotulo or re.sub(r"<[^>]+>", " ", inner))
    appear(f"#{sid}_c", t0, y=40, s=0.88)
    vanish(f"#{sid}_c", t1)
    if som:
        hit(t0 + 0.05, som, 0.3)
    return sid


GRAD = {"g": "gG", "o": "gO", "w": "gW", "b": "gB", "r": "gR"}


def textao(t0, t1, grande, pequeno="", tom="w", pos="chest", tam=150, som="impact", vol=0.45):
    """texto GRANDE em degradê entrando com desfoque. Só em número, revelação ou frase de efeito (pouco!).
    tom: w branco, g verde (revelação), o laranja, b azul, r vermelho. pos: chest, L, R, top."""
    sid = nid("bw")
    stl = {"chest": "left:0;right:0;top:640px;text-align:center",
           "L": "left:60px;width:900px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;text-align:center",
           "R": "right:60px;width:900px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;text-align:center",
           "top": "left:0;right:0;top:90px;text-align:center"}[pos]
    sm = f'<div class="bws" id="{sid}s">{E(pequeno)}</div>' if pequeno else ""
    disp = "flex" if "display:flex" in stl else "block"
    add(f'<div id="{sid}" class="bw" style="{stl.replace("display:flex;", "")}"><div class="bwbg"></div>{sm}<div class="bwb {GRAD[tom]}" id="{sid}b" style="font-size:{tam}px">{E(grande)}</div></div>')
    win(f"#{sid}", t0 - 0.4, t1 + 0.1, disp)
    ev(t0, t1, "headline", f"{pequeno} {grande}")
    hide0(f"#{sid}")
    sett(f"#{sid}", {"opacity": 1}, t0 - 0.3)
    if pequeno:
        appear(f"#{sid}s", t0 - 0.3, y=14, s=0.96, d=0.4)
    hide0(f"#{sid}b")
    fromto(f"#{sid}b", {"opacity": 0, "scale": 1.45, "filter": "blur(22px)"}, {"opacity": 1, "scale": 1, "filter": "blur(0px)", "duration": 0.5, "ease": "expo.out"}, t0)
    vanish(f"#{sid}", t1)
    if som:
        hit(t0, som, vol)
    return sid


def numero(t0, t1, valor, pre="", suf="", dec=0, rotulo="", tom="g", pos="chest", tam=190, de=0):
    """número dito, grande, contando de `de` até `valor`"""
    sid = textao(t0, t1, pre + ptbr(valor, dec) + suf, rotulo, tom, pos, tam, som="impact", vol=0.4)
    conta(f"{sid}b", de, valor, t0, d=min(1.2, max(0.6, (t1 - t0) / 2)), pre=pre, suf=suf, dec=dec)
    return sid


def pergunta(t0, t1, texto, pos="top"):
    """pergunta imaginária ("ah, mas e se…"): minúscula, entre aspas, casual, no COMEÇO da fala"""
    sid = nid("pq")
    lugar = {"top": "left:0;right:0;top:110px", "low": "left:0;right:0;bottom:120px"}[pos]
    add(f'<div id="{sid}" class="perg" style="{lugar}">“{E(texto.lower())}”</div>')
    win(f"#{sid}", t0 - 0.2, t1 + 0.1)
    appear(f"#{sid}", t0, y=14, s=1, d=0.35, blur=8)
    vanish(f"#{sid}", t1)
    ev(t0, t1, "caption", texto)
    return sid


def lista_borrada(t0, t1, itens, titulo=""):
    """lista anunciada no gancho, mostrada BORRADA (curiosidade: nada entregue antes da hora)"""
    sid = nid("lb")
    li = "".join(f'<div class="lbi"><b>{k+1}</b><span>{E(x)}</span></div>' for k, x in enumerate(itens))
    tt = f'<div class="lbt gW">{E(titulo)}</div>' if titulo else ""
    tela_cheia(t0, t1, f'<div class="lb" id="{sid}">{tt}{li}</div>', rotulo="lista borrada", som=True)
    hide0(f"#{sid} .lbi")
    fromto(f"#{sid} .lbi", {"opacity": 0, "x": -60}, {"opacity": 1, "x": 0, "duration": 0.4, "stagger": 0.12, "ease": "expo.out"}, t0 + 0.2)
    return sid


def capitulo(t, num, titulo, dur=2.4):
    """virada de assunto: número do capítulo + título, sobre o rosto desfocado, com impacto grave"""
    sid = nid("cp")
    add(f'<div id="{sid}" class="cap"><div class="capn gO" id="{sid}n">{num:02d}</div><div class="capt" id="{sid}t">{E(titulo.upper())}</div></div>')
    win(f"#{sid}", t - 0.2, t + dur + 0.1, "flex")
    ev(t, t + dur, "chapter", f"{num:02d} {titulo}")
    rosto_desfocado(t - 0.1, t + dur + 0.2)
    pop(f"#{sid}n", t, d=0.5, k=1.8)
    appear(f"#{sid}t", t + 0.15, y=30, s=0.95)
    vanish(f"#{sid}", t + dur)
    hit(t, "impact", 0.5)
    return sid


def legenda(t0, t1, depois, n, destaque=(), topo=900):
    """frase curta acendendo palavra por palavra no tempo da fala (use pouco)"""
    sid = nid("sl")
    i0 = next(i for i, x in enumerate(W) if x[0] >= depois - 0.01)
    ws = W[i0:i0 + n]
    spans = []
    for k, (s, e, w) in enumerate(ws):
        cls = "slw hl" if norm(w) in [norm(h) for h in destaque] else "slw"
        spans.append(f'<span class="{cls}" id="{sid}w{k}">{E(w.strip(",."))}</span>')
    add(f'<div id="{sid}" class="sl" style="top:{topo}px">{" ".join(spans)}</div>')
    win(f"#{sid}", t0 - 0.2, t1 + 0.1)
    appear(f"#{sid}", t0 - 0.1, y=12, s=1, d=0.3, blur=6)
    for k, (s, e, w) in enumerate(ws):
        fromto(f"#{sid}w{k}", {"opacity": 0.28}, {"opacity": 1, "duration": 0.12, "ease": "none"}, s)
    vanish(f"#{sid}", t1)
    return sid


# ---------------------------------------------------------------- saída
def salvar():
    build_camera()
    css = open("estilo.css", encoding="utf-8").read()
    ids = re.findall(r'id="([^"]+)"', "\n".join(els))
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        sys.exit(f"ids repetidos: {sorted(dup)[:20]}")
    page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=1920, height=1080">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1920" data-height="1080" data-fps="60">
<div id="camBox"><div id="camFx"><div id="camP"><div id="camT"><video id="cam" class="clip" src="{SRC}" muted playsinline data-start="0" data-duration="{DUR}" data-media-start="0" data-track-index="0"></video></div></div></div></div>
{chr(10).join(els)}
<div class="vig"></div>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script></body></html>'''
    open("index.html", "w", encoding="utf-8").write(page)
    keep = []
    for t, k, v in sorted(sfx, key=lambda x: x[0]):
        t = max(0, t)
        if keep and t - keep[-1][0] < 0.6:          # nunca dois sons colados: som raro
            continue
        keep.append([t, k, v])
    json.dump(keep, open("sfx.json", "w"))
    json.dump(EVENTS, open("events.json", "w"), ensure_ascii=False)
    print(len(els), "elementos,", len(js), "animações,", len(keep), "sons,", len(EVENTS), "eventos")
