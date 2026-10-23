@echo off
title Odoo 20 Server
cd /d "%~dp0"
echo ===================================================
echo Starting Odoo 20 Server...
echo Web URL: http://localhost:8069
echo Configuration: %CD%\odoo.conf
echo ===================================================
"%CD%\venv\Scripts\python.exe" "%CD%\odoo\odoo-bin" -c "%CD%\odoo.conf" -d tadic_demo
if %errorlevel% neq 0 (
    echo.
    echo Odoo exited with an error. Check logs above.
    pause
)
