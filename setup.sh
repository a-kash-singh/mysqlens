#!/bin/bash

# MySQLens Quick Setup Script
# Inspired by OptiSchema-Slim

set -e

echo "🚀 MySQLens Quick Setup"
echo "======================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for Docker Compose V2 (built into Docker CLI)
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose V2 found (docker compose)"
    COMPOSE_CMD="docker compose"
# Fallback to V1 if V2 not available
elif command -v docker-compose &> /dev/null; then
    echo "⚠️  Docker Compose V1 found (docker-compose)"
    echo "   Consider upgrading to Docker Compose V2"
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose is not installed."
    echo "   Install Docker Desktop which includes Compose V2"
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file to configure your LLM provider"
    echo ""
    echo "   Recommended: Use Ollama for local, private AI (no API key needed!)"
    echo "   1. Install Ollama: brew install ollama"
    echo "   2. Start Ollama: ollama serve"
    echo "   3. Pull model: ollama pull llama3.2:latest"
    echo "   4. LLM_PROVIDER is already set to 'ollama' in .env"
    echo ""
    echo "   Or use cloud providers:"
    echo "   - For OpenAI: Set LLM_PROVIDER=openai and add OPENAI_API_KEY"
    echo "   - For Gemini: Set LLM_PROVIDER=gemini and add GEMINI_API_KEY"
    echo "   - For DeepSeek: Set LLM_PROVIDER=deepseek and add DEEPSEEK_API_KEY"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Build and start services
echo "🔨 Building Docker images..."
$COMPOSE_CMD build

echo ""
echo "🚀 Starting services..."
$COMPOSE_CMD up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if services are running
if $COMPOSE_CMD ps | grep -q "Up"; then
    echo ""
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Access the application:"
    echo "   - Frontend Dashboard: http://localhost:3000"
    echo "   - Backend API: http://localhost:8080"
    echo "   - API Documentation: http://localhost:8080/docs"
    echo ""
    echo "📊 View logs:"
    echo "   $COMPOSE_CMD logs -f"
    echo ""
    echo "🛑 Stop services:"
    echo "   $COMPOSE_CMD down"
    echo ""
    echo "📚 Next steps:"
    echo "   - See QUICK_START.md for detailed guide"
    echo "   - Configure Ollama for local AI (recommended)"
    echo "   - Connect to your MySQL database"
    echo ""
    echo "🎉 Setup complete! Happy optimizing!"
else
    echo ""
    echo "❌ Services failed to start. Check logs with:"
    echo "   $COMPOSE_CMD logs"
    exit 1
fi
