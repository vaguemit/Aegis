@echo off
echo Starting AegisPath FastAPI Backend...
call .\.venv\Scripts\activate.bat
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
