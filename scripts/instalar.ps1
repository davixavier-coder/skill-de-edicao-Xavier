# Instala a edição Xavier (Windows). Roda de novo sem problema: só faz o que falta.
# powershell -ExecutionPolicy Bypass -File instalar.ps1
$ErrorActionPreference = "Continue"
$S = Split-Path -Parent $PSScriptRoot
$faltou = $false
function Ok($m) { Write-Host "OK: $m" }
function Falta($m) { Write-Host "FALTA: $m"; $script:faltou = $true }

Write-Host "== conferindo o computador"
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) { $v = [int](& node -p "process.versions.node.split('.')[0]"); if ($v -ge 22) { Ok "Node $(node -v)" } else { Falta "Node 22+ (baixe em nodejs.org)" } } else { Falta "Node 22+ (baixe em nodejs.org)" }
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) { Ok "FFmpeg" } else { Falta "FFmpeg: winget install Gyan.FFmpeg" }
$py = $null
foreach ($c in @(@{exe="py"; pre=@("-3.12")}, @{exe="py"; pre=@("-3.11")}, @{exe="py"; pre=@("-3.13")}, @{exe="python"; pre=@()})) {
  $cmd = Get-Command $c.exe -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -notlike "*\WindowsApps\*") {
    $pre = $c.pre
    & $c.exe @pre -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $c; break }
  }
}
if ($py) { Ok "Python" } else { Falta "Python 3.10 a 3.13 (python.org, marque 'Add to PATH')" }
if ($faltou) { Write-Host "Instale o que falta e rode de novo."; exit 1 }

Write-Host "== ambiente Python da skill (Whisper + OpenCV)"
$venvPy = Join-Path $S "ambiente\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { $pre = $py.pre; & $py.exe @pre -m venv (Join-Path $S "ambiente") }
& $venvPy -m pip install -q --upgrade pip
& $venvPy -m pip install -q numpy opencv-python-headless
& $venvPy -m pip install -q faster-whisper
if ($LASTEXITCODE -ne 0) { & $venvPy -m pip install -q openai-whisper }
Ok "Whisper e OpenCV"

Write-Host "== detector de rosto"
New-Item -ItemType Directory -Force -Path (Join-Path $S "modelos") | Out-Null
$yu = Join-Path $S "modelos\yunet.onnx"
if (-not (Test-Path $yu) -or (Get-Item $yu).Length -lt 100000) {
  Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx" -OutFile $yu
}
Ok "detector de rosto"

Write-Host "== fonte Inter"
$inter = Join-Path $S "motor\Inter.woff2"
if (-not (Test-Path $inter)) {
  $t = Join-Path $env:TEMP "inter-xavier"; New-Item -ItemType Directory -Force -Path $t | Out-Null
  try {
    Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip" -OutFile "$t\inter.zip"
    Expand-Archive -Force "$t\inter.zip" "$t\x"
    $f = Get-ChildItem -Recurse "$t\x" -Filter "InterVariable.woff2" | Select-Object -First 1
    if ($f) { Copy-Item $f.FullName $inter }
  } catch { Write-Host "AVISO: Inter não baixou; o vídeo usa a Inter do Google Fonts" }
}

Write-Host "== sons"
& $venvPy (Join-Path $S "scripts\sons.py") (Join-Path $S "sons") | Out-Null
Ok "sons gerados"

Write-Host "== HyperFrames"
if (-not (Test-Path "$HOME\.claude\skills\hyperframes\SKILL.md")) { npx -y skills add heygen-com/hyperframes -g -y }
Write-Host ""
Write-Host "TUDO PRONTO"
