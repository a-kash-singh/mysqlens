#!/bin/bash

# Automated Ollama Installation Script for MySQLens
# Supports macOS, Linux, and provides guidance for Windows
# Inspired by the local-first philosophy of OptiSchema-Slim

set -e

OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:latest}"
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════╗
║                                               ║
║     🔒 MySQLens Local AI Setup (Ollama)      ║
║                                               ║
║   Complete Privacy • Zero API Costs          ║
║   Your data never leaves localhost           ║
║                                               ║
╚═══════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)

echo -e "${BLUE}📋 Detected OS: ${BOLD}${OS}${NC}"
echo ""

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is already installed!${NC}"
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n1 || echo "unknown")
    echo -e "${BLUE}   Version: ${OLLAMA_VERSION}${NC}"
    echo ""
else
    echo -e "${YELLOW}📦 Ollama not found. Installing...${NC}"
    echo ""

    case $OS in
        macos)
            if command -v brew &> /dev/null; then
                echo -e "${BLUE}🍺 Installing Ollama via Homebrew...${NC}"
                brew install ollama
            else
                echo -e "${YELLOW}⚠️  Homebrew not found. Installing via official script...${NC}"
                curl -fsSL https://ollama.com/install.sh | sh
            fi
            ;;
        linux)
            echo -e "${BLUE}🐧 Installing Ollama on Linux...${NC}"
            curl -fsSL https://ollama.com/install.sh | sh
            ;;
        windows)
            echo -e "${RED}❌ Automated Windows installation not supported${NC}"
            echo -e "${YELLOW}📥 Please download Ollama from: https://ollama.com/download${NC}"
            echo -e "${YELLOW}   Then run this script again.${NC}"
            exit 1
            ;;
        *)
            echo -e "${RED}❌ Unsupported OS${NC}"
            echo -e "${YELLOW}📥 Please install Ollama manually from: https://ollama.com/download${NC}"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}✅ Ollama installed successfully!${NC}"
    echo ""
fi

# Check if Ollama service is running
echo -e "${BLUE}🔍 Checking Ollama service status...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama service is running${NC}"
    OLLAMA_RUNNING=true
else
    echo -e "${YELLOW}⚠️  Ollama service is not running${NC}"
    OLLAMA_RUNNING=false
fi
echo ""

# Start Ollama service if not running
if [ "$OLLAMA_RUNNING" = false ]; then
    echo -e "${BLUE}🚀 Starting Ollama service...${NC}"

    # Try to start Ollama in the background
    if [[ "$OS" == "macos" ]] || [[ "$OS" == "linux" ]]; then
        # Check if systemd is available (Linux)
        if command -v systemctl &> /dev/null && systemctl list-units --type=service | grep -q ollama; then
            echo -e "${BLUE}   Using systemd to start Ollama...${NC}"
            sudo systemctl start ollama
            sleep 3
        else
            # Start Ollama manually in background
            echo -e "${BLUE}   Starting Ollama in background...${NC}"
            nohup ollama serve > /tmp/ollama.log 2>&1 &
            OLLAMA_PID=$!
            echo -e "${BLUE}   Ollama PID: ${OLLAMA_PID}${NC}"
            sleep 5
        fi

        # Verify it started
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Ollama service started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start Ollama service${NC}"
            echo -e "${YELLOW}   Please start it manually: ollama serve${NC}"
            exit 1
        fi
    fi
    echo ""
fi

# Check if model is already pulled
echo -e "${BLUE}🔍 Checking for model: ${BOLD}${OLLAMA_MODEL}${NC}"
if ollama list | grep -q "$(echo $OLLAMA_MODEL | cut -d':' -f1)"; then
    echo -e "${GREEN}✅ Model ${OLLAMA_MODEL} is already installed${NC}"
else
    echo -e "${YELLOW}📥 Model ${OLLAMA_MODEL} not found. Downloading...${NC}"
    echo -e "${BLUE}   This may take a few minutes depending on your connection${NC}"
    echo ""

    ollama pull $OLLAMA_MODEL

    echo ""
    echo -e "${GREEN}✅ Model ${OLLAMA_MODEL} downloaded successfully!${NC}"
fi
echo ""

# Display model info
echo -e "${BLUE}📊 Installed Models:${NC}"
ollama list
echo ""

