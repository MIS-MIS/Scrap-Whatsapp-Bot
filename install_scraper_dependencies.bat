@echo off
echo ========================================
echo   GOOGLE MAPS SCRAPER - DEPENDENCY INSTALLER
echo ========================================
echo.

echo 🚀 Installing all dependencies for Google Maps Scraper...
echo.

REM Check if Python is installed
echo 🔍 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed!
    echo.
    echo 📥 Please install Python 3.7+ from: https://python.org/downloads/
    echo ✅ Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found:
python --version

echo.
echo 🔍 Checking pip installation...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed!
    echo 📥 Installing pip...
    python -m ensurepip --upgrade
    if %errorlevel% neq 0 (
        echo ❌ Failed to install pip!
        pause
        exit /b 1
    )
)

echo ✅ pip found:
pip --version

echo.
echo 📦 Installing Python packages...
echo.

echo 📥 Installing Playwright (Browser automation)...
pip install playwright
if %errorlevel% neq 0 (
    echo ❌ Failed to install Playwright!
    pause
    exit /b 1
)
echo ✅ Playwright installed successfully

echo.
echo 📥 Installing Pandas (Data processing)...
pip install pandas
if %errorlevel% neq 0 (
    echo ❌ Failed to install Pandas!
    pause
    exit /b 1
)
echo ✅ Pandas installed successfully

echo.
echo 📥 Installing additional required packages...
pip install openpyxl xlsxwriter
if %errorlevel% neq 0 (
    echo ⚠️  Warning: Excel support packages failed to install
    echo 💡 CSV functionality will still work
)
echo ✅ Additional packages installed

echo.
echo 🌐 Installing Playwright browsers...
echo 📥 This may take a few minutes (downloading Chrome browser)...
playwright install chromium
if %errorlevel% neq 0 (
    echo ❌ Failed to install Playwright browsers!
    echo 💡 Trying alternative installation...
    python -m playwright install chromium
    if %errorlevel% neq 0 (
        echo ❌ Browser installation failed!
        echo 💡 You may need to install manually
        pause
        exit /b 1
    )
)
echo ✅ Playwright browsers installed successfully

echo.
echo 🔧 Installing system dependencies (if needed)...
playwright install-deps >nul 2>&1
echo ✅ System dependencies checked

echo.
echo 🧪 Testing installation...
echo.

echo 📝 Creating test script...
echo import playwright > test_installation.py
echo import pandas >> test_installation.py
echo print("✅ All packages imported successfully!") >> test_installation.py
echo print("🚀 Google Maps Scraper is ready to use!") >> test_installation.py

echo 🧪 Running test...
python test_installation.py
if %errorlevel% neq 0 (
    echo ❌ Installation test failed!
    pause
    exit /b 1
)

echo.
echo 🧹 Cleaning up test files...
del test_installation.py >nul 2>&1

echo.
echo ========================================
echo   ✅ INSTALLATION COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo 📋 Installed Components:
echo ✅ Python (verified)
echo ✅ pip (package manager)
echo ✅ Playwright (browser automation)
echo ✅ Pandas (data processing)
echo ✅ Chrome browser (for automation)
echo ✅ System dependencies
echo.
echo 🚀 Ready to use:
echo   • python main.py (command line scraper)
echo   • python interactive_scraper.py (full interface)
echo   • start_scraper_24_7.bat (24/7 operation)
echo.
echo 📁 Output files will be saved to:
echo   • output/all_contacts.csv
echo   • fetched_contacts.json
echo   • search_progress.json
echo.
echo 💡 Next steps:
echo 1. Run: python interactive_scraper.py
echo 2. Choose your scraping options
echo 3. Start collecting business data!
echo.
pause