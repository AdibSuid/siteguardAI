# 🦙 Using Local LLMs with Ollama

SiteGuard AI now supports **free, local LLMs** using Ollama! No API keys required.

## Quick Setup

### 1. Install Ollama

**Windows:**
```powershell
# Download and install from: https://ollama.ai/download/windows
# Or use winget:
winget install Ollama.Ollama
```

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama Service

Ollama should start automatically after installation. Verify it's running:

```bash
# Check if Ollama is running
curl http://localhost:11434
```

### 3. Download a Model

Choose one of these models:

```bash
# Llama 3 (recommended, ~4.7GB)
ollama pull llama3

# Llama 3.1 (larger, better quality, ~8GB)
ollama pull llama3.1

# Mistral (smaller, faster, ~4.1GB)
ollama pull mistral

# Phi-3 (smallest, ~2.3GB)
ollama pull phi3

# Gemma 2 (Google, ~5GB)
ollama pull gemma2
```

### 4. Verify Installation

```bash
# List downloaded models
ollama list

# Test the model
ollama run llama3 "Write a short safety report"
```

### 5. Configure SiteGuard AI

The app is already configured to use Ollama by default! Just start it:

```bash
streamlit run app/web/streamlit_app.py
```

Or update `.env` if needed:
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

## Model Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **llama3** | 4.7GB | Fast | Excellent | ✅ Recommended |
| llama3.1 | 8GB | Medium | Best | High quality reports |
| mistral | 4.1GB | Very Fast | Good | Quick processing |
| phi3 | 2.3GB | Fastest | Good | Low-end systems |
| gemma2 | 5GB | Fast | Excellent | Alternative to Llama |

## Advantages

✅ **100% Free** - No API costs
✅ **Private** - All data stays on your machine
✅ **Offline** - No internet required
✅ **Fast** - Local processing
✅ **No Rate Limits** - Generate unlimited reports

## System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5-10GB for models
- **CPU**: Modern multi-core processor
- **GPU**: Optional (but faster with NVIDIA GPU)

## Troubleshooting

### Ollama not connecting
```bash
# Check if Ollama is running
curl http://localhost:11434

# Restart Ollama service
# Windows: Restart from System Tray
# macOS/Linux: 
sudo systemctl restart ollama
```

### Model not found
```bash
# Pull the model first
ollama pull llama3

# Verify it's installed
ollama list
```

### Out of memory
```bash
# Use a smaller model
ollama pull phi3

# Or configure in config.yaml:
llm:
  model: "phi3"
```

### Slow generation
- Use a smaller model (phi3 or mistral)
- Enable GPU acceleration if available
- Close other applications

## Advanced: GPU Acceleration

Ollama automatically uses GPU if available (NVIDIA CUDA, AMD ROCm, or Apple Metal).

**Check GPU usage:**
```bash
# While generating a report
nvidia-smi  # For NVIDIA
```

## Switching Providers

In the Streamlit app sidebar, you can switch between:
- **Ollama** (Local, Free)
- **OpenAI** (Cloud, Paid - Requires API key)
- **Gemini** (Cloud, Paid - Requires API key)

## Additional Models

Browse all available models:
https://ollama.ai/library

```bash
# Code-specific models
ollama pull codellama

# Multimodal (vision + text)
ollama pull llava

# Uncensored models
ollama pull dolphin-mistral
```

## Performance Tips

1. **Keep Ollama running** - Startup takes a few seconds
2. **Use SSD** - Faster model loading
3. **Increase RAM** - Better performance
4. **Use GPU** - 10-50x faster generation
5. **Pre-download models** - Don't wait during first use

## Example Usage

```python
from app.core.llm.generator import create_report_generator

# Create Ollama generator
generator = create_report_generator({
    "provider": "ollama",
    "model": "llama3"
})

# Generate report
report = generator.generate_report(
    violations=violations,
    metadata=metadata
)
```

---

**🎉 You're now running completely free, local AI for report generation!**

No API keys. No cloud. No costs. Just AI on your machine.
