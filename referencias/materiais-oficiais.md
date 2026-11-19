# Materiais oficiais

"Materiais oficiais" são as coisas reais que a pessoa cita: o site da ferramenta, a página do GitHub, o print do app,
o post, a notícia, o vídeo, o canal. Eles fazem o vídeo parecer verdadeiro e seguram a atenção. Use esse nome ao
falar com a pessoa (não "telas").

## Onde pegar, em ordem

1. O que a pessoa mandou ou gravou (gravação de tela, prints dela).
2. A fonte original: site oficial, README e página do GitHub, post do criador, página de lançamento, notícia de
   veículo grande.
3. Logo oficial: o arquivo do site ou do kit de imprensa da marca (SVG ou PNG), colorido.

Nunca: página de suporte genérica no lugar da tela real, banco de imagens, imagem gerada por IA, print de terceiro
com marca d'água, tela recriada ou redesenhada. Se a imagem existe na fonte, use a da fonte.

## Capturar uma página

```
python3 ~/.claude/skills/edicao-xavier/scripts/capturar.py URL hf/assets/cap/nome.png [--largura 1440] [--altura 2600] [--escuro]
```

Captura a página com o Chrome em modo headless, na altura pedida (página longa = altura maior, pra rolar no vídeo).
Abra a imagem depois e confira: aviso de cookies cobrindo, página de login, erro 404 ou conteúdo errado = capture de
novo ou troque a fonte.

Página que exige login (X, Instagram, painel): peça pra pessoa mandar o print ou gravar a tela.

## Vídeos

Trecho de vídeo público (lançamento, demo): baixe só o pedaço que vai usar, cite a fonte e use poucos segundos. Peça
autorização antes de baixar qualquer coisa que não seja oficial.

## Dados pessoais

Antes de usar qualquer material: tem nome de cliente, telefone, e-mail, conversa, saldo, endereço? Borre com o
`borrar()` do motor (um retângulo desfocado por cima) ou recorte.

## Conferir os fatos

Todo número, data e nome que aparece na tela precisa de fonte. Se não achar a fonte, a frase não ganha texto na tela.
