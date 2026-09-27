@echo off
title GESTALT // Cognitive Blueprint Studio
echo =========================================================
echo    GESTALT: Cognitive Topology ^& Socratic Blueprint Extractor
echo    High-Bandwidth Thought-to-Topology Interface
echo =========================================================
echo.
echo Launching local server on http://127.0.0.1:8000 ...
echo.
cd /d "%~dp0"
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
pause
