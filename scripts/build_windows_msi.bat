@echo off
REM build_windows_msi.bat — Build MoonJoy Windows MSI installer
REM Requires: pip install cx_Freeze

echo === Building MoonJoy Windows MSI ===

echo [1/2] Building MSI with cx_Freeze...
py setup_cx.py bdist_msi --target-dir dist\windows

echo.
echo [2/2] MSI build complete!
echo.
echo MSI file is in: dist\windows\
echo.
echo To install: double-click the .msi file
echo To use as screensaver after install:
echo   1. Copy MoonJoy.exe to %%SystemRoot%%\System32\MoonJoy.scr
echo   2. Right-click Desktop ^> Personalize ^> Lock Screen ^> Screen Saver Settings
echo   3. Select "MoonJoy"
echo.
pause
