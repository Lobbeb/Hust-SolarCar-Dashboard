#!/bin/bash
# HUST Solar Car Dashboard - Quick Setup Script
# Run this script to install all dependencies and start the system

echo "🚗⚡ HUST Solar Car Dashboard Setup"
echo "=================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

echo "✅ Python and Node.js found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Setup environment file
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment configuration..."
    cp .env.template .env
    echo "📝 Please edit .env file with your database credentials"
fi

# Install frontend dependencies
echo "🎨 Installing frontend dependencies..."
cd hust-frontend
npm install
cd ..

echo "🎉 Setup complete!"
echo ""
echo "🚀 To start the system:"
echo "1. Edit .env file with your database credentials"
echo "2. Run: python backend/app.py (in one terminal)"
echo "3. Run: cd hust-frontend && npm run dev (in another terminal)"
echo "4. Open: http://localhost:5173"
echo ""
echo "📱 For VS Code integration:"
echo "- Install 'Live Preview' extension"
echo "- Right-click preview.html → 'Show Preview'"
