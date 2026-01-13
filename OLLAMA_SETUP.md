# Ollama Setup Guide for MySQLens

This guide will help you set up local LLM support using Ollama for complete data privacy and offline analysis.

## Why Use Ollama?

- **Complete Privacy**: Your schema and queries never leave your machine
- **No API Costs**: No per-request charges or subscription fees
- **Offline Capable**: Works without internet connection
- **Fast**: No network latency, responses are instant
- **Control**: Choose and customize your models

## Installation

### macOS

```bash
brew install ollama
```

Or download from: https://ollama.com/download

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows

Download the installer from: https://ollama.com/download

### Docker (Alternative)

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

## Starting Ollama

```bash
# Start the Ollama service
ollama serve
```

The service will run on `http://localhost:11434` by default.

## Choosing a Model

### Recommended Models for MySQLens

| Model | Size | Best For | Command |
|-------|------|----------|---------|
| **llama3.2:latest** | 4.7GB | General SQL analysis, best balance | `ollama pull llama3.2:latest` |
| **sqlcoder:7b** | 4.1GB | SQL-specialized tasks | `ollama pull sqlcoder:7b` |
| **llama3.2:1b** | 1.3GB | Limited hardware, fast responses | `ollama pull llama3.2:1b` |
| **deepseek-coder-v2** | 8.9GB | Complex optimization, best quality | `ollama pull deepseek-coder-v2` |

### Pulling a Model

```bash
# Start with the recommended model
ollama pull llama3.2:latest

# Or choose a SQL-specialized model
ollama pull sqlcoder:7b
```

This will download the model. First-time downloads take a few minutes depending on your internet speed.

## Configuring MySQLens

### 1. Update .env File

```bash
# Set Ollama as the provider
LLM_PROVIDER=ollama

# Configure Ollama connection
OLLAMA_BASE_URL=http://host.docker.internal:11434  # For Docker
OLLAMA_MODEL=llama3.2:latest                        # Your chosen model
```

**Note:**
- Use `http://host.docker.internal:11434` when running MySQLens in Docker
- Use `http://localhost:11434` for local development (no Docker)

### 2. Verify Configuration

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Should return a JSON list of installed models
```

### 3. Test with a Simple Query

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:latest",
  "prompt": "Explain what a database index is in one sentence.",
  "stream": false
}'
```

## Starting MySQLens with Ollama

### Using Docker Compose

```bash
# Make sure Ollama is running first
ollama serve

# In another terminal, start MySQLens
docker compose up -d

# Check logs
docker compose logs -f backend
```

You should see: `Creating Ollama provider for local LLM`

### Local Development

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Frontend (new terminal)
cd frontend
npm run dev
```

## Troubleshooting

### Ollama Connection Issues

**Problem:** "Cannot connect to Ollama. Is it running?"

**Solutions:**
1. Verify Ollama is running: `curl http://localhost:11434/api/tags`
2. Check if port 11434 is accessible
3. For Docker, ensure `host.docker.internal` resolves correctly
4. On Linux in Docker, you may need to use `http://172.17.0.1:11434` instead

### Model Not Found

**Problem:** "Model 'xyz' not found"

**Solution:**
```bash
# List installed models
ollama list

# Pull the model you specified in .env
ollama pull llama3.2:latest
```

### Slow Responses

**Problem:** Ollama takes too long to respond

**Solutions:**
1. Use a smaller model: `llama3.2:1b` instead of larger models
2. Ensure your machine has enough RAM (8GB minimum, 16GB recommended)
3. Close other resource-intensive applications
4. Consider using GPU acceleration if available

### Docker Networking Issues on Linux

**Problem:** Docker can't reach Ollama on `host.docker.internal`

**Solution:**
```bash
# Find your host machine's Docker network IP
ip addr show docker0

# Update .env to use that IP
OLLAMA_BASE_URL=http://172.17.0.1:11434

# Or run Ollama in Docker network mode
docker run -d --network=host -v ollama:/root/.ollama --name ollama ollama/ollama
```

## Performance Tuning

### Model Parameters

You can customize model behavior by editing `backend/llm/ollama_provider.py`:

```python
"options": {
    "temperature": 0.2,  # Lower = more deterministic (0.0-1.0)
    "num_predict": 2000, # Max tokens to generate
    "top_k": 40,         # Sampling parameter
    "top_p": 0.9,        # Nucleus sampling
}
```

### Hardware Recommendations

- **Minimum**: 8GB RAM, 4-core CPU
- **Recommended**: 16GB RAM, 8-core CPU
- **Optimal**: 32GB RAM, GPU with 8GB+ VRAM

## Model Comparisons

### Performance vs. Quality

| Model | Speed | Quality | Privacy | Cost |
|-------|-------|---------|---------|------|
| llama3.2:1b | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free |
| llama3.2:latest | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free |
| sqlcoder:7b | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free |
| deepseek-coder-v2 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free |
| GPT-4 (cloud) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | $$$$ |

## Advanced: Custom Models

You can fine-tune or customize models for your specific use case:

```bash
# Create a custom model with specific parameters
ollama create mysqlens-custom -f Modelfile

# Example Modelfile:
# FROM llama3.2:latest
# SYSTEM You are a MySQL performance expert specializing in query optimization.
# PARAMETER temperature 0.1
# PARAMETER num_predict 2000
```

## Getting Help

- **Ollama Documentation**: https://github.com/ollama/ollama
- **MySQLens Issues**: https://github.com/a-kash-singh/mysqlens/issues
- **Model Library**: https://ollama.com/library

## Next Steps

1. Start analyzing your MySQL queries with complete privacy
2. Experiment with different models to find the best fit
3. Monitor performance and adjust settings as needed
4. Share your experience with the community!

---

**Built with privacy in mind** 🔒
