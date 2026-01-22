#!/bin/bash
# Deploy Qwen2.5-VL-72B locally using SGLang with ROCm support
# For AMD Ryzen AI MAX+ 395 with Radeon 8060S (128GB unified memory)

set -e

echo "=== Qwen2.5-VL-72B Deployment Script ==="
echo "Target: AMD Ryzen AI MAX+ 395 (ROCm backend)"
echo ""

# Configuration
MODEL_NAME="Qwen/Qwen2.5-VL-72B-Instruct"
QUANT_MODEL_NAME="${VISION_MODEL_QUANT_NAME:-}"
QUANTIZATION="gptq"  # INT4 quantization (~14-18GB VRAM)
HOST="127.0.0.1"
PORT=8000
MEM_FRACTION=0.75  # Use 75% of 128GB (~96GB for model)

echo "Configuration:"
echo "  Model: $MODEL_NAME"
echo "  Quantization: $QUANTIZATION (INT4)"
if [ -n "$QUANT_MODEL_NAME" ]; then
  echo "  Quantized model repo: $QUANT_MODEL_NAME"
fi
echo "  Endpoint: http://$HOST:$PORT/v1"
echo "  Memory allocation: ${MEM_FRACTION}% of 128GB"
echo ""

# Step 1: Check Python environment
echo "[1/5] Checking Python environment..."
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Step 2: Install SGLang with ROCm support
echo "[2/5] Installing SGLang with ROCm support..."
echo "This may take several minutes..."

# Note: Adjust ROCm version based on your system
# Check with: rocminfo | grep "Marketing Name"
pip install "sglang[all]" --extra-index-url https://download.pytorch.org/whl/rocm6.0

echo "✓ SGLang installed"
echo ""

# Step 3: Download model from HuggingFace
echo "[3/5] Downloading Qwen2.5-VL-72B-Instruct..."
echo "This will download ~145GB. Ensure you have sufficient disk space."
echo ""

# Check if huggingface-cli is available
if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface-cli..."
    pip install huggingface_hub[cli]
fi

# Select model repo to download
DOWNLOAD_MODEL="$MODEL_NAME"
if [ "$QUANTIZATION" != "none" ] && [ -n "$QUANT_MODEL_NAME" ]; then
  DOWNLOAD_MODEL="$QUANT_MODEL_NAME"
fi

# Download model (will skip if already downloaded)
MODEL_DIR="./models/$(basename $DOWNLOAD_MODEL)"
huggingface-cli download $DOWNLOAD_MODEL --local-dir "$MODEL_DIR"

echo "✓ Model downloaded to ./models/$(basename $MODEL_NAME)"
echo ""

# Step 4: Create launch script
echo "[4/5] Creating launch script..."

cat > launch_vision_model.sh << 'LAUNCH_SCRIPT'
#!/bin/bash
# Launch Qwen2.5-VL-72B with SGLang

MODEL_PATH="$MODEL_DIR"
HOST="127.0.0.1"
PORT=8000
MEM_FRACTION=0.75

echo "Launching Qwen2.5-VL-72B..."
echo "Endpoint will be available at: http://$HOST:$PORT/v1"
echo ""
echo "Expected startup time: 2-5 minutes"
echo "Expected inference time: 2-5 minutes per image comparison"
echo ""

python -m sglang.launch_server \
  --model-path "$MODEL_PATH" \
  --quantization gptq \
  --host "$HOST" \
  --port "$PORT" \
  --device rocm \
  --mem-fraction-static "$MEM_FRACTION" \
  --trust-remote-code \
  --chat-template qwen2.5-vl

# Alternative: Use vLLM instead of SGLang
# Uncomment below and comment above if SGLang has issues
#
# vllm serve "$MODEL_PATH" \
#   --quantization gptq \
#   --dtype half \
#   --max-model-len 32768 \
#   --gpu-memory-utilization 0.75 \
#   --trust-remote-code \
#   --device rocm
LAUNCH_SCRIPT

chmod +x launch_vision_model.sh

echo "✓ Launch script created: launch_vision_model.sh"
echo ""

# Step 5: Create systemd service (optional)
echo "[5/5] Creating systemd service (optional)..."

cat > qwen-vision.service << 'SERVICE'
[Unit]
Description=Qwen2.5-VL-72B Vision Model Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/path/to/colossus_blender_mcp
ExecStart=/path/to/colossus_blender_mcp/launch_vision_model.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

echo "✓ Systemd service template created: qwen-vision.service"
echo "  To install: sudo cp qwen-vision.service /etc/systemd/system/"
echo "  Edit paths in the service file first!"
echo ""

# Deployment complete
echo "==================================="
echo "✓ Deployment Complete!"
echo "==================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Launch the vision model server:"
echo "   ./launch_vision_model.sh"
echo ""
echo "2. Wait for startup (2-5 minutes)"
echo ""
echo "3. Test the connection:"
echo "   python test_vision_model.py"
echo ""
echo "4. Update .env file:"
echo "   VISION_MODEL_ENDPOINT=http://localhost:8000/v1"
echo ""
echo "Troubleshooting:"
echo "- Check GPU: rocminfo | grep 'Marketing Name'"
echo "- Monitor VRAM: watch -n 1 'rocm-smi'"
echo "- View logs: journalctl -u qwen-vision -f"
echo ""
