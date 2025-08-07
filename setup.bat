@echo off
REM HUST Solar Car Dashboard - Quick Setup Script for Windows
REM Run this script to install all dependencies and start the system

echo 🚗⚡ HUST Solar Car Dashboard Setup
echo ==================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    pause
    exit /b 1
)

echo ✅ Python and Node.js found

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Setup environment file
if not exist ".env" (
    echo ⚙️ Creating environment configuration...
    copy .env.template .env
    echo 📝 Please edit .env file with your database credentials
)

REM Install frontend dependencies
echo 🎨 Installing frontend dependencies...
cd hust-frontend
npm install
cd ..

echo 🎉 Setup complete!
echo.
echo 🚀 To start the system:
echo 1. Edit .env file with your database credentials
echo 2. Run: python backend/app.py ^(in one terminal^)
echo 3. Run: cd hust-frontend ^&^& npm run dev ^(in another terminal^)
echo 4. Open: http://localhost:5173
echo.
echo 📱 For VS Code integration:
echo - Install 'Live Preview' extension
echo - Right-click preview.html → 'Show Preview'
pause
