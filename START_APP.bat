@echo off
title Autism Lens Clinical Decision Support System
color 0B
echo.
echo ================================================
echo   Autism Lens - Clinical Decision Support System
echo   Official Pearson VABS-3 & DSM-5-TR Engine
echo ================================================
echo.
echo Starting server, please wait 3-5 seconds...
echo Your browser will open automatically at http://127.0.0.1:5050
echo Do NOT close this window while using the application.
echo.

if exist .venv\Scripts\python.exe (
    set "PY_CMD=.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

%PY_CMD% run.py
pause
