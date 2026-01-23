param(
  [Parameter(Mandatory=$true)][string]$ModelPath,
  [string]$BindHost = '127.0.0.1',
  [int]$Port = 8001
)

$ErrorActionPreference = 'Stop'

# This script expects a llama.cpp server binary OR llama-cpp-python installed.
# Option A: llama.cpp binary
$llamaServer = Get-Command 'llama-server' -ErrorAction SilentlyContinue
if ($llamaServer) {
  Write-Host "Starting llama-server (binary)..." -ForegroundColor Cyan
  & $llamaServer.Source --model "$ModelPath" --host $BindHost --port $Port
  exit 0
}

# Option B: llama-cpp-python server
Write-Host "llama-server not found; trying llama-cpp-python server..." -ForegroundColor Yellow

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
  $python = 'python'
}

& $python -m pip show llama-cpp-python | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing llama-cpp-python (this can take a while)..." -ForegroundColor Yellow
  & $python -m pip install llama-cpp-python
}

Write-Host "Starting llama-cpp-python OpenAI server..." -ForegroundColor Cyan
Write-Host "Endpoint: http://${BindHost}:$Port/v1" -ForegroundColor Cyan

# llama-cpp-python provides an OpenAI-compatible server module in most builds.
& $python -m llama_cpp.server --model "$ModelPath" --host $BindHost --port $Port
