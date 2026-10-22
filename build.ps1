# build.ps1 - PowerShell build script for Attention Tracker
# Usage: .\build.ps1 [-Clean] [-NoDeps]
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
Write-Host "  Attention Tracker - Build Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Clean previous build
if ($Clean) {
    Write-Host "[Clean] Removing build/ and dist/ ..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "$Root\build", "$Root\dist" -ErrorAction SilentlyContinue
}

# Create / activate venv
if (-not (Test-Path $VenvDir)) {
    Write-Host "[Setup] Creating virtual environment..." -ForegroundColor Green
    python -m venv $VenvDir
}

$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PyInstallerExe = Join-Path $VenvDir "Scripts\pyinstaller.exe"

# Install dependencies
if (-not $NoDeps) {
    Write-Host "[Deps] Installing dependencies from requirements.txt..." -ForegroundColor Green
    & $PipExe install -r "$Root\requirements.txt" --quiet
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
}

# Run tests
Write-Host "[Test] Running pytest..." -ForegroundColor Green
& $PythonExe -m pytest "$Root\tests" -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Tests failed - build continuing anyway." -ForegroundColor Yellow
}

# PyInstaller
Write-Host "[Build] Running PyInstaller..." -ForegroundColor Green
& $PyInstallerExe "$Root\attention.spec" --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$ExePath = Join-Path $Root "dist\AttentionTracker\AttentionTracker.exe"
$AssetInternal = Join-Path $Root "dist\AttentionTracker\_internal\assets\face_landmarker.task"
$AssetRoot = Join-Path $Root "dist\AttentionTracker\assets\face_landmarker.task"
$ZipPath = Join-Path $Root "dist\AttentionTracker-Windows.zip"

if (-not (Test-Path $ExePath)) {
    throw "Build output not found at $ExePath"
}
if ((-not (Test-Path $AssetInternal)) -and (-not (Test-Path $AssetRoot))) {
    throw "Model asset face_landmarker.task not found in dist/AttentionTracker"
}

# Ensure asset exists in root assets as well for user clarity
if ((Test-Path $AssetInternal) -and (-not (Test-Path $AssetRoot))) {
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "dist\AttentionTracker\assets") | Out-Null
    Copy-Item $AssetInternal -Destination $AssetRoot -Force
}

# Ensure README_INSTALL.txt is at root of dist folder
Copy-Item "$Root\README_INSTALL.txt" -Destination "$Root\dist\AttentionTracker\README_INSTALL.txt" -Force

# Package ZIP
Write-Host "[Package] Packaging AttentionTracker-Windows.zip..." -ForegroundColor Green
$DistFolder = Join-Path $Root "dist\AttentionTracker"
Compress-Archive -Path $DistFolder -DestinationPath $ZipPath -Force

if (Test-Path $ZipPath) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "  BUILD & PACKAGING SUCCESSFUL" -ForegroundColor Green
    Write-Host "  Executable: $ExePath" -ForegroundColor Green
    Write-Host "  Package:    $ZipPath" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
} else {
    throw "Failed to create ZIP package at $ZipPath"
}
