@echo off
echo Demarrage de EFImagingBench...
cd /d "%~dp0"
call venv64\Scripts\activate.bat
python EFImagingBench_App\src\gui\EFImagingBench_GUI.py
if %ERRORLEVEL% NEQ 0 (
    echo Une erreur s'est produite lors du demarrage de l'application.
    echo Code d'erreur: %ERRORLEVEL%
    pause
)
