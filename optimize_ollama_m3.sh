#!/bin/bash

# 🚀 Ollama Optimization Script for Mac M3
# Maximize performance for Apple Silicon

echo "🔧 Optimizing Ollama for Mac M3..."

# Stop current Ollama service
echo "⏹️  Stopping Ollama service..."
pkill -f ollama
sleep 2

# Set optimal environment variables for M3
export OLLAMA_FLASH_ATTENTION=true
export OLLAMA_LLM_LIBRARY=metal
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_KEEP_ALIVE=5m0s
export OLLAMA_CONTEXT_LENGTH=4096

# Create optimized config file
mkdir -p ~/.ollama
cat > ~/.ollama/config.env << EOF
# Mac M3 Optimizations
OLLAMA_FLASH_ATTENTION=true
OLLAMA_LLM_LIBRARY=metal
OLLAMA_GPU_OVERHEAD=0
OLLAMA_NUM_PARALLEL=1
OLLAMA_KEEP_ALIVE=5m0s
OLLAMA_CONTEXT_LENGTH=4096
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_LOAD_TIMEOUT=5m0s
EOF

echo "✅ Configuration optimized for M3!"
echo "📊 Settings applied:"
echo "   • Flash Attention: ENABLED"
echo "   • Metal Library: ENABLED" 
echo "   • GPU Overhead: MINIMIZED"
echo "   • Parallel Processing: OPTIMIZED"

# Start Ollama with optimized settings
echo "🚀 Starting Ollama with M3 optimizations..."
ollama serve &

echo "⏳ Waiting for service to start..."
sleep 5

# Test the configuration
echo "🧪 Testing optimized configuration..."
ollama list

echo "🎉 Ollama optimized for Mac M3!"
echo "💡 Tip: Use 'ollama run qwen3-coder:latest' for best performance"
