@echo off
REM Build script for MediaCore (Windows)

echo Building frontend...
cd frontend
call npm run build

echo Copying to backend/static...
cd ..
if exist backend\static rmdir /s /q backend\static
mkdir backend\static
xcopy /s /e /y frontend\dist\* backend\static\

echo Done! You can now start the backend with: cd backend ^&^& python main.py
