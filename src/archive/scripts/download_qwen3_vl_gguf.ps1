param(
  [ValidateSet('8B','30B')][string]$Size = '8B',
  [string]$Quant = $env:QWEN3_GGUF_QUANT
)

$ErrorActionPreference = 'Stop'

if (-not $Quant) { $Quant = 'Q4_K_M' }

$root = Split-Path -Parent $PSScriptRoot
$modelsDir = Join-Path $root 'models'
New-Item -ItemType Directory -Force -Path $modelsDir | Out-Null

# Use a small python helper to pick repo + filename
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
  $python = 'python'
}

Write-Host "Selecting GGUF repo for Qwen3-VL-$Size ($Quant)..." -ForegroundColor Cyan
$env:QWEN3_GGUF_QUANT = $Quant
$selection = & $python (Join-Path $PSScriptRoot 'hf_find_qwen3_vl_gguf.py')
$selectionText = $selection | Out-String

# Parse the printed section
$patternRepo = "Target: Qwen3-VL-$Size\s+Repo: (.+)\s+GGUF: (.+)"
$match = [regex]::Match($selectionText, $patternRepo, [System.Text.RegularExpressions.RegexOptions]::Multiline)
if (-not $match.Success) {
  throw "Could not parse repo/gguf selection. Run scripts/hf_find_qwen3_vl_gguf.py manually to inspect output."
}

$repo = $match.Groups[1].Value.Trim()
$gguf = $match.Groups[2].Value.Trim()
if ($gguf -eq '<not found>' -or $gguf -like '*no .gguf*') {
  throw "No GGUF file detected for $repo. Try a different quant or adjust search terms."
}

$folder = ($repo.Split('/') | Select-Object -Last 1)
$targetDir = Join-Path $modelsDir $folder
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

Write-Host "Downloading $repo ($gguf) to $targetDir" -ForegroundColor Yellow

# Ensure HF token is present (from env or .env)
if (-not $env:HUGGINGFACE_TOKEN) {
  $envPath = Join-Path $root '.env'
  if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    $tokMatch = [regex]::Match($envContent, "(?m)^HUGGINGFACE_TOKEN=(.+)$")
    if ($tokMatch.Success) {
      $env:HUGGINGFACE_TOKEN = $tokMatch.Groups[1].Value.Trim().Trim('"').Trim("'")
    }
  }
}

# huggingface-cli reads HUGGINGFACE_HUB_TOKEN; set it for compatibility
if ($env:HUGGINGFACE_TOKEN -and -not $env:HUGGINGFACE_HUB_TOKEN) {
  $env:HUGGINGFACE_HUB_TOKEN = $env:HUGGINGFACE_TOKEN
}

try {
  huggingface-cli --help | Out-Null
} catch {
  Write-Host "Installing huggingface-cli..." -ForegroundColor Yellow
  & $python -m pip install huggingface_hub[cli]
}

huggingface-cli download $repo --include "$gguf" --local-dir $targetDir --local-dir-use-symlinks False

Write-Host "Done." -ForegroundColor Green
Write-Host "Model path: $targetDir\$gguf" -ForegroundColor Green
