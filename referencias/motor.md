# O motor (motor/lib.py)

O `build.py` de cada vídeo importa o motor (`from lib import *`), chama as funções na ordem do vídeo e termina com
`salvar()`, que escreve `index.html` (a composição HyperFrames), `sfx.json` (os sons) e `events.json` (lista de tudo
que entrou, pra revisão). Tempo sempre em segundos na linha do tempo JÁ CORTADA.

## Achar o tempo certo

- `T("frase dita")`: quando a frase começa. `T("frase", depois=120)` procura a partir de 120 s (frase repetida).
- `FIM("frase dita")`: quando a última palavra dela termina. Use como fim de cena: a tela sai quando a frase acaba.
- `DUR`, `CUTS` (pontos de corte), `W` (palavras `[início, fim, palavra]`).
- Se `T` não achar, ele para e mostra a frase: confira a grafia em `dados/fala.txt` (o Whisper pode ter escrito
  diferente do que você esperava).

## Rosto

| Função | O que faz |
|---|---|
| `cam(t, "M")` | troca o enquadramento em t. `"W"` aberto, `"M"` médio, `"CL"` fechado com espaço à esquerda, `"CR"` com espaço à direita, `"X"` bem fechado. `how`: `"cut"`, `"ease"`, `"whip"` (padrão: seco no corte de pausa, suave no meio da fala) |
| `punch(t)` | soco de zoom na palavra de ênfase |
| `push_in(t)` / `push_out(t)` | aproxima e fica / volta |
| `rosto_desfocado(t0, t1)` | desfoca e escurece o rosto atrás de algo |

A câmera segue o rosto sozinha (dados/face.json) e aproxima devagar dentro de cada take.

## Telas cheias (material oficial)

| Função | O que faz |
|---|---|
| `pagina(t0, t1, "assets/cap/site.png", "site.com", y0, y1)` | site real numa janela de navegador, rolando de y0 até y1 (pixels da captura). Devolve o id |
| `imagem(t0, t1, "assets/cap/print.png")` | print ou foto em tela cheia, com fundo desfocado dela mesma e zoom lento |
| `tela_cheia(t0, t1, html)` | qualquer cena montada à mão (`fundo="bgA"`, `"bgB"`, `"bgC"`; `entra`/`sai`: `"zoom"`, `"cut"`, `"fade"`) |
| `video(src, t0, dur, inicio_midia=0)` | devolve o `<video>` mudo pra pôr dentro de `tela_cheia` (vídeo real, gravação de tela) |
| `anel(t0, t1, x, y, w, h)` | destaque no termo dito (coordenadas da tela 1920x1080) |
| `cursor(t, x0, y0, x1, y1)` | seta do mouse indo até o ponto e clicando |
| `borrar(t0, t1, x, y, w, h)` | esconde dado pessoal |
| `logos(t0, t1, [srcs])` | logos oficiais em cascata sobre o rosto desfocado |
| `ao_lado(t0, t1, html, pos="L")` | material ao lado do rosto (junto com `cam(t0, "CL")`) |

Gravação de tela com zoom no clique: `tela_cheia(t0, t1, video("assets/tela.mp4", t0, t1 - t0, inicio_midia=12.5))` e
depois `fromto("#ID", {"scale": 1}, {"scale": 1.8, "x": ..., "y": ..., "duration": 0.6, "ease": "power3.inOut"}, t)` no
elemento do vídeo, voltando com outro `fromto` quando o clique acaba.

## Texto (pouco!)

| Função | O que faz |
|---|---|
| `textao(t0, t1, "GRANDE", "frase pequena em cima", tom="w")` | texto grande em degradê entrando com desfoque. `tom`: `w`, `g` (revelação), `o`, `b`, `r`. `pos`: `chest`, `L`, `R`, `top` |
| `numero(t0, t1, 938, suf="%", rotulo="a procura subiu")` | número dito, contando |
| `pergunta(t0, t1, "ah, mas e se…")` | pergunta imaginária minúscula e casual, no começo da fala |
| `lista_borrada(t0, t1, ["item", …], "TÍTULO")` | lista do gancho borrada (curiosidade) |
| `capitulo(t, 3, "o que muda agora")` | virada de assunto com número |
| `legenda(t0, t1, depois, n, destaque=("palavra",))` | frase curta acendendo palavra por palavra |

## Som

`hit(t, "whoosh"|"whip"|"pop"|"impact"|"riser"|"key", vol)` põe o pico do som em t. As funções já colocam o som certo
nas entradas grandes; `salvar()` nunca deixa dois sons a menos de 0,6 s um do outro. Som é raro: a maioria das
entradas fica sem som nenhum.

## Peças soltas

`add(html)` põe um elemento; `win(sel, a, b)` faz ele existir só entre a e b; `appear`, `vanish`, `pop`, `fromto`,
`to`, `sett` animam com GSAP; `digitar(id, texto, t)` escreve letra por letra; `conta(id, a, b, t)` conta um número.
Classe nova vai no `estilo.css` do projeto.

## Receita de um bloco típico

```python
cam(T("o primeiro"), "CL")                                    # abre espaço à esquerda
ao_lado(T("o primeiro"), FIM("na loja dele"), '<img class="shot" src="assets/cap/loja.png">', "L")
cam(T("e sabe quanto"), "X", "cut")
numero(T("dez mil"), FIM("por mes"), 10000, pre="R$ ", rotulo="por mês")
pg = pagina(T("olha o site"), FIM("de graca"), "assets/cap/site.png", "site.com", 0, 900)
anel(T("de graca") - 0.1, FIM("de graca") + 0.4, 1180, 410, 300, 90)
```
