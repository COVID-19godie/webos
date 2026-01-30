@echo off
setlocal

REM Ensure script runs from this folder
cd /d "%~dp0"

echo Running Django migrations...
python manage.py makemigrations
if errorlevel 1 (
  echo makemigrations failed.
  exit /b 1
)

python manage.py migrate
if errorlevel 1 (
  echo migrate failed.
  exit /b 1
)

echo Migrations completed.
endlocal
