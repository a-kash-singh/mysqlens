#!/bin/bash

# OptiSchema-MySQL Quick Setup Script

set -e

echo "🚀 OptiSchema-MySQL Quick Setup"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file to configure your LLM provider"
    echo "   - For Ollama (local): Set LLM_PROVIDER=ollama"
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
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Access the application:"
    echo "   - Frontend Dashboard: http://localhost:3000"
    echo "   - Backend API: http://localhost:8080"
    echo "   - API Documentation: http://localhost:8080/docs"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Stop services:"
    echo "   docker-compose down"
    echo ""
    echo "🎉 Setup complete! Happy optimizing!"
else
    echo ""
    echo "❌ Services failed to start. Check logs with:"
    echo "   docker-compose logs"
    exit 1
fi
