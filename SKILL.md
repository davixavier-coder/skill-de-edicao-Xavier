---
name: edicao-xavier
description: >
  Edição de vídeo longo do YouTube (16:9) no estilo Xavier: pessoa falando pra câmera (às vezes com tela gravada),
  pausas cortadas, câmera que segue o rosto e troca de enquadramento, telas cheias com materiais oficiais (sites,
  prints, vídeos reais), poucos textos grandes em Inter, números contando, capítulos e sons raros e audíveis.
  Montado em HyperFrames (HTML + GSAP renderizado em MP4). Use quando a pessoa mandar uma gravação e disser
  "edita esse vídeo", "edição Xavier", "edita no estilo do Davi", "edita meu vídeo do YouTube", ou pedir pra
  refazer uma prévia com ajustes.
---

# Edição Xavier

Transforma uma gravação bruta (rosto falando, 16:9) num vídeo pronto pro YouTube que segura a atenção do começo
ao fim. O estilo foi aprovado em vídeos reais. O que funciona e o que é proibido está em
`referencias/estilo.md`. **Leia esse arquivo antes de montar qualquer cena.** Quase todo erro caro nessa edição é
repetir algo que já foi reprovado.

`S=~/.claude/skills/edicao-xavier` e `PY=$S/ambiente/bin/python` (Windows: `$S\ambiente\Scripts\python.exe`) nos
comandos abaixo. O `PY` é o Python da skill, com Whisper e OpenCV; os outros scripts rodam com qualquer `python3`.

## Primeira vez

Rode `bash $S/scripts/instalar.sh` (Mac/Linux) ou `powershell -ExecutionPolicy Bypass -File $S/scripts/instalar.ps1`
(Windows). Ele confere Node 22+, FFmpeg e Python 3.10+, instala o Whisper, o OpenCV e as skills oficiais do
HyperFrames, baixa o detector de rosto e gera os sons. Termina com `TUDO PRONTO`.

## O fluxo (um vídeo por vez)

1. **Preparar a gravação** (transcrição palavra por palavra, corte de pausas, rosto, forma de onda e folha de quadros):
   ```
   $PY $S/scripts/preparar.py GRAVACAO.mov PASTA_DO_PROJETO [--modelo small] [--remover "12.4-18.9,300-305"]
   ```
   Ele cria `PASTA_DO_PROJETO/hf/` já com o motor (`lib.py`, `estilo.css`, `build.py` de exemplo), os sons e os
   dados em `hf/dados/`. `--remover` tira trechos do bruto (take errado, repetição) antes do corte de pausas.
2. **Assistir antes de editar.** Abra `hf/dados/folha.jpg` (um quadro a cada poucos segundos) e leia
   `hf/dados/fala.txt` inteiro. Ache: takes repetidos ou errados (corte com `--remover` e rode de novo), o gancho,
   os momentos de revelação, os números, as perguntas imaginárias ("ah, mas e se…") e os trechos longos só de rosto.
   A legenda e o texto seguem o que a pessoa FALOU, não o roteiro.
3. **Pegar os materiais oficiais** de cada coisa citada (site, GitHub, print do app, post, vídeo). Ver
   `referencias/materiais-oficiais.md`. Captura de página: `python3 $S/scripts/capturar.py URL hf/assets/cap/nome.png`.
4. **Plano de cenas** antes do código, em tabela: frase dita → o que aparece → enquadramento/som. Confira contra a
   lista de proibidos do `estilo.md` (tela parada, texto demais, material repetido, entregar a resposta antes).
5. **Montar o `hf/build.py`** com as funções do motor (`referencias/motor.md`). Cada cena começa na palavra certa
   com `T("frase dita")` e termina quando a frase dela acaba.
6. **Prévia** em 1080p 60:
   ```
   cd PASTA_DO_PROJETO/hf && python3 build.py && npx hyperframes lint
   npx hyperframes render --quality draft --output renders/previa.mp4
   python3 $S/scripts/mixar.py renders/previa.mp4 renders/previa-som.mp4
   python3 $S/scripts/folha.py renders/previa-som.mp4 renders/folha-previa.jpg
   ```
   Confira a folha da prévia inteira e a lista de `referencias/conferencia.md` antes de mandar.
7. **Entregar a prévia** e esperar o veredito. Ajustes viram regra nova em `referencias/estilo.md` na hora.
8. **Final**, só depois do OK: `python3 build.py --src assets/cortado.mp4` (resolução original),
   `npx hyperframes render --quality delivery --output renders/final.mp4` e `mixar.py ... --voz assets/cortado.mp4`.

Render longo: rode em segundo plano (`HYPERFRAMES_RENDER_DETACHED=1`, ver a skill `hyperframes-cli`) e confira o log.

## Regras que valem pra tudo

- Um vídeo por vez, prévia antes do final. Nunca refazer vídeo entregue sem a pessoa pedir.
- Rosto intocado: nenhum filtro de cor, brilho ou nitidez no rosto. Voz original, no volume original.
- Nunca baixar a qualidade: prévia em 1080p 60, final na resolução e no fps da gravação (`--quality delivery`).
  Nada de 720p 25 nem tela cortada.
- Só materiais oficiais e reais. Nunca recriar, redesenhar ou inventar tela, print ou número.
- Dado pessoal que aparecer (nome de cliente, telefone, e-mail, conversa) é borrado.
- Nada de nome, rosto, skill ou material de outro criador que serviu de referência.
- Fonte: só Inter.
- Se a pessoa aprovar, reprovar ou criar uma regra: escreva em `referencias/estilo.md` na hora, com a frase dela.
