# Edição Xavier

Skill pro Claude Code que edita vídeo longo do YouTube (16:9) no estilo Xavier: pausas cortadas, câmera que segue o
rosto, telas cheias com materiais oficiais, poucos textos grandes em Inter, números contando, capítulos e sons raros.
Montada em [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP renderizado em MP4).

## Instalar

Abra o Claude Code e cole:

> instala essa skill: https://github.com/davixavier-coder/skill-de-edicao-Xavier

Ou à mão:

```bash
git clone https://github.com/davixavier-coder/skill-de-edicao-Xavier ~/.claude/skills/edicao-xavier
bash ~/.claude/skills/edicao-xavier/scripts/instalar.sh
```

No Windows: `powershell -ExecutionPolicy Bypass -File $HOME\.claude\skills\edicao-xavier\scripts\instalar.ps1`.

Precisa de: Node 22+, FFmpeg, Python 3.10+ e Google Chrome. O instalador confere tudo, instala o Whisper e o OpenCV
num ambiente só da skill, baixa o detector de rosto e a fonte Inter, gera os sons e instala as skills oficiais do
HyperFrames. Termina com `TUDO PRONTO`.

## Usar

No Claude Code, mande a gravação e peça:

> edita esse vídeo no estilo Xavier: /caminho/da/gravacao.mov

O Claude transcreve, corta as pausas, assiste, pega os materiais oficiais, monta a edição e te entrega uma prévia em
1080p 60. Você pede os ajustes, ele refaz, e só depois do seu OK sai o final na resolução da gravação.

## O que tem aqui

- `SKILL.md`: o fluxo que o Claude segue.
- `referencias/estilo.md`: o que funciona e o que é proibido (a parte mais importante).
- `referencias/motor.md`, `motor/`: o motor de edição (câmera, telas cheias, textos, sons).
- `referencias/materiais-oficiais.md`, `referencias/conferencia.md`: de onde vem o material e a conferência final.
- `scripts/`: preparar a gravação, capturar sites, gerar sons, mixar e folha de quadros.

## Créditos e licenças

Código desta skill: licença MIT. Usa HyperFrames (HeyGen), GSAP, FFmpeg, Whisper, OpenCV e o detector de rosto YuNet
(OpenCV Zoo), cada um com a sua licença. A fonte Inter (rsms/inter) é baixada na instalação, sob a licença SIL Open
Font License. Os sons são gerados na hora pelo `scripts/sons.py`.
