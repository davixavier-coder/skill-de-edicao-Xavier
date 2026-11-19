#!/usr/bin/env bash
# Instala a edição Xavier (Mac e Linux). Roda de novo sem problema: só faz o que falta.
set -u
S="$(cd "$(dirname "$0")/.." && pwd)"
ok() { echo "OK: $1"; }
falta() { echo "FALTA: $1"; FALTOU=1; }
FALTOU=0

echo "== conferindo o computador"
if command -v node >/dev/null 2>&1; then
  v=$(node -p 'process.versions.node.split(".")[0]')
  if [ "$v" -ge 22 ]; then ok "Node $(node -v)"; else falta "Node 22 ou mais novo (tem $(node -v)): baixe em nodejs.org"; fi
else falta "Node 22+: baixe em nodejs.org"; fi
command -v ffmpeg >/dev/null 2>&1 && ok "FFmpeg" || falta "FFmpeg (Mac: brew install ffmpeg)"
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] && ok "Python ($($PY --version))" || falta "Python 3.10+: baixe em python.org"
if [ -d "/Applications/Google Chrome.app" ] || command -v google-chrome >/dev/null 2>&1; then ok "Chrome"
else echo "AVISO: sem Google Chrome, a captura de sites não funciona"; fi
[ "$FALTOU" = 1 ] && { echo "Instale o que falta e rode de novo."; exit 1; }

echo "== ambiente Python da skill (Whisper + OpenCV)"
if [ ! -x "$S/ambiente/bin/python" ]; then "$PY" -m venv "$S/ambiente" || { echo "não consegui criar o ambiente Python"; exit 1; }; fi
"$S/ambiente/bin/python" -m pip install -q --upgrade pip
"$S/ambiente/bin/python" -m pip install -q numpy opencv-python-headless
if ! "$S/ambiente/bin/python" -m pip install -q faster-whisper; then
  echo "faster-whisper não instalou, usando o openai-whisper"
  "$S/ambiente/bin/python" -m pip install -q openai-whisper || { echo "o Whisper não instalou"; exit 1; }
fi
ok "Whisper e OpenCV"

echo "== detector de rosto (YuNet, OpenCV Zoo)"
mkdir -p "$S/modelos"
if [ ! -s "$S/modelos/yunet.onnx" ] || [ "$(wc -c < "$S/modelos/yunet.onnx")" -lt 100000 ]; then
  curl -fsSL -o "$S/modelos/yunet.onnx" https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx \
    || { echo "não consegui baixar o detector de rosto"; exit 1; }
fi
ok "detector de rosto"

echo "== fonte Inter (oficial, rsms/inter, licença OFL)"
if [ ! -s "$S/motor/Inter.woff2" ]; then
  T=$(mktemp -d)
  if curl -fsSL -o "$T/inter.zip" https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip && unzip -q -o "$T/inter.zip" -d "$T/x"; then
    f=$(find "$T/x" -name "InterVariable.woff2" | head -1); [ -n "$f" ] && cp "$f" "$S/motor/Inter.woff2"
  fi
  rm -rf "$T"
fi
[ -s "$S/motor/Inter.woff2" ] && ok "Inter" || echo "AVISO: Inter não baixou; o vídeo usa a Inter do Google Fonts"

echo "== sons"
"$S/ambiente/bin/python" "$S/scripts/sons.py" "$S/sons" >/dev/null && ok "sons gerados"

echo "== HyperFrames (skills oficiais da HeyGen)"
if [ ! -f "$HOME/.claude/skills/hyperframes/SKILL.md" ]; then
  npx -y skills add heygen-com/hyperframes -g -y || echo "AVISO: rode à mão: npx skills add heygen-com/hyperframes"
fi
npx -y hyperframes --version >/dev/null 2>&1 && ok "HyperFrames" || echo "AVISO: npx hyperframes não respondeu; rode: npx hyperframes doctor"

echo ""
echo "TUDO PRONTO"
