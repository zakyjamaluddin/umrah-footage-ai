@echo off
echo ====================================================
echo   Umrah Footage AI Indexer & Ads Script Matcher
echo ====================================================
echo.
echo Menjalankan Backend FastAPI (Port 8000)...
start "Umrah AI - Backend" cmd /k start_backend.bat

echo Menjalankan Frontend Web UI (Port 5173)...
start "Umrah AI - Frontend" cmd /k start_frontend.bat

echo.
echo Aplikasi siap dibuka di browser: http://localhost:5173
echo.
pause
