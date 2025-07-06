@echo off
echo Starting Portfolio Tracker...
echo.

echo Initializing backend database...
cd backend
python init_data.py
echo.

echo Starting backend server (FastAPI)...
start cmd /k "uvicorn main:app --reload"
echo Backend started at http://localhost:8000
echo.

echo Starting frontend server (Vue.js)...
cd ../frontend
start cmd /k "npm run serve"
echo Frontend will be available at http://localhost:8080
echo.

echo Both servers are starting...
echo Press any key to exit
pause 