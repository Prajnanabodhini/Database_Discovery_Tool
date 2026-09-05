@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
"%PYTHON_EXE%" main.py cli --mode metadata
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo Metadata discovery exited with error code %EXIT_CODE%.
  if not defined CI pause
)
endlocal & exit /b %EXIT_CODE%
