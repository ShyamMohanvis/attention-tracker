# build.ps1 — PowerShell build script for Attention Tracker
# Usage: .\build.ps1
# Requires: Python 3.12, pip, pyinstaller

param(
    [switch]$Clean,
    [switch]$NoDeps
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $Root "venv"
$SrcDir = Join-Path $Root "src"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Attention Tracker — Build Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# ── Clean previous build ─────────────────────────────────────────────────────
if ($Clean) {
    Write-Host "[Clean] Removing build/ and dist/ ..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "$Root\build", "$Root\dist" -ErrorAction SilentlyContinue
}

# ── Create / activate venv ───────────────────────────────────────────────────
if (-not (Test-Path $VenvDir)) {
    Write-Host "[Setup] Creating virtual environment..." -ForegroundColor Green
    python -m venv $VenvDir
}

$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PyInstallerExe = Join-Path $VenvDir "Scripts\pyinstaller.exe"

# ── Install dependencies ─────────────────────────────────────────────────────
if (-not $NoDeps) {
    Write-Host "[Deps] Installing dependencies from requirements.txt..." -ForegroundColor Green
    & $PipExe install -r "$Root\requirements.txt" --quiet
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
}

# ── Run tests ────────────────────────────────────────────────────────────────
Write-Host "[Test] Running pytest..." -ForegroundColor Green
& $PythonExe -m pytest "$Root\tests" -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Tests failed — build continuing anyway." -ForegroundColor Yellow
}

# ── PyInstaller ───────────────────────────────────────────────────────────────
Write-Host "[Build] Running PyInstaller..." -ForegroundColor Green
& $PyInstallerExe "$Root\attention.spec" --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$ExePath = Join-Path $Root "dist\AttentionTracker\AttentionTracker.exe"
if (Test-Path $ExePath) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "  BUILD SUCCESSFUL" -ForegroundColor Green
    Write-Host "  Output: $ExePath" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
} else {
    throw "Build output not found at $ExePath"
}
