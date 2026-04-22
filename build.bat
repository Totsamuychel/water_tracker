@echo off
pip install -r requirements.txt
pyinstaller build.spec --clean
echo Build complete! EXE is in dist/WaterTracker.exe
pause
