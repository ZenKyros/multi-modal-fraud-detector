#!/bin/bash
# Quick Start Script for Multi-Modal Fraud Detector

echo "==================================="
echo "Multi-Modal Fraud Detector"
echo "Quick Start Setup"
echo "==================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}[1/5] Checking Python installation...${NC}"
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi
echo -e "${GREEN}✓ Python found: $(python --version)${NC}"
echo ""

# Check Node
echo -e "${BLUE}[2/5] Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
echo ""

# Backend setup
echo -e "${BLUE}[3/5] Setting up backend...${NC}"
cd backend || exit 1

# Create virtual environment
python -m venv venv

# Activate venv
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
pip install -q -r ../requirements.txt

echo -e "${GREEN}✓ Backend dependencies installed${NC}"
cd ..
echo ""

# Frontend setup
echo -e "${BLUE}[4/5] Setting up frontend...${NC}"
cd frontend || exit 1
npm install -q
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
cd ..
echo ""

# Configuration
echo -e "${BLUE}[5/5] Configuration Check${NC}"
echo "Please ensure you have:"
echo "  • GROQ_API_KEY set in backend/.env"
echo "  • GEMINI_API_KEY set in backend/.env"
echo ""

echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Update backend/.env with your API keys"
echo "  2. Start backend: cd backend && python -m uvicorn main:app --reload"
echo "  3. Start frontend: cd frontend && npm run dev"
echo "  4. Open http://localhost:5173 in your browser"
echo ""
