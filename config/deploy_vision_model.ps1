# Deploy Qwen2.5-VL-72B locally using SGLang with ROCm support
# For AMD Ryzen AI MAX+ 395 with Radeon 8060S (128GB unified memory)
# PowerShell version for Windows

$ErrorActionPreference = "Stop"

Write-Host "=== Qwen2.5-VL-72B Deployment Script ===" -ForegroundColor Cyan
Write-Host "Target: AMD Ryzen AI MAX+ 395 (ROCm backend)"
Write-Host ""

# Configuration
$MODEL_NAME = "Qwen/Qwen2.5-VL-72B-Instruct"
$QUANT_MODEL_NAME = $env:VISION_MODEL_QUANT_NAME  # Optional: quantized model repo (e.g., GPTQ)
$QUANTIZATION = "gptq"  # INT4 quantization (~14-18GB VRAM)
$HOST = "127.0.0.1"
$PORT = 8000
$MEM_FRACTION = 0.75  # Use 75% of 128GB (~96GB for model)

Write-Host "Configuration:"
Write-Host "  Model: $MODEL_NAME"
Write-Host "  Quantization: $QUANTIZATION (INT4)"
if ($QUANT_MODEL_NAME) {
    Write-Host "  Quantized model repo: $QUANT_MODEL_NAME"
}
Write-Host "  Endpoint: http://$($HOST):$PORT/v1"
Write-Host "  Memory allocation: $($MEM_FRACTION*100)% of 128GB"
Write-Host ""

# Step 1: Check Python environment
Write-Host "[1/5] Checking Python environment..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Install SGLang with ROCm support
Write-Host "[2/5] Installing SGLang with ROCm support..." -ForegroundColor Yellow
Write-Host "This may take several minutes..."

# For Windows with AMD GPU, we need ROCm-compatible PyTorch
# Note: ROCm on Windows is experimental - you may need WSL2
Write-Host ""
Write-Host "⚠ IMPORTANT: ROCm on Windows requires WSL2" -ForegroundColor Yellow
Write-Host "If you haven't set up WSL2 with ROCm, please follow these steps:" -ForegroundColor Yellow
Write-Host "1. Install WSL2: wsl --install"
Write-Host "2. Install Ubuntu: wsl --install -d Ubuntu-22.04"
Write-Host "3. Run this script inside WSL2 using the .sh version"
Write-Host ""

$response = Read-Host "Do you want to continue with Windows native installation? (experimental) [y/N]"
if ($response -ne "y") {
    Write-Host "Deployment cancelled. Please use WSL2 for ROCm support."
    exit 0
}

# Windows native installation (may fall back to CPU)
pip install "sglang[all]"

Write-Host "✓ SGLang installed" -ForegroundColor Green
Write-Host ""

# Step 3: Download model from HuggingFace
Write-Host "[3/5] Downloading Qwen2.5-VL-72B-Instruct..." -ForegroundColor Yellow
Write-Host "This will download ~145GB. Ensure you have sufficient disk space."
Write-Host ""

# Install huggingface-cli if not present
try {
    huggingface-cli --version | Out-Null
} catch {
    Write-Host "Installing huggingface-cli..."
    pip install huggingface_hub[cli]
}

# Select model repo to download
$downloadModel = $MODEL_NAME
if ($QUANTIZATION -ne "none" -and $QUANT_MODEL_NAME) {
    $downloadModel = $QUANT_MODEL_NAME
}

# Create models directory
$modelFolder = [System.IO.Path]::GetFileName($downloadModel)
$modelsDir = ".\models\$modelFolder"
if (-not (Test-Path $modelsDir)) {
    New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null
}

# Download model
huggingface-cli download $downloadModel --local-dir $modelsDir

Write-Host "✓ Model downloaded to $modelsDir" -ForegroundColor Green
Write-Host ""

# Step 4: Create launch script
Write-Host "[4/5] Creating launch script..." -ForegroundColor Yellow

$launchScript = @"
# Launch Qwen2.5-VL-72B with SGLang
`$MODEL_PATH = ".\models\$modelFolder"
`$HOST = "127.0.0.1"
`$PORT = 8000
`$MEM_FRACTION = 0.75

Write-Host "Launching Qwen2.5-VL-72B..."
Write-Host "Endpoint will be available at: http://`$($HOST):`$PORT/v1"
Write-Host ""
Write-Host "Expected startup time: 2-5 minutes"
Write-Host "Expected inference time: 2-5 minutes per image comparison"
Write-Host ""

python -m sglang.launch_server ``
  --model-path "`$MODEL_PATH" ``
  --quantization gptq ``
  --host "`$HOST" ``
  --port `$PORT ``
  --device rocm ``
  --mem-fraction-static `$MEM_FRACTION ``
  --trust-remote-code ``
  --chat-template qwen2.5-vl

# If ROCm doesn't work on Windows, fall back to CPU (will be slow)
# python -m sglang.launch_server ``
#   --model-path "`$MODEL_PATH" ``
#   --quantization gptq ``
#   --host "`$HOST" ``
#   --port `$PORT ``
#   --device cpu ``
#   --trust-remote-code ``
#   --chat-template qwen2.5-vl
"@

$launchScript | Out-File -FilePath "launch_vision_model.ps1" -Encoding utf8

Write-Host "✓ Launch script created: launch_vision_model.ps1" -ForegroundColor Green
Write-Host ""

# Step 5: Update .env file
Write-Host "[5/5] Updating .env file..." -ForegroundColor Yellow

$envFile = ".\.env"
$envContent = Get-Content $envFile -Raw

if ($envContent -notmatch "VISION_MODEL_ENDPOINT") {
    Add-Content -Path $envFile -Value "`nVISION_MODEL_ENDPOINT=http://localhost:8000/v1"
    Write-Host "✓ Added VISION_MODEL_ENDPOINT to .env" -ForegroundColor Green
} else {
    Write-Host "✓ VISION_MODEL_ENDPOINT already exists in .env" -ForegroundColor Green
}
Write-Host ""

# Deployment complete
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:"
Write-Host ""
Write-Host "1. Launch the vision model server:"
Write-Host "   .\launch_vision_model.ps1"
Write-Host ""
Write-Host "2. Wait for startup (2-5 minutes)"
Write-Host ""
Write-Host "3. Test the connection:"
Write-Host "   python test_vision_model.py"
Write-Host ""
Write-Host "⚠ IMPORTANT FOR AMD GPU:" -ForegroundColor Yellow
Write-Host "ROCm on Windows is experimental. For best results:" -ForegroundColor Yellow
Write-Host "1. Use WSL2 with Ubuntu"
Write-Host "2. Run the .sh version of this script in WSL2"
Write-Host "3. Your AMD Ryzen AI MAX+ 395 will work best in Linux"
Write-Host ""
Write-Host "Alternative: Use cloud vision API temporarily" -ForegroundColor Yellow
Write-Host "Set in .env: VISION_MODEL_ENDPOINT=https://api.example.com/v1"
Write-Host ""
