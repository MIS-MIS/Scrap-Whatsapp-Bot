@echo off
echo ========================================
echo Google Maps Scraper - 24/7 Operation
echo ========================================
echo.

echo 🔧 Configuring system for continuous scraping...
echo.

REM Disable sleep and hibernate while scraper runs
powercfg -change -standby-timeout-ac 0
powercfg -change -hibernate-timeout-ac 0
powercfg -change -monitor-timeout-ac 30
echo ✅ Sleep mode disabled - system will stay awake

echo.
echo 📋 24/7 Scraping Status:
echo ✅ Screen can turn off (saves power)
echo ✅ System stays awake (scraper keeps running)
echo ✅ Browser automation continues
echo ✅ Scheduled scraping executes on time
echo ✅ Data collection never stops
echo ❌ Do NOT put computer to sleep manually
echo.

echo 🚀 Starting Google Maps Scraper in 24/7 mode...
echo.
echo 💡 To stop scraper: Press Ctrl+C
echo 🔄 To restart: Run this script again
echo 📊 Data will be saved to output/all_contacts.csv
echo.

REM Start the scraper
python interactive_scraper.py

echo.
echo 🔧 Scraper stopped. Restoring normal power settings...
powercfg -change -standby-timeout-ac 30
powercfg -change -hibernate-timeout-ac 180
powercfg -change -monitor-timeout-ac 15
echo ✅ Power settings restored to normal

echo.
echo 👋 Scraping session ended
pause