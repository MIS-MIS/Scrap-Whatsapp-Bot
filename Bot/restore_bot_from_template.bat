@echo off
setlocal
set ROOT=%~dp0

if not exist "%ROOT%bot.template.js" (
  echo bot.template.js not found in %ROOT%
  echo Aborting.
  exit /b 1
)

copy /Y "%ROOT%bot.template.js" "%ROOT%bot.js" >nul
if %errorlevel% neq 0 (
  echo Failed to restore bot.js
  exit /b 1
)

echo Restored bot.js from bot.template.js successfully.
endlocal
