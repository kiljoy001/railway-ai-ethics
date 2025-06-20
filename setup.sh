#!/bin/bash

# Railway CLI Installation and Project Setup Script

echo "Railway Setup Script"
echo "======================"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        echo "Installing Railway CLI via Homebrew..."
        brew install railway
    else
        echo "Installing Railway CLI via curl..."
        curl -fsSL https://railway.app/install.sh | sh
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Installing Railway CLI for Linux..."
    curl -fsSL https://railway.app/install.sh | sh
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    echo "Installing Railway CLI for Windows..."
    npm install -g @railway/cli
else
    echo "Unsupported OS. Please install manually from https://railway.app"
    exit 1
fi

# Verify installation
if command -v railway &> /dev/null; then
    echo "✅ Railway CLI installed successfully"
    railway --version
else
    echo "❌ Railway installation failed"
    exit 1
fi

# Login to Railway
echo ""
echo "Logging into Railway..."
railway login

# Clone and setup the project
echo ""
echo "Setting up AI Ethics Crisis Dashboard..."
read -p "Enter project directory name [ai-ethics-dashboard]: " PROJECT_DIR
PROJECT_DIR=${PROJECT_DIR:-ai-ethics-dashboard}

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create project files
echo "Creating project files..."

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi
uvicorn
httpx
python-dotenv
EOF



# Create railway.json
cat > railway.json << 'EOF'
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT"
  }
}
EOF

echo ""
echo "✅ Project structure created"
echo ""
echo "Next steps:"
echo "1. Copy your main.py file to this directory"
echo "2. Copy .env.example to .env and add your configuration"
echo "3. Run 'railway up' to deploy"
echo ""
echo "To deploy:"
echo "  cd $PROJECT_DIR"
echo "  railway up"
echo ""
echo "Your app will be available at: https://[your-app].up.railway.app"
