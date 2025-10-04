@echo off
setlocal ENABLEDELAYEDEXPANSION

:: -------------------------------
:: CONFIGURATION
:: -------------------------------
set "VENV_DIR=.\pyeyesweb_env"
set "LIB_SOURCE=."
:: -------------------------------

:: -------------------------------
:: ANSI COLOR CODES (PowerShell + cmd.exe)
:: -------------------------------
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RESET=[0m"

:: -------------------------------
:: CHECK PYTHON
:: -------------------------------
echo %YELLOW%[INFO] Checking Python installation...%RESET%
where.exe python >nul 2>nul
if errorlevel 1 (
    echo %RED%[ERROR] Python not found. Please install Python 3.11.%RESET%
    goto :end_script
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo %YELLOW%[INFO] Python version detected: %PY_VER%%RESET%

echo %PY_VER% | findstr /R "^3\.11\." >nul
if errorlevel 1 (
   echo %RED%[ERROR] Python 3.11.x is required. Found %PY_VER%%RESET%
   goto :end_script
)
echo %GREEN%[OK] Python 3.11.x found.%RESET%

:: -------------------------------
:: CREATE VIRTUAL ENV
:: -------------------------------
echo %YELLOW%[INFO] Creating virtual environment "%VENV_DIR%"...%RESET%
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo %RED%[ERROR] Failed to create virtual environment.%RESET%
    goto :end_script
)
echo %GREEN%[OK] Virtual environment created.%RESET%

:: -------------------------------
:: ACTIVATE VENV
:: -------------------------------
echo %YELLOW%[INFO] Activating virtual environment...%RESET%
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo %RED%[ERROR] Failed to activate virtual environment.%RESET%
    goto :end_script
)
echo %GREEN%[OK] Virtual environment activated.%RESET%

:: -------------------------------
:: INSTALL LIBRARY
:: -------------------------------
echo %YELLOW%[INFO] Upgrading pip, setuptools, wheel...%RESET%
python -m pip install --upgrade pip setuptools wheel

echo %YELLOW%[INFO] Installing pyeyesweb from "%LIB_SOURCE%"...%RESET%
python -m pip install -U pyeyesweb
if errorlevel 1 (
    echo %RED%[ERROR] Library installation failed.%RESET%
    goto :end_script
)
echo %GREEN%[OK] Library installed successfully in virtual environment.%RESET%

:end_script
echo.
echo %YELLOW%[INFO] Script finished. Press any key to exit...%RESET%
pause >nul

endlocal
exit /b 0
