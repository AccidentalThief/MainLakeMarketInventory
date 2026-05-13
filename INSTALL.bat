@echo off
setlocal enabledelayedexpansion
title DeliTrack Installer

echo.
echo  =====================================================
echo    DeliTrack - Deli Inventory Manager
echo    Installer
echo  =====================================================
echo.

:: Step 1: Check for Python
echo  [1/4] Checking for Python...

python --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
    echo        Found Python !PYVER!
    goto :check_version
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    for /f "tokens=2" %%v in ('py --version 2^>^&1') do set PYVER=%%v
    echo        Found Python !PYVER! (via py launcher)
    set PYTHON=py
    goto :setup
)

:: Python not found - download and install it
echo        Python not found. Downloading Python installer...
echo.

set PYTHON_URL=https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe
set PYTHON_INSTALLER=%TEMP%\python_installer.exe

powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"
if not exist "%PYTHON_INSTALLER%" (
    echo.
    echo  ERROR: Could not download Python automatically.
    echo  Please visit https://www.python.org/downloads/ and install Python 3.
    echo  Then run this installer again.
    echo.
    pause
    exit /b 1
)

echo        Installing Python (this may take a minute)...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
if %errorlevel% neq 0 (
    echo  ERROR: Python installation failed.
    pause
    exit /b 1
)
del "%PYTHON_INSTALLER%"
call refreshenv >nul 2>&1
set PYTHON=python
echo        Python installed successfully!
goto :setup

:check_version
set PYTHON=python

:setup
:: Step 2: Set up environment
echo.
echo  [2/4] Setting up app environment...

set INSTALL_DIR=%USERPROFILE%\DeliTrack
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

xcopy /E /I /Y "%~dp0deli_simple\*" "%INSTALL_DIR%\" >nul 2>&1
if %errorlevel% neq 0 (
    xcopy /E /I /Y "%~dp0*" "%INSTALL_DIR%\" >nul 2>&1
)

cd /d "%INSTALL_DIR%"

if not exist "%INSTALL_DIR%\venv" (
    echo        Creating isolated Python environment...
    %PYTHON% -m venv venv
    if %errorlevel% neq 0 (
        echo  ERROR: Could not create Python environment.
        pause
        exit /b 1
    )
) else (
    echo        Existing environment found, updating...
)

:: Step 3: Install requirements
echo.
echo  [3/4] Installing requirements (PyQt6)...
echo        This may take a minute on first install...

"%INSTALL_DIR%\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%INSTALL_DIR%\venv\Scripts\pip.exe" install -r "%INSTALL_DIR%\requirements.txt" --quiet
if %errorlevel% neq 0 (
    echo  ERROR: Failed to install requirements.
    echo  Please check your internet connection and try again.
    pause
    exit /b 1
)
echo        Requirements installed!

:: Step 4: Create desktop shortcut
echo.
echo  [4/4] Creating desktop shortcut...

set LAUNCHER=%INSTALL_DIR%\launch.bat
set SHORTCUT=%USERPROFILE%\Desktop\DeliTrack.lnk
set PS_SCRIPT=%TEMP%\delitrack_shortcut.ps1

(
    echo @echo off
    echo cd /d "%INSTALL_DIR%"
    echo start "" "%INSTALL_DIR%\venv\Scripts\pythonw.exe" "%INSTALL_DIR%\main.py"
) > "%LAUNCHER%"

(
    echo $ws = New-Object -ComObject WScript.Shell
    echo $s = $ws.CreateShortcut('%SHORTCUT%'^)
    echo $s.TargetPath = '%LAUNCHER%'
    echo $s.WorkingDirectory = '%INSTALL_DIR%'
    echo $s.WindowStyle = 7
    echo $s.IconLocation = '%INSTALL_DIR%\delitrack.ico'
    echo $s.Description = 'DeliTrack Inventory Manager'
    echo $s.Save(^)
) > "%PS_SCRIPT%"

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del "%PS_SCRIPT%" >nul 2>&1

if exist "%SHORTCUT%" (
    echo        Desktop shortcut created!
) else (
    echo        NOTE: Shortcut could not be placed on Desktop.
    echo        You can launch the app by double-clicking:
    echo        %LAUNCHER%
)

echo.
echo  =====================================================
echo    Installation complete!
echo  =====================================================
echo.
echo    DeliTrack has been installed to:
echo    %INSTALL_DIR%
echo.
echo    A "DeliTrack" shortcut is now on your Desktop.
echo    Double-click it any time to open the app.
echo.

set /p LAUNCH=   Launch DeliTrack now? (Y/N): 
if /i "%LAUNCH%"=="Y" (
    start "" "%INSTALL_DIR%\venv\Scripts\pythonw.exe" "%INSTALL_DIR%\main.py"
)

echo.
pause
