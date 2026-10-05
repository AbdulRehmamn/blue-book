@echo off
setlocal
cd /d "%~dp0"
if not exist "app.py" goto missing
if exist ".venv\Scripts\python.exe" goto install
py -3 --version >nul 2>&1
if errorlevel 1 goto fallback
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install
:fallback
python --version >nul 2>&1
if errorlevel 1 goto pythonmissing
python -m venv .venv
if errorlevel 1 goto failed
:install
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 goto failed
.venv\Scripts\python.exe app.py
if errorlevel 1 goto failed
exit /b 0
:pythonmissing
echo Install Python 3.10 or newer from python.org, including Tcl/Tk and the Python launcher.
goto failed
:missing
echo Extract the ENTIRE ZIP first. START.bat must stay beside app.py.
:failed
echo Setup or launch failed. See the error above. Your existing progress is retained.
pause
exit /b 1
