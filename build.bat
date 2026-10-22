@echo off
REM build.bat — Windows batch build script for Attention Tracker
REM Usage: build.bat [--clean]

setlocal enabledelayedexpansion

set ROOT=%~dp0
set VENV=%ROOT%venv
set PIP=%VENV%\Scripts\pip.exe
set PYTHON=%VENV%\Scripts\python.exe
set PYINST=%VENV%\Scripts\pyinstaller.exe

echo ==================================================
echo   Attention Tracker - Build
echo ==================================================

IF "%1"=="--clean" (
    echo [Clean] Removing build/ and dist/ ...
    if exist "%ROOT%build" rmdir /s /q "%ROOT%build"
    if exist "%ROOT%dist"  rmdir /s /q "%ROOT%dist"
)

REM ── Create venv if needed ──────────────────────────────────────────────────
if not exist "%VENV%" (
    echo [Setup] Creating virtual environment...
    python -m venv "%VENV%"
)

REM ── Install dependencies ───────────────────────────────────────────────────
echo [Deps] Installing requirements...
"%PIP%" install -r "%ROOT%requirements.txt" --quiet
if errorlevel 1 (echo [ERROR] pip install failed && exit /b 1)

REM ── Tests ─────────────────────────────────────────────────────────────────
echo [Test] Running tests...
"%PYTHON%" -m pytest "%ROOT%tests" -v --tb=short

REM ── Build ─────────────────────────────────────────────────────────────────
echo [Build] Running PyInstaller...
"%PYINST%" "%ROOT%attention.spec" --noconfirm
if errorlevel 1 (echo [ERROR] PyInstaller failed && exit /b 1)

if not exist "%ROOT%dist\AttentionTracker\AttentionTracker.exe" (
    echo [ERROR] AttentionTracker.exe not found at %ROOT%dist\AttentionTracker\AttentionTracker.exe
    exit /b 1
)
if not exist "%ROOT%dist\AttentionTracker\assets\face_landmarker.task" (
    echo [ERROR] Model asset not found at %ROOT%dist\AttentionTracker\assets\face_landmarker.task
    exit /b 1
)

REM ── Package ZIP ──────────────────────────────────────────────────────────────
echo [Package] Packaging AttentionTracker-Windows.zip...
powershell -NoProfile -Command "Compress-Archive -Path '%ROOT%dist\AttentionTracker' -DestinationPath '%ROOT%dist\AttentionTracker-Windows.zip' -Force"
if errorlevel 1 (echo [ERROR] Packaging failed && exit /b 1)

echo ==================================================
echo   BUILD & PACKAGING SUCCESSFUL
echo   Output:  %ROOT%dist\AttentionTracker\AttentionTracker.exe
echo   Package: %ROOT%dist\AttentionTracker-Windows.zip
echo ==================================================