# Test Ollama with a simple query
echo -e "${BLUE}🧪 Testing Ollama with a simple query...${NC}"
TEST_RESPONSE=$(curl -s http://localhost:11434/api/generate -d "{
  \"model\": \"${OLLAMA_MODEL}\",
  \"prompt\": \"What is a database index? Answer in one sentence.\",
  \"stream\": false
}" | grep -o '"response":"[^"]*"' | cut -d'"' -f4 || echo "")

if [ -n "$TEST_RESPONSE" ]; then
    echo -e "${GREEN}✅ Ollama is working correctly!${NC}"
    echo -e "${BLUE}   Test Response: ${TEST_RESPONSE:0:100}...${NC}"
else
    echo -e "${YELLOW}⚠️  Could not get response from Ollama${NC}"
    echo -e "${YELLOW}   But it may still work. Try manually: ollama run ${OLLAMA_MODEL}${NC}"
fi
echo ""

# Update or create .env file
echo -e "${BLUE}📝 Configuring MySQLens .env file...${NC}"

if [ ! -f .env ]; then
    echo -e "${YELLOW}   Creating new .env file...${NC}"
    cat > .env << EOL
# MySQLens Configuration (Auto-generated)
# Local-First AI Setup - Your data never leaves localhost

# LLM Provider (using local Ollama for complete privacy)
LLM_PROVIDER=ollama

# Ollama Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=${OLLAMA_MODEL}

# Cloud LLM Providers (Optional - only if you prefer cloud over local)
#OPENAI_API_KEY=your_openai_key_here
#GEMINI_API_KEY=your_gemini_key_here
#DEEPSEEK_API_KEY=your_deepseek_key_here

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
EOL
    echo -e "${GREEN}✅ Created .env file with Ollama configuration${NC}"
else
    # Update existing .env
    if grep -q "^LLM_PROVIDER=" .env; then
        sed -i.bak "s/^LLM_PROVIDER=.*/LLM_PROVIDER=ollama/" .env
    else
        echo "LLM_PROVIDER=ollama" >> .env
    fi

    if grep -q "^OLLAMA_MODEL=" .env; then
        sed -i.bak "s/^OLLAMA_MODEL=.*/OLLAMA_MODEL=${OLLAMA_MODEL}/" .env
    else
        echo "OLLAMA_MODEL=${OLLAMA_MODEL}" >> .env
    fi

    if grep -q "^OLLAMA_BASE_URL=" .env; then
        sed -i.bak "s|^OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://host.docker.internal:11434|" .env
    else
        echo "OLLAMA_BASE_URL=http://host.docker.internal:11434" >> .env
    fi

    echo -e "${GREEN}✅ Updated .env file with Ollama configuration${NC}"
fi
echo ""

# Summary
echo -e "${BOLD}${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════╗
║                                               ║
║        ✅ Ollama Setup Complete!             ║
║                                               ║
╚═══════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BOLD}📋 Summary:${NC}"
echo -e "   ${GREEN}✅${NC} Ollama installed and running"
echo -e "   ${GREEN}✅${NC} Model downloaded: ${BOLD}${OLLAMA_MODEL}${NC}"
echo -e "   ${GREEN}✅${NC} MySQLens configured for local AI"
echo -e "   ${GREEN}✅${NC} .env file updated"
echo ""

echo -e "${BOLD}🚀 Next Steps:${NC}"
echo -e "   1. Start MySQLens: ${BLUE}docker compose up -d${NC}"
echo -e "   2. Open dashboard: ${BLUE}http://localhost:3000${NC}"
echo -e "   3. Connect to your MySQL database"
echo -e "   4. Start optimizing with ${BOLD}complete privacy${NC}!"
echo ""

echo -e "${BOLD}💡 Useful Commands:${NC}"
echo -e "   • Check Ollama status: ${BLUE}curl http://localhost:11434/api/tags${NC}"
echo -e "   • List models: ${BLUE}ollama list${NC}"
echo -e "   • Test model: ${BLUE}ollama run ${OLLAMA_MODEL}${NC}"
echo -e "   • View logs (if manually started): ${BLUE}tail -f /tmp/ollama.log${NC}"
echo ""

echo -e "${BOLD}${BLUE}🔒 Privacy Note:${NC}"
echo -e "   Your MySQL schema and queries ${BOLD}NEVER${NC} leave localhost."
echo -e "   All AI analysis happens on your machine. Zero data egress. 🎉"
echo ""

echo -e "${GREEN}Happy optimizing with complete privacy! 🚀${NC}"
