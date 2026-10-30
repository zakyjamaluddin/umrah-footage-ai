@echo off
echo Starting Umrah Footage AI Backend...
cd backend
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
